#!/usr/bin/env bash

set -Eeuo pipefail

# Safely recover an S3 CloudFormation stack after a failed update or
# deploy a previously saved template and parameter set through a change set.
#
# Usage:
#   ./rollback-stack.sh <environment>
#       [--mode continue-update-rollback|previous-template]
#       [--template FILE]
#       [--parameters FILE]
#       [--region REGION]
#       [--profile PROFILE]
#       [--skip-resources ID1,ID2]
#
# Modes:
#   continue-update-rollback
#       Recover a stack in UPDATE_ROLLBACK_FAILED state.
#
#   previous-template
#       Deploy a supplied previous template and parameter file through
#       a reviewed CloudFormation change set. This is a forward update,
#       not a native CloudFormation rollback operation.

readonly DEFAULT_STACK_NAME_PREFIX="s3-static-website"
readonly DEFAULT_POLL_INTERVAL=10
readonly DEFAULT_STACK_TIMEOUT_SECONDS=3600
readonly MAX_TEMPLATE_BYTES=51200

STACK_NAME_PREFIX="${STACK_NAME_PREFIX:-${DEFAULT_STACK_NAME_PREFIX}}"
POLL_INTERVAL="${STACK_POLL_INTERVAL:-${DEFAULT_POLL_INTERVAL}}"
STACK_TIMEOUT_SECONDS="${STACK_TIMEOUT_SECONDS:-${DEFAULT_STACK_TIMEOUT_SECONDS}}"

ENVIRONMENT=""
MODE="continue-update-rollback"
TEMPLATE_FILE=""
PARAMETERS_FILE=""
AWS_REGION_VALUE="${AWS_REGION:-${AWS_DEFAULT_REGION:-ap-south-1}}"
AWS_PROFILE_VALUE="${AWS_PROFILE:-}"
SKIP_RESOURCES_CSV=""

CHANGE_SET_NAME=""
CHANGE_SET_CREATED=false
EXECUTION_STARTED=false

log() {
    printf '[INFO] %s\n' "$*"
}

success() {
    printf '[PASS] %s\n' "$*"
}

warning() {
    printf '[WARN] %s\n' "$*" >&2
}

error() {
    printf '[ERROR] %s\n' "$*" >&2
}

usage() {
    cat <<'EOF'
Usage:
  rollback-stack.sh <dev|staging|production> [options]

Options:
  --mode MODE              continue-update-rollback | previous-template
  --template FILE          Previous CloudFormation template (required for
                           previous-template mode)
  --parameters FILE        CloudFormation parameter JSON file (required for
                           previous-template mode)
  --region REGION          AWS deployment Region
  --profile PROFILE        AWS CLI profile
  --skip-resources IDS     Comma-separated logical resource IDs to skip
                           during continue-update-rollback
  -h, --help               Display this help message

Environment variables:
  STACK_NAME_PREFIX        CloudFormation stack name prefix
  STACK_POLL_INTERVAL      Polling interval in seconds
  STACK_TIMEOUT_SECONDS    Maximum wait time for recovery or update

Examples:
  ./rollback-stack.sh dev

  ./rollback-stack.sh staging \
      --mode continue-update-rollback \
      --skip-resources StaticWebsiteBucketPolicy

  ./rollback-stack.sh production \
      --mode previous-template \
      --template ./templates/static-website-bucket.yaml \
      --parameters ./parameters/production.json \
      --region ap-south-1

Important:
  - continue-update-rollback is only for UPDATE_ROLLBACK_FAILED stacks.
  - previous-template creates a new update change set.
  - Neither mode deletes S3 objects or guarantees recovery of deleted data.
  - Review stack events and resource state before taking action.
EOF
}

parse_arguments() {
    if (( $# == 0 )); then
        usage >&2
        return 2
    fi

    ENVIRONMENT="$1"
    shift

    case "${ENVIRONMENT}" in
        dev|staging|production) ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            error "Invalid environment: ${ENVIRONMENT}"
            usage >&2
            return 2
            ;;
    esac

    while (( $# > 0 )); do
        case "$1" in
            --mode)
                if [[ $# -lt 2 || -z "$2" ]]; then
                    error "--mode requires a value."
                    return 2
                fi
                MODE="$2"
                shift 2
                ;;
            --template)
                if [[ $# -lt 2 || -z "$2" ]]; then
                    error "--template requires a file path."
                    return 2
                fi
                TEMPLATE_FILE="$2"
                shift 2
                ;;
            --parameters)
                if [[ $# -lt 2 || -z "$2" ]]; then
                    error "--parameters requires a file path."
                    return 2
                fi
                PARAMETERS_FILE="$2"
                shift 2
                ;;
            --region)
                if [[ $# -lt 2 || -z "$2" ]]; then
                    error "--region requires a value."
                    return 2
                fi
                AWS_REGION_VALUE="$2"
                shift 2
                ;;
            --profile)
                if [[ $# -lt 2 || -z "$2" ]]; then
                    error "--profile requires a value."
                    return 2
                fi
                AWS_PROFILE_VALUE="$2"
                shift 2
                ;;
            --skip-resources)
                if [[ $# -lt 2 || -z "$2" ]]; then
                    error "--skip-resources requires a comma-separated list."
                    return 2
                fi
                SKIP_RESOURCES_CSV="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                usage >&2
                return 2
                ;;
        esac
    done

    case "${MODE}" in
        continue-update-rollback|previous-template) ;;
        *)
            error "Unsupported mode: ${MODE}"
            return 2
            ;;
    esac

    if [[ "${MODE}" == "previous-template" ]]; then
        if [[ -z "${TEMPLATE_FILE}" || -z "${PARAMETERS_FILE}" ]]; then
            error "previous-template mode requires --template and --parameters."
            return 2
        fi
    elif [[ -n "${TEMPLATE_FILE}" || -n "${PARAMETERS_FILE}" ]]; then
        error "--template and --parameters are only valid in previous-template mode."
        return 2
    fi

    if [[ "${MODE}" == "previous-template" && -n "${SKIP_RESOURCES_CSV}" ]]; then
        error "--skip-resources is only valid in continue-update-rollback mode."
        return 2
    fi

    if [[ ! "${POLL_INTERVAL}" =~ ^[1-9][0-9]*$ ]]; then
        error "STACK_POLL_INTERVAL must be a positive integer."
        return 2
    fi

    if [[ ! "${STACK_TIMEOUT_SECONDS}" =~ ^[1-9][0-9]*$ ]]; then
        error "STACK_TIMEOUT_SECONDS must be a positive integer."
        return 2
    fi

    if [[ -n "${SKIP_RESOURCES_CSV}" ]]; then
        validate_skip_resource_ids
    fi

    STACK_NAME="${STACK_NAME_PREFIX}-${ENVIRONMENT}"
}

validate_skip_resource_ids() {
    local item
    local -a resource_ids

    IFS=',' read -r -a resource_ids <<< "${SKIP_RESOURCES_CSV}"

    if (( ${#resource_ids[@]} == 0 )); then
        error "No resource IDs were supplied."
        return 2
    fi

    for item in "${resource_ids[@]}"; do
        if [[ ! "${item}" =~ ^[A-Za-z0-9]+$ ]]; then
            error "Invalid CloudFormation logical resource ID: ${item}"
            return 2
        fi
    done
}

require_commands() {
    local missing=0
    local command_name

    for command_name in aws python3 date sleep wc tr; do
        if ! command -v "${command_name}" >/dev/null 2>&1; then
            error "Required command not found: ${command_name}"
            missing=1
        fi
    done

    if (( missing != 0 )); then
        return 1
    fi
}

aws_cli() {
    local -a args=("$@")

    if [[ -n "${AWS_PROFILE_VALUE}" ]]; then
        aws --profile "${AWS_PROFILE_VALUE}" "${args[@]}"
    else
        aws "${args[@]}"
    fi
}

aws_cli_region() {
    aws_cli "$@" --region "${AWS_REGION_VALUE}" --no-cli-pager
}

resolve_file_path() {
    python3 - "$1" <<'PY'
import os
import sys

print(os.path.realpath(sys.argv[1]))
PY
}

verify_aws_identity() {
    local identity
    local account_id
    local caller_arn

    log "Verifying AWS credentials and account identity..."

    if ! identity="$(aws_cli sts get-caller-identity --output json)"; then
        error "Unable to retrieve AWS identity. Check credentials and profile configuration."
        return 1
    fi

    account_id="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["Account"])' <<< "${identity}")"
    caller_arn="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["Arn"])' <<< "${identity}")"

    printf 'AWS Account: %s\n' "${account_id}"
    printf 'Caller ARN:  %s\n' "${caller_arn}"
    printf 'Region:      %s\n' "${AWS_REGION_VALUE}"
    printf 'Stack:       %s\n' "${STACK_NAME}"
    printf 'Environment: %s\n' "${ENVIRONMENT}"

    success "AWS identity verified."
}

get_stack_status() {
    aws_cli_region cloudformation describe-stacks \
        --stack-name "${STACK_NAME}" \
        --query 'Stacks[0].StackStatus' \
        --output text
}

verify_stack_exists() {
    local output
    local status
    local error_file

    error_file="$(mktemp)"

    if output="$(aws_cli_region cloudformation describe-stacks \
        --stack-name "${STACK_NAME}" \
        --output json 2>"${error_file}")"; then
        rm -f "${error_file}"
        status="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["Stacks"][0]["StackStatus"])' <<< "${output}")"
        log "Current stack status: ${status}"
        return 0
    fi

    if grep -q "does not exist" "${error_file}" ||
        grep -q "Stack with id .* does not exist" "${error_file}"; then
        rm -f "${error_file}"
        error "CloudFormation stack does not exist: ${STACK_NAME}"
        return 1
    fi

    cat "${error_file}" >&2
    rm -f "${error_file}"
    error "Unable to inspect stack. Check IAM permissions, Region, and AWS connectivity."
    return 1
}

display_recent_stack_events() {
    log "Recent CloudFormation stack events:"

    aws_cli_region cloudformation describe-stack-events \
        --stack-name "${STACK_NAME}" \
        --max-items 20 \
        --query 'StackEvents[].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' \
        --output table
}

confirm_environment() {
    local confirmation

    printf '\n'
    warning "You are about to perform a recovery operation."
    printf 'Environment: %s\n' "${ENVIRONMENT}"
    printf 'Stack:       %s\n' "${STACK_NAME}"
    printf 'AWS Region:  %s\n' "${AWS_REGION_VALUE}"
    printf '\n'
    printf 'Type the environment name to continue: '
    read -r confirmation

    if [[ "${confirmation}" != "${ENVIRONMENT}" ]]; then
        warning "Environment confirmation did not match. Operation cancelled."
        return 1
    fi
}

confirm_rollback() {
    local confirmation

    printf '\n'
    warning "CloudFormation will attempt to continue the failed update rollback."
    warning "Resources listed in --skip-resources may remain inconsistent with the template."
    printf 'Type CONTINUE-ROLLBACK to proceed: '
    read -r confirmation

    if [[ "${confirmation}" != "CONTINUE-ROLLBACK" ]]; then
        warning "Recovery cancelled."
        return 1
    fi
}

confirm_previous_template_update() {
    local confirmation

    printf '\n'
    warning "The previous-template mode will create a new CloudFormation update."
    warning "Review the change set carefully before execution."
    printf 'Type EXECUTE-CHANGE-SET to proceed: '
    read -r confirmation

    if [[ "${confirmation}" != "EXECUTE-CHANGE-SET" ]]; then
        warning "Change set execution cancelled."
        return 1
    fi
}

validate_template_and_parameters() {
    local template_size

    TEMPLATE_FILE="$(resolve_file_path "${TEMPLATE_FILE}")"
    PARAMETERS_FILE="$(resolve_file_path "${PARAMETERS_FILE}")"

    if [[ ! -f "${TEMPLATE_FILE}" ]]; then
        error "Template file not found: ${TEMPLATE_FILE}"
        return 1
    fi

    if [[ ! -f "${PARAMETERS_FILE}" ]]; then
        error "Parameter file not found: ${PARAMETERS_FILE}"
        return 1
    fi

    if ! python3 -m json.tool "${PARAMETERS_FILE}" >/dev/null; then
        error "Parameter file is not valid JSON: ${PARAMETERS_FILE}"
        return 1
    fi

    if ! python3 - "${PARAMETERS_FILE}" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as file:
    parameters = json.load(file)

if not isinstance(parameters, list):
    raise SystemExit("Parameter file must contain a JSON array.")

for index, parameter in enumerate(parameters):
    if not isinstance(parameter, dict):
        raise SystemExit(f"Parameter entry {index} must be an object.")

    if not isinstance(parameter.get("ParameterKey"), str):
        raise SystemExit(f"Parameter entry {index} requires ParameterKey.")

    if not isinstance(parameter.get("ParameterValue"), str):
        raise SystemExit(f"Parameter entry {index} requires ParameterValue.")
PY
    then
        error "Parameter file does not follow the CloudFormation parameter-file format."
        return 1
    fi

    template_size="$(wc -c < "${TEMPLATE_FILE}" | tr -d '[:space:]')"

    if (( template_size > MAX_TEMPLATE_BYTES )); then
        error "Template exceeds the ${MAX_TEMPLATE_BYTES}-byte TemplateBody limit."
        error "Use an S3-hosted TemplateURL workflow for larger templates."
        return 1
    fi

    log "Validating CloudFormation template..."

    aws_cli_region cloudformation validate-template \
        --template-body "file://${TEMPLATE_FILE}" \
        --output json >/dev/null

    success "Template and parameter JSON validation completed."
}

wait_for_stack_status() {
    local expected_status="$1"
    local start_time
    local elapsed
    local current_status

    start_time="$(date +%s)"

    log "Waiting for stack status: ${expected_status}"

    while true; do
        if ! current_status="$(get_stack_status 2>/dev/null)"; then
            error "Unable to retrieve current stack status."
            return 1
        fi

        if [[ "${current_status}" == "${expected_status}" ]]; then
            success "Stack reached ${expected_status}."
            return 0
        fi

        case "${current_status}" in
            UPDATE_ROLLBACK_FAILED|UPDATE_FAILED|ROLLBACK_FAILED|CREATE_FAILED|DELETE_FAILED|IMPORT_ROLLBACK_FAILED|UPDATE_ROLLBACK_COMPLETE_CLEANUP_FAILED)
                error "Stack entered failure status: ${current_status}"
                display_recent_stack_events || true
                return 1
                ;;
            *)
                ;;
        esac

        elapsed=$(( $(date +%s) - start_time ))

        if (( elapsed >= STACK_TIMEOUT_SECONDS )); then
            error "Timed out after ${STACK_TIMEOUT_SECONDS} seconds."
            error "Last observed stack status: ${current_status}"
            display_recent_stack_events || true
            return 1
        fi

        log "Current status: ${current_status} (${elapsed}s elapsed)."
        sleep "${POLL_INTERVAL}"
    done
}

continue_update_rollback() {
    local status
    local -a command_args

    status="$(get_stack_status)"

    if [[ "${status}" != "UPDATE_ROLLBACK_FAILED" ]]; then
        error "continue-update-rollback requires UPDATE_ROLLBACK_FAILED."
        error "Current stack status: ${status}"
        return 1
    fi

    display_recent_stack_events

    confirm_rollback || return 1

    command_args=(
        cloudformation
        continue-update-rollback
        --stack-name "${STACK_NAME}"
    )

    if [[ -n "${SKIP_RESOURCES_CSV}" ]]; then
        local -a resource_ids

        IFS=',' read -r -a resource_ids <<< "${SKIP_RESOURCES_CSV}"

        warning "Resources to skip during rollback:"
        printf '  %s\n' "${resource_ids[@]}"

        command_args+=(--resources-to-skip "${resource_ids[@]}")
    fi

    log "Submitting continue-update-rollback request..."

    aws_cli_region "${command_args[@]}" >/dev/null

    success "Rollback continuation request accepted."

    wait_for_stack_status "UPDATE_ROLLBACK_COMPLETE"

    display_recent_stack_events
}

cleanup_change_set() {
    if [[ "${CHANGE_SET_CREATED}" != true || -z "${CHANGE_SET_NAME}" ]]; then
        return 0
    fi

    if [[ "${EXECUTION_STARTED}" == true ]]; then
        return 0
    fi

    warning "Deleting unexecuted change set: ${CHANGE_SET_NAME}"

    aws_cli_region cloudformation delete-change-set \
        --stack-name "${STACK_NAME}" \
        --change-set-name "${CHANGE_SET_NAME}" >/dev/null 2>&1 || true
}

handle_exit() {
    local exit_code=$?

    cleanup_change_set

    exit "${exit_code}"
}

create_change_set() {
    local timestamp
    local output
    local error_file
    local result

    timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
    CHANGE_SET_NAME="recovery-${ENVIRONMENT}-${timestamp}-$$"
    error_file="$(mktemp)"

    log "Creating CloudFormation update change set..."

    if output="$(aws_cli_region cloudformation create-change-set \
        --stack-name "${STACK_NAME}" \
        --change-set-name "${CHANGE_SET_NAME}" \
        --change-set-type UPDATE \
        --template-body "file://${TEMPLATE_FILE}" \
        --parameters "file://${PARAMETERS_FILE}" \
        --description "Recovery deployment using a previously saved template" \
        --query 'Id' \
        --output text 2>"${error_file}")"; then
        rm -f "${error_file}"
        CHANGE_SET_CREATED=true
        printf 'Change set ARN: %s\n' "${output}"
        return 0
    fi

    result=$?

    if grep -Eiq "didn't contain changes|no updates are to be performed|The submitted information didn't contain changes" "${error_file}"; then
        warning "CloudFormation detected no changes. No update is required."
        rm -f "${error_file}"
        return 10
    fi

    cat "${error_file}" >&2
    rm -f "${error_file}"

    error "Unable to create change set."
    return "${result:-1}"
}

wait_for_change_set() {
    local status
    local reason

    log "Waiting for change set creation..."

    while true; do
        status="$(aws_cli_region cloudformation describe-change-set \
            --stack-name "${STACK_NAME}" \
            --change-set-name "${CHANGE_SET_NAME}" \
            --query 'Status' \
            --output text)"

        case "${status}" in
            CREATE_COMPLETE)
                success "Change set created successfully."
                return 0
                ;;
            FAILED)
                reason="$(aws_cli_region cloudformation describe-change-set \
                    --stack-name "${STACK_NAME}" \
                    --change-set-name "${CHANGE_SET_NAME}" \
                    --query 'StatusReason' \
                    --output text)"

                if grep -Eiq "didn't contain changes|no updates are to be performed|The submitted information didn't contain changes" <<< "${reason}"; then
                    warning "No infrastructure changes detected."
                    return 10
                fi

                error "Change set creation failed: ${reason}"
                return 1
                ;;
            CREATE_PENDING|CREATE_IN_PROGRESS)
                ;;
            *)
                warning "Unexpected change set status: ${status}"
                ;;
        esac

        sleep "${POLL_INTERVAL}"
    done
}

display_change_set() {
    log "Proposed CloudFormation changes:"

    aws_cli_region cloudformation describe-change-set \
        --stack-name "${STACK_NAME}" \
        --change-set-name "${CHANGE_SET_NAME}" \
        --query 'Changes[].ResourceChange.[Action,LogicalResourceId,ResourceType,Replacement,Scope]' \
        --output table

    printf '\n'
    log "Full change set details:"

    aws_cli_region cloudformation describe-change-set \
        --stack-name "${STACK_NAME}" \
        --change-set-name "${CHANGE_SET_NAME}" \
        --output json
}

execute_change_set() {
    confirm_previous_template_update || return 1

    log "Executing reviewed change set..."

    aws_cli_region cloudformation execute-change-set \
        --stack-name "${STACK_NAME}" \
        --change-set-name "${CHANGE_SET_NAME}" >/dev/null

    EXECUTION_STARTED=true
    CHANGE_SET_CREATED=false

    success "Change set execution started."

    wait_for_stack_status "UPDATE_COMPLETE"

    display_stack_outputs
    display_recent_stack_events
}

display_stack_outputs() {
    log "CloudFormation stack outputs:"

    aws_cli_region cloudformation describe-stacks \
        --stack-name "${STACK_NAME}" \
        --query 'Stacks[0].Outputs[].[OutputKey,OutputValue]' \
        --output table
}

previous_template_update() {
    local status
    local change_set_result

    status="$(get_stack_status)"

    case "${status}" in
        CREATE_COMPLETE|UPDATE_COMPLETE|UPDATE_ROLLBACK_COMPLETE|IMPORT_COMPLETE)
            success "Stack is in a stable state for an update."
            ;;
        *)
            error "Cannot deploy a previous template while stack status is ${status}."
            error "Resolve the current stack operation before attempting another update."
            return 1
            ;;
    esac

    validate_template_and_parameters
    display_recent_stack_events

    create_change_set || {
        change_set_result=$?

        if (( change_set_result == 10 )); then
            success "No changes to deploy."
            return 0
        fi

        return "${change_set_result}"
    }

    wait_for_change_set || {
        change_set_result=$?

        if (( change_set_result == 10 )); then
            success "No changes to deploy."
            return 0
        fi

        return "${change_set_result}"
    }

    display_change_set
    execute_change_set
}

main() {
    parse_arguments "$@"
    require_commands

    trap handle_exit EXIT

    verify_aws_identity
    verify_stack_exists
    confirm_environment

    case "${MODE}" in
        continue-update-rollback)
            continue_update_rollback
            ;;
        previous-template)
            previous_template_update
            ;;
    esac

    success "CloudFormation recovery workflow completed."
}

main "$@"

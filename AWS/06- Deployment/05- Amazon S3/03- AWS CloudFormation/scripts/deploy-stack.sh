#!/usr/bin/env bash

set -Eeuo pipefail

# Deploy the Amazon S3 static website CloudFormation stack.
#
# Usage:
#   ./deploy-stack.sh <dev|staging|production>
#   ./deploy-stack.sh production --region ap-south-1
#   ./deploy-stack.sh staging --profile development
#
# Environment variables:
#   AWS_REGION                 Default deployment Region
#   AWS_DEFAULT_REGION         Fallback deployment Region
#   AWS_PROFILE                AWS CLI profile
#   STACK_NAME_PREFIX          Stack name prefix (default: s3-static-website)
#   CHANGE_SET_TIMEOUT_SECONDS Change-set polling timeout (default: 300)
#   POLL_INTERVAL_SECONDS      Polling interval (default: 5)

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly CLOUDFORMATION_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
readonly TEMPLATE_FILE="${CLOUDFORMATION_DIR}/templates/static-website-bucket.yaml"
readonly PARAMETER_DIR="${CLOUDFORMATION_DIR}/parameters"

readonly STACK_NAME_PREFIX="${STACK_NAME_PREFIX:-s3-static-website}"
readonly CHANGE_SET_TIMEOUT_SECONDS="${CHANGE_SET_TIMEOUT_SECONDS:-300}"
readonly POLL_INTERVAL_SECONDS="${POLL_INTERVAL_SECONDS:-5}"

ENVIRONMENT=""
AWS_REGION_VALUE="${AWS_REGION:-${AWS_DEFAULT_REGION:-ap-south-1}}"
AWS_PROFILE_VALUE="${AWS_PROFILE:-}"

STACK_NAME=""
CHANGE_SET_NAME=""
CHANGE_SET_CREATED=false
STACK_EXISTS=false
CHANGE_SET_TYPE=""

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
  deploy-stack.sh <dev|staging|production> [options]

Options:
  --region REGION       AWS deployment Region
  --profile PROFILE     AWS CLI profile
  -h, --help            Display this help message

Environment variables:
  STACK_NAME_PREFIX          Stack name prefix
  CHANGE_SET_TIMEOUT_SECONDS Change-set creation timeout
  POLL_INTERVAL_SECONDS      Polling interval

Examples:
  ./deploy-stack.sh dev
  ./deploy-stack.sh staging --region ap-south-1
  ./deploy-stack.sh production --profile production
EOF
}

require_commands() {
    local missing=0
    local command_name

    for command_name in aws python3 date sleep; do
        if ! command -v "${command_name}" >/dev/null 2>&1; then
            error "Required command not found: ${command_name}"
            missing=1
        fi
    done

    if (( missing != 0 )); then
        return 1
    fi
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

    if [[ ! "${CHANGE_SET_TIMEOUT_SECONDS}" =~ ^[1-9][0-9]*$ ]]; then
        error "CHANGE_SET_TIMEOUT_SECONDS must be a positive integer."
        return 2
    fi

    if [[ ! "${POLL_INTERVAL_SECONDS}" =~ ^[1-9][0-9]*$ ]]; then
        error "POLL_INTERVAL_SECONDS must be a positive integer."
        return 2
    fi

    STACK_NAME="${STACK_NAME_PREFIX}-${ENVIRONMENT}"
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

validate_local_files() {
    local parameter_file="${PARAMETER_DIR}/${ENVIRONMENT}.json"
    local template_size

    if [[ ! -f "${TEMPLATE_FILE}" ]]; then
        error "CloudFormation template not found: ${TEMPLATE_FILE}"
        return 1
    fi

    if [[ ! -f "${parameter_file}" ]]; then
        error "Parameter file not found: ${parameter_file}"
        return 1
    fi

    if ! python3 -m json.tool "${parameter_file}" >/dev/null; then
        error "Invalid JSON parameter file: ${parameter_file}"
        return 1
    fi

    template_size="$(wc -c < "${TEMPLATE_FILE}" | tr -d '[:space:]')"

    if (( template_size > 51200 )); then
        error "Template exceeds the 51,200-byte TemplateBody limit (${template_size} bytes). Use an appropriately secured TemplateURL deployment workflow."
        return 1
    fi

    success "Template and parameter file exist and pass local syntax checks."
}

verify_aws_identity() {
    local identity
    local account_id
    local arn

    log "Verifying AWS identity..."

    if ! identity="$(aws_cli sts get-caller-identity --output json)"; then
        error "Unable to retrieve AWS caller identity. Check credentials and profile configuration."
        return 1
    fi

    account_id="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["Account"])' <<< "${identity}")"
    arn="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["Arn"])' <<< "${identity}")"

    printf 'AWS Account: %s\n' "${account_id}"
    printf 'Caller ARN:  %s\n' "${arn}"
    printf 'Region:      %s\n' "${AWS_REGION_VALUE}"
    printf 'Stack:       %s\n' "${STACK_NAME}"
    printf 'Environment: %s\n' "${ENVIRONMENT}"

    success "AWS identity verified."
}

validate_template_with_aws() {
    log "Validating CloudFormation template..."

    if ! aws_cli_region cloudformation validate-template \
        --template-body "file://${TEMPLATE_FILE}" >/dev/null; then
        error "CloudFormation template validation failed."
        return 1
    fi

    success "CloudFormation template validation passed."
}

confirm_environment() {
    local confirmation

    printf '\n'
    warning "You are preparing to deploy the %s environment." "${ENVIRONMENT}"
    printf 'Target stack: %s\n' "${STACK_NAME}"
    printf 'AWS Region:   %s\n' "${AWS_REGION_VALUE}"

    read -r -p "Type '${ENVIRONMENT}' to continue: " confirmation

    if [[ "${confirmation}" != "${ENVIRONMENT}" ]]; then
        warning "Environment confirmation did not match. Deployment cancelled."
        return 1
    fi
}

inspect_stack() {
    local status

    if ! aws_cli_region cloudformation describe-stacks \
        --stack-name "${STACK_NAME}" >/dev/null 2>&1; then
        STACK_EXISTS=false
        CHANGE_SET_TYPE="CREATE"
        log "Stack does not exist. A new stack will be created."
        return 0
    fi

    STACK_EXISTS=true

    status="$(aws_cli_region cloudformation describe-stacks \
        --stack-name "${STACK_NAME}" \
        --query 'Stacks[0].StackStatus' \
        --output text)"

    log "Current stack status: ${status}"

    case "${status}" in
        CREATE_COMPLETE|UPDATE_COMPLETE|UPDATE_ROLLBACK_COMPLETE|IMPORT_COMPLETE)
            CHANGE_SET_TYPE="UPDATE"
            ;;
        *)
            error "Stack is not in a deployable state: ${status}"
            error "Resolve the current stack operation or failure before deploying."
            return 1
            ;;
    esac
}

create_change_set() {
    local parameter_file="${PARAMETER_DIR}/${ENVIRONMENT}.json"
    local output
    local exit_code=0

    CHANGE_SET_NAME="${STACK_NAME}-deploy-$(date -u +%Y%m%dT%H%M%SZ)-$$"

    log "Creating ${CHANGE_SET_TYPE} change set: ${CHANGE_SET_NAME}"

    local -a command_args=(
        cloudformation
        create-change-set
        --stack-name "${STACK_NAME}"
        --change-set-name "${CHANGE_SET_NAME}"
        --change-set-type "${CHANGE_SET_TYPE}"
        --template-body "file://${TEMPLATE_FILE}"
        --parameters "file://${parameter_file}"
        --description "Deploy ${ENVIRONMENT} S3 static website infrastructure"
        --region "${AWS_REGION_VALUE}"
        --no-cli-pager
    )

    if [[ -n "${AWS_PROFILE_VALUE}" ]]; then
        command_args+=(--profile "${AWS_PROFILE_VALUE}")
    fi

    if output="$(aws "${command_args[@]}" 2>&1)"; then
        CHANGE_SET_CREATED=true
        printf '%s\n' "${output}"
        success "Change set created."
        return 0
    else
        exit_code=$?
    fi

    if grep -Eqi "didn't contain changes|no updates are to be performed|No updates are to be performed" <<< "${output}"; then
        warning "No infrastructure changes detected."
        return 10
    fi

    error "Unable to create change set."
    printf '%s\n' "${output}" >&2
    return "${exit_code}"
}

wait_for_change_set() {
    local start_time
    local elapsed
    local status
    local reason

    start_time="$(date +%s)"

    log "Waiting for change-set creation..."

    while true; do
        if ! status="$(aws_cli_region cloudformation describe-change-set \
            --stack-name "${STACK_NAME}" \
            --change-set-name "${CHANGE_SET_NAME}" \
            --query 'Status' \
            --output text 2>/dev/null)"; then
            error "Unable to inspect change-set status."
            return 1
        fi

        case "${status}" in
            CREATE_COMPLETE)
                success "Change set is ready."
                return 0
                ;;
            FAILED)
                reason="$(aws_cli_region cloudformation describe-change-set \
                    --stack-name "${STACK_NAME}" \
                    --change-set-name "${CHANGE_SET_NAME}" \
                    --query 'StatusReason' \
                    --output text 2>/dev/null || true)"

                if grep -Eqi "didn't contain changes|no updates are to be performed" <<< "${reason}"; then
                    warning "No infrastructure changes detected."
                    return 10
                fi

                error "Change-set creation failed: ${reason}"
                return 1
                ;;
            CREATE_PENDING|CREATE_IN_PROGRESS)
                ;;
            *)
                warning "Change-set status: ${status}"
                ;;
        esac

        elapsed=$(( $(date +%s) - start_time ))

        if (( elapsed >= CHANGE_SET_TIMEOUT_SECONDS )); then
            error "Timed out waiting for change-set creation."
            return 1
        fi

        sleep "${POLL_INTERVAL_SECONDS}"
    done
}

display_change_set() {
    log "Proposed infrastructure changes:"

    aws_cli_region cloudformation describe-change-set \
        --stack-name "${STACK_NAME}" \
        --change-set-name "${CHANGE_SET_NAME}" \
        --query 'Changes[].ResourceChange.[Action,LogicalResourceId,ResourceType,Replacement]' \
        --output table

    printf '\n'
    log "Full change-set details:"
    aws_cli_region cloudformation describe-change-set \
        --stack-name "${STACK_NAME}" \
        --change-set-name "${CHANGE_SET_NAME}" \
        --query '{StackName:StackName,ChangeSetName:ChangeSetName,Status:Status,Changes:Changes,Parameters:Parameters}' \
        --output json
}

confirm_change_set_execution() {
    local confirmation

    printf '\n'
    warning "Review the proposed infrastructure changes carefully."
    warning "Resource replacements or deletions may affect production resources."

    read -r -p "Execute this change set? Type 'yes' to proceed: " confirmation

    if [[ "${confirmation}" != "yes" ]]; then
        warning "Change-set execution cancelled."
        return 1
    fi
}

delete_change_set() {
    if [[ "${CHANGE_SET_CREATED}" != "true" || -z "${CHANGE_SET_NAME}" ]]; then
        return 0
    fi

    log "Deleting change set: ${CHANGE_SET_NAME}"

    if aws_cli_region cloudformation delete-change-set \
        --stack-name "${STACK_NAME}" \
        --change-set-name "${CHANGE_SET_NAME}" >/dev/null 2>&1; then
        CHANGE_SET_CREATED=false
        success "Change set deleted."
    else
        warning "Unable to delete change set automatically: ${CHANGE_SET_NAME}"
    fi
}

cleanup() {
    local exit_code=$?

    if [[ "${CHANGE_SET_CREATED}" == "true" ]]; then
        delete_change_set || true
    fi

    exit "${exit_code}"
}

trap cleanup EXIT

execute_change_set() {
    log "Executing change set..."

    if ! aws_cli_region cloudformation execute-change-set \
        --stack-name "${STACK_NAME}" \
        --change-set-name "${CHANGE_SET_NAME}"; then
        error "Failed to execute change set."
        return 1
    fi

    CHANGE_SET_CREATED=false
    success "Change set execution started."
}

wait_for_stack_completion() {
    local start_time
    local elapsed
    local status
    local reason

    start_time="$(date +%s)"

    log "Waiting for CloudFormation stack operation to complete..."

    while true; do
        if ! status="$(aws_cli_region cloudformation describe-stacks \
            --stack-name "${STACK_NAME}" \
            --query 'Stacks[0].StackStatus' \
            --output text 2>/dev/null)"; then
            error "Unable to retrieve stack status."
            return 1
        fi

        case "${status}" in
            CREATE_COMPLETE|UPDATE_COMPLETE)
                success "Stack deployment completed: ${status}"
                return 0
                ;;
            CREATE_FAILED|ROLLBACK_COMPLETE|ROLLBACK_FAILED|UPDATE_ROLLBACK_FAILED|UPDATE_FAILED)
                reason="$(aws_cli_region cloudformation describe-stacks \
                    --stack-name "${STACK_NAME}" \
                    --query 'Stacks[0].StackStatusReason' \
                    --output text 2>/dev/null || true)"

                error "Stack deployment failed: ${status}"
                error "Reason: ${reason}"
                return 1
                ;;
            CREATE_IN_PROGRESS|UPDATE_IN_PROGRESS|UPDATE_COMPLETE_CLEANUP_IN_PROGRESS|UPDATE_ROLLBACK_IN_PROGRESS|UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS)
                ;;
            *)
                warning "Current stack status: ${status}"
                ;;
        esac

        elapsed=$(( $(date +%s) - start_time ))

        if (( elapsed >= CHANGE_SET_TIMEOUT_SECONDS * 10 )); then
            error "Timed out waiting for stack deployment."
            return 1
        fi

        sleep "${POLL_INTERVAL_SECONDS}"
    done
}

display_stack_outputs() {
    log "CloudFormation stack outputs:"

    aws_cli_region cloudformation describe-stacks \
        --stack-name "${STACK_NAME}" \
        --query 'Stacks[0].Outputs' \
        --output table

    printf '\n'
    success "Deployment workflow completed for ${ENVIRONMENT}."
}

display_stack_events_on_failure() {
    warning "Recent CloudFormation stack events:"

    aws_cli_region cloudformation describe-stack-events \
        --stack-name "${STACK_NAME}" \
        --max-items 30 \
        --query 'StackEvents[].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' \
        --output table || true
}

main() {
    parse_arguments "$@"
    require_commands
    validate_local_files
    verify_aws_identity
    validate_template_with_aws
    confirm_environment
    inspect_stack

    local change_set_result=0

    create_change_set || change_set_result=$?

    if (( change_set_result == 10 )); then
        success "Deployment skipped because there are no changes."
        exit 0
    elif (( change_set_result != 0 )); then
        exit "${change_set_result}"
    fi

    local wait_result=0

    wait_for_change_set || wait_result=$?

    if (( wait_result == 10 )); then
        warning "No changes are required."
        exit 0
    elif (( wait_result != 0 )); then
        exit 1
    fi

    display_change_set
    confirm_change_set_execution
    execute_change_set

    if ! wait_for_stack_completion; then
        display_stack_events_on_failure
        exit 1
    fi

    display_stack_outputs
}

main "$@"

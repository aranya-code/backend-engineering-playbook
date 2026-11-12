#!/usr/bin/env bash

set -Eeuo pipefail

# Detect configuration drift in an Amazon S3 CloudFormation stack.
#
# Usage:
#   ./detect-drift.sh <dev|staging|production>
#   ./detect-drift.sh production --region ap-south-1
#   ./detect-drift.sh staging --profile development
#
# Environment variables:
#   AWS_REGION                 Default deployment Region
#   AWS_DEFAULT_REGION         Fallback deployment Region
#   AWS_PROFILE                AWS CLI profile
#   STACK_NAME_PREFIX          Stack name prefix (default: s3-static-website)
#   DRIFT_POLL_INTERVAL        Polling interval in seconds (default: 10)
#   DRIFT_TIMEOUT_SECONDS      Detection timeout in seconds (default: 1800)

readonly STACK_NAME_PREFIX="${STACK_NAME_PREFIX:-s3-static-website}"
readonly DRIFT_POLL_INTERVAL="${DRIFT_POLL_INTERVAL:-10}"
readonly DRIFT_TIMEOUT_SECONDS="${DRIFT_TIMEOUT_SECONDS:-1800}"

ENVIRONMENT=""
AWS_REGION_VALUE="${AWS_REGION:-${AWS_DEFAULT_REGION:-ap-south-1}}"
AWS_PROFILE_VALUE="${AWS_PROFILE:-}"
STACK_NAME=""

DETECTION_ID=""
DETECTION_STARTED=false

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
  detect-drift.sh <dev|staging|production> [options]

Options:
  --region REGION       AWS deployment Region
  --profile PROFILE     AWS CLI profile
  -h, --help            Display this help message

Environment variables:
  STACK_NAME_PREFIX     CloudFormation stack name prefix
  DRIFT_POLL_INTERVAL   Polling interval in seconds
  DRIFT_TIMEOUT_SECONDS Detection timeout in seconds

Examples:
  ./detect-drift.sh dev
  ./detect-drift.sh staging --region ap-south-1
  ./detect-drift.sh production --profile production
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

    if [[ ! "${DRIFT_POLL_INTERVAL}" =~ ^[1-9][0-9]*$ ]]; then
        error "DRIFT_POLL_INTERVAL must be a positive integer."
        return 2
    fi

    if [[ ! "${DRIFT_TIMEOUT_SECONDS}" =~ ^[1-9][0-9]*$ ]]; then
        error "DRIFT_TIMEOUT_SECONDS must be a positive integer."
        return 2
    fi

    STACK_NAME="${STACK_NAME_PREFIX}-${ENVIRONMENT}"
}

require_commands() {
    local missing=0
    local command_name

    for command_name in aws python3 sleep date; do
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

verify_stack() {
    local status

    log "Checking CloudFormation stack..."

    if ! aws_cli_region cloudformation describe-stacks \
        --stack-name "${STACK_NAME}" >/dev/null 2>&1; then
        error "CloudFormation stack not found or inaccessible: ${STACK_NAME}"
        return 1
    fi

    status="$(aws_cli_region cloudformation describe-stacks \
        --stack-name "${STACK_NAME}" \
        --query 'Stacks[0].StackStatus' \
        --output text)"

    log "Current stack status: ${status}"

    case "${status}" in
        CREATE_COMPLETE|UPDATE_COMPLETE|UPDATE_ROLLBACK_COMPLETE|IMPORT_COMPLETE)
            success "Stack is in a stable state."
            ;;
        *)
            error "Drift detection requires a stable stack. Current status: ${status}"
            return 1
            ;;
    esac
}

start_drift_detection() {
    log "Starting CloudFormation drift detection..."

    DETECTION_ID="$(aws_cli_region cloudformation detect-stack-drift \
        --stack-name "${STACK_NAME}" \
        --query 'StackDriftDetectionId' \
        --output text)"

    if [[ -z "${DETECTION_ID}" || "${DETECTION_ID}" == "None" ]]; then
        error "CloudFormation did not return a drift detection ID."
        return 1
    fi

    DETECTION_STARTED=true

    printf 'Detection ID: %s\n' "${DETECTION_ID}"
    success "Drift detection started."
}

wait_for_drift_detection() {
    local start_time
    local elapsed
    local status
    local reason

    start_time="$(date +%s)"

    log "Waiting for drift detection to complete..."

    while true; do
        if ! status="$(aws_cli_region cloudformation describe-stack-drift-detection-status \
            --stack-drift-detection-id "${DETECTION_ID}" \
            --query 'DetectionStatus' \
            --output text)"; then
            error "Unable to retrieve drift detection status."
            return 1
        fi

        case "${status}" in
            DETECTION_COMPLETE)
                success "Drift detection completed."
                return 0
                ;;
            DETECTION_FAILED)
                reason="$(aws_cli_region cloudformation describe-stack-drift-detection-status \
                    --stack-drift-detection-id "${DETECTION_ID}" \
                    --query 'DetectionStatusReason' \
                    --output text 2>/dev/null || true)"

                error "Drift detection failed: ${reason}"
                return 1
                ;;
            DETECTION_IN_PROGRESS)
                ;;
            *)
                warning "Unexpected detection status: ${status}"
                ;;
        esac

        elapsed=$(( $(date +%s) - start_time ))

        if (( elapsed >= DRIFT_TIMEOUT_SECONDS )); then
            error "Drift detection timed out after ${DRIFT_TIMEOUT_SECONDS} seconds."
            return 1
        fi

        log "Detection still running (${elapsed}s elapsed)."
        sleep "${DRIFT_POLL_INTERVAL}"
    done
}

display_drift_summary() {
    local drift_status
    local drifted_count
    local in_sync_count
    local not_checked_count
    local total_count

    log "Retrieving stack drift summary..."

    drift_status="$(aws_cli_region cloudformation describe-stack-drift-detection-status \
        --stack-drift-detection-id "${DETECTION_ID}" \
        --query 'StackDriftStatus' \
        --output text)"

    drifted_count="$(aws_cli_region cloudformation describe-stack-drift-detection-status \
        --stack-drift-detection-id "${DETECTION_ID}" \
        --query 'DriftedStackResourceCount' \
        --output text)"

    in_sync_count="$(aws_cli_region cloudformation describe-stack-drift-detection-status \
        --stack-drift-detection-id "${DETECTION_ID}" \
        --query 'StackResourceDriftStatusCounts.IN_SYNC' \
        --output text)"

    not_checked_count="$(aws_cli_region cloudformation describe-stack-drift-detection-status \
        --stack-drift-detection-id "${DETECTION_ID}" \
        --query 'StackResourceDriftStatusCounts.NOT_CHECKED' \
        --output text)"

    total_count="$(aws_cli_region cloudformation describe-stack-drift-detection-status \
        --stack-drift-detection-id "${DETECTION_ID}" \
        --query 'EvaluatedStackResourceCount' \
        --output text)"

    printf '\n'
    printf '%s\n' "========================================"
    printf '%s\n' "CloudFormation Drift Summary"
    printf '%s\n' "========================================"
    printf 'Stack:              %s\n' "${STACK_NAME}"
    printf 'Drift status:       %s\n' "${drift_status}"
    printf 'Drifted resources:  %s\n' "${drifted_count}"
    printf 'In-sync resources:  %s\n' "${in_sync_count:-0}"
    printf 'Not checked:        %s\n' "${not_checked_count:-0}"
    printf 'Evaluated resources: %s\n' "${total_count}"
    printf '%s\n' "========================================"

    case "${drift_status}" in
        DRIFTED)
            warning "Stack configuration drift detected."
            ;;
        IN_SYNC)
            success "No drift detected among evaluated resources."
            ;;
        NOT_CHECKED)
            warning "Stack drift status is NOT_CHECKED."
            ;;
        *)
            warning "Unexpected stack drift status: ${drift_status}"
            ;;
    esac
}

display_resource_drifts() {
    local drifted_count
    local not_checked_count

    drifted_count="$(aws_cli_region cloudformation describe-stack-resource-drifts \
        --stack-name "${STACK_NAME}" \
        --stack-resource-drift-status-filters MODIFIED DELETED \
        --query 'length(StackResourceDrifts)' \
        --output text)"

    printf '\n'
    log "Drifted resources (MODIFIED or DELETED):"

    if [[ "${drifted_count}" == "0" ]]; then
        success "No MODIFIED or DELETED resources reported."
    else
        aws_cli_region cloudformation describe-stack-resource-drifts \
            --stack-name "${STACK_NAME}" \
            --stack-resource-drift-status-filters MODIFIED DELETED \
            --query 'StackResourceDrifts[].[LogicalResourceId,ResourceType,StackResourceDriftStatus,Timestamp]' \
            --output table

        warning "Review detailed resource differences before taking corrective action."
    fi

    printf '\n'
    log "Resources not checked by CloudFormation drift detection:"

    not_checked_count="$(aws_cli_region cloudformation describe-stack-resource-drifts \
        --stack-name "${STACK_NAME}" \
        --stack-resource-drift-status-filters NOT_CHECKED \
        --query 'length(StackResourceDrifts)' \
        --output text)"

    if [[ "${not_checked_count}" == "0" ]]; then
        success "No NOT_CHECKED resources reported."
    else
        aws_cli_region cloudformation describe-stack-resource-drifts \
            --stack-name "${STACK_NAME}" \
            --stack-resource-drift-status-filters NOT_CHECKED \
            --query 'StackResourceDrifts[].[LogicalResourceId,ResourceType,StackResourceDriftStatus]' \
            --output table

        warning "Some resources could not be evaluated."
    fi
}

display_drift_details() {
    local drifted_count

    drifted_count="$(aws_cli_region cloudformation describe-stack-resource-drifts \
        --stack-name "${STACK_NAME}" \
        --stack-resource-drift-status-filters MODIFIED DELETED \
        --query 'length(StackResourceDrifts)' \
        --output text)"

    if [[ "${drifted_count}" == "0" ]]; then
        return 0
    fi

    printf '\n'
    log "Detailed drift information:"

    aws_cli_region cloudformation describe-stack-resource-drifts \
        --stack-name "${STACK_NAME}" \
        --stack-resource-drift-status-filters MODIFIED DELETED \
        --query 'StackResourceDrifts[].{LogicalResourceId:LogicalResourceId,ResourceType:ResourceType,Status:StackResourceDriftStatus,Expected:ExpectedProperties,Actual:ActualProperties,Difference:PropertyDifferences}' \
        --output json
}

main() {
    parse_arguments "$@"
    require_commands
    verify_aws_identity
    verify_stack
    start_drift_detection
    wait_for_drift_detection
    display_drift_summary
    display_resource_drifts
    display_drift_details

    local final_status

    final_status="$(aws_cli_region cloudformation describe-stack-drift-detection-status \
        --stack-drift-detection-id "${DETECTION_ID}" \
        --query 'StackDriftStatus' \
        --output text)"

    case "${final_status}" in
        DRIFTED)
            warning "Drift investigation is required. No automatic remediation was performed."
            exit 1
            ;;
        IN_SYNC)
            success "Drift check completed. Evaluated resources are in sync."
            exit 0
            ;;
        *)
            warning "Drift check completed with status: ${final_status}"
            exit 2
            ;;
    esac
}

main "$@"

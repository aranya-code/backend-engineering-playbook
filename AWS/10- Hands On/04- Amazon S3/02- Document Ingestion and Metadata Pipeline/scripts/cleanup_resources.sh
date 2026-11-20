#!/usr/bin/env bash
#
# Safely clean up the Document Ingestion and Metadata Pipeline resources.
#
# This script delegates infrastructure destruction to Terraform. It does not
# independently delete AWS resources, avoiding conflicts with Terraform state.
#
# Important:
# - Terraform resources include S3, DynamoDB, SQS, Lambda, IAM, EventBridge,
#   and CloudWatch resources.
# - DynamoDB tables and CloudWatch log groups have prevent_destroy lifecycle
#   protection in the current infrastructure configuration.
# - S3 bucket deletion can permanently remove uploaded documents when
#   force_destroy_documents_bucket is enabled.
# - DynamoDB deletion protection may also need to be disabled explicitly.
# - Terraform state and backend configuration must remain available.
#
# Usage:
#   ./scripts/cleanup_resources.sh
#   ./scripts/cleanup_resources.sh --environment dev
#   ./scripts/cleanup_resources.sh --environment dev --auto-approve
#   ./scripts/cleanup_resources.sh --environment dev --plan-only
#
# Optional environment variables:
#   TF_VAR_aws_region
#   TF_VAR_environment
#   TF_VAR_force_destroy_documents_bucket
#   TF_VAR_enable_deletion_protection
#
# Run from any directory. Terraform is executed from infrastructure/terraform.

set -Eeuo pipefail

SCRIPT_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1
    pwd
)"

PROJECT_ROOT="$(
    cd -- "${SCRIPT_DIR}/.." >/dev/null 2>&1
    pwd
)"

TERRAFORM_DIR="${PROJECT_ROOT}/infrastructure/terraform"

ENVIRONMENT="${TF_VAR_environment:-dev}"
AUTO_APPROVE=false
PLAN_ONLY=false
SKIP_CONFIRMATION=false

log() {
    printf '[INFO] %s\n' "$*"
}

warn() {
    printf '[WARN] %s\n' "$*" >&2
}

error() {
    printf '[ERROR] %s\n' "$*" >&2
}

usage() {
    cat <<'EOF'
Usage:
  cleanup_resources.sh [OPTIONS]

Options:
  --environment NAME   Terraform environment value (default: dev)
  --auto-approve       Apply the destroy plan without interactive confirmation
  --plan-only          Generate and display a destroy plan without applying it
  --yes                Skip the script confirmation prompt
  --help               Display this help message

Environment:
  TF_VAR_aws_region
  TF_VAR_environment
  TF_VAR_force_destroy_documents_bucket
  TF_VAR_enable_deletion_protection

Examples:
  ./scripts/cleanup_resources.sh
  ./scripts/cleanup_resources.sh --environment dev
  ./scripts/cleanup_resources.sh --environment dev --plan-only
  ./scripts/cleanup_resources.sh --environment dev --auto-approve

Notes:
  --auto-approve bypasses only the script's interactive confirmation.
  Terraform lifecycle protections and AWS deletion protection still apply.
EOF
}

cleanup_temp_files() {
    if [[ -n "${DESTROY_PLAN_FILE:-}" && -f "${DESTROY_PLAN_FILE}" ]]; then
        rm -f -- "${DESTROY_PLAN_FILE}"
    fi
}

handle_error() {
    local exit_code=$?

    error "Cleanup failed with exit code ${exit_code}."
    error "Review the Terraform output and AWS resource state before retrying."
    exit "${exit_code}"
}

require_command() {
    local command_name="$1"

    if ! command -v "${command_name}" >/dev/null 2>&1; then
        error "Required command not found: ${command_name}"
        exit 1
    fi
}

confirm_cleanup() {
    local expected_value="destroy-${ENVIRONMENT}"
    local confirmation

    if [[ "${SKIP_CONFIRMATION}" == true ]]; then
        return
    fi

    printf '\n'
    warn "This operation can permanently delete AWS resources."
    warn "Environment: ${ENVIRONMENT}"
    warn "Terraform directory: ${TERRAFORM_DIR}"
    printf '\n'
    printf 'Type "%s" to continue: ' "${expected_value}"

    read -r confirmation

    if [[ "${confirmation}" != "${expected_value}" ]]; then
        log "Confirmation did not match. Cleanup cancelled."
        exit 0
    fi
}

validate_environment() {
    if [[ ! "${ENVIRONMENT}" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        error "Invalid environment name: ${ENVIRONMENT}"
        error "Use only letters, numbers, underscores, and hyphens."
        exit 1
    fi
}

validate_terraform_directory() {
    if [[ ! -d "${TERRAFORM_DIR}" ]]; then
        error "Terraform directory not found: ${TERRAFORM_DIR}"
        exit 1
    fi

    if [[ ! -f "${TERRAFORM_DIR}/versions.tf" ]]; then
        error "Terraform configuration not found in ${TERRAFORM_DIR}."
        exit 1
    fi
}

validate_aws_identity() {
    local caller_identity
    local account_id
    local arn

    require_command aws

    log "Checking AWS credentials and caller identity."

    if ! caller_identity="$(aws sts get-caller-identity --output json)"; then
        error "Unable to retrieve AWS caller identity."
        error "Configure valid AWS credentials before continuing."
        exit 1
    fi

    account_id="$(
        printf '%s' "${caller_identity}" |
            python3 -c 'import json, sys; print(json.load(sys.stdin)["Account"])'
    )"

    arn="$(
        printf '%s' "${caller_identity}" |
            python3 -c 'import json, sys; print(json.load(sys.stdin)["Arn"])'
    )"

    log "AWS account: ${account_id}"
    log "AWS principal: ${arn}"

    if [[ -n "${EXPECTED_AWS_ACCOUNT_ID:-}" ]]; then
        if [[ "${account_id}" != "${EXPECTED_AWS_ACCOUNT_ID}" ]]; then
            error "AWS account mismatch."
            error "Expected: ${EXPECTED_AWS_ACCOUNT_ID}"
            error "Actual:   ${account_id}"
            exit 1
        fi
    fi
}

validate_terraform_state() {
    log "Checking Terraform state."

    if ! terraform state list >/dev/null 2>&1; then
        error "Terraform state is unavailable or not initialized."
        error "Run terraform init and verify the configured backend."
        exit 1
    fi

    local state_count

    state_count="$(
        terraform state list |
            awk 'NF { count++ } END { print count + 0 }'
    )"

    if [[ "${state_count}" -eq 0 ]]; then
        log "Terraform state contains no managed resources."
        log "Nothing to destroy."
        exit 0
    fi

    log "Terraform manages ${state_count} resource instance(s)."
}

show_protected_resource_warning() {
    cat <<'EOF'

Important infrastructure protections:

- DynamoDB tables use prevent_destroy.
- CloudWatch log groups use prevent_destroy.
- DynamoDB deletion protection may be enabled.
- The S3 bucket may contain documents and object versions.
- Terraform may refuse destruction until lifecycle protections are
  deliberately changed in the configuration.
- S3 objects can be permanently removed if bucket force-destroy is enabled.

Do not remove lifecycle protection or disable deletion protection merely to
make a destroy command succeed. Confirm retention, backup, and recovery
requirements first.

If Terraform refuses destruction because of prevent_destroy, review the
specific resource and make an intentional, reviewed configuration change.
EOF
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --environment)
                if [[ $# -lt 2 || -z "$2" ]]; then
                    error "--environment requires a value."
                    exit 1
                fi

                ENVIRONMENT="$2"
                shift 2
                ;;

            --auto-approve)
                AUTO_APPROVE=true
                SKIP_CONFIRMATION=true
                shift
                ;;

            --plan-only)
                PLAN_ONLY=true
                shift
                ;;

            --yes)
                SKIP_CONFIRMATION=true
                shift
                ;;

            --help|-h)
                usage
                exit 0
                ;;

            *)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

main() {
    parse_arguments "$@"
    validate_environment
    validate_terraform_directory

    require_command terraform
    require_command python3

    trap cleanup_temp_files EXIT
    trap handle_error ERR

    if [[ "${TF_VAR_environment:-}" != "${ENVIRONMENT}" ]]; then
        export TF_VAR_environment="${ENVIRONMENT}"
    fi

    cd "${TERRAFORM_DIR}"

    log "Initializing Terraform."
    terraform init -input=false

    log "Validating Terraform configuration."
    terraform validate

    validate_aws_identity
    validate_terraform_state

    show_protected_resource_warning

    if [[ "${PLAN_ONLY}" == false ]]; then
        confirm_cleanup
    fi

    DESTROY_PLAN_FILE="$(mktemp "${TMPDIR:-/tmp}/s3-pipeline-destroy.XXXXXX")"

    log "Generating Terraform destroy plan."

    terraform plan \
        -destroy \
        -input=false \
        -var="environment=${ENVIRONMENT}" \
        -out="${DESTROY_PLAN_FILE}"

    log "Reviewing planned resource changes."
    terraform show "${DESTROY_PLAN_FILE}"

    if [[ "${PLAN_ONLY}" == true ]]; then
        log "Plan-only mode enabled. No resources were deleted."
        log "Review the destroy plan before running cleanup."
        return 0
    fi

    if [[ "${AUTO_APPROVE}" == false ]]; then
        printf '\n'
        warn "Review the destroy plan carefully."
        printf 'Type "apply-destroy" to apply this exact plan: '

        local confirmation
        read -r confirmation

        if [[ "${confirmation}" != "apply-destroy" ]]; then
            log "Destroy operation cancelled."
            return 0
        fi
    fi

    log "Applying the reviewed Terraform destroy plan."
    terraform apply -input=false "${DESTROY_PLAN_FILE}"

    log "Terraform destroy operation completed."
    warn "Verify AWS resources and retained data independently."
    warn "Resources protected by prevent_destroy or AWS deletion protection"
    warn "may remain and require a separately reviewed cleanup procedure."
}

main "$@"
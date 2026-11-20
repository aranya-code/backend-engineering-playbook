#!/usr/bin/env bash

set -Eeuo pipefail

# Safely destroy the Data Lake Storage and Lifecycle Automation infrastructure.
#
# Default behavior:
#   - Inspect the active AWS identity.
#   - Verify the Terraform workspace and target environment.
#   - Display the Terraform destruction plan.
#   - Do not destroy resources.
#
# Destruction requires both:
#   --destroy
#   Explicit AWS account ID confirmation.
#
# Important:
#   - This script does not delete objects manually from S3.
#   - S3 buckets must be empty before Terraform can destroy them.
#   - force_destroy_buckets must be reviewed separately if bucket contents
#     are intentionally disposable.
#   - The KMS key has prevent_destroy enabled in encryption.tf. Terraform
#     will refuse to destroy it until that protection is deliberately
#     reviewed and changed.
#   - Terraform state and backend resources are not deleted by this script.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
TERRAFORM_DIR="${PROJECT_ROOT}/infrastructure/terraform"

DEFAULT_REGION="ap-south-1"
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-${TF_VAR_aws_region:-${DEFAULT_REGION}}}}"
ENVIRONMENT="${ENVIRONMENT:-${TF_VAR_environment:-dev}}"

DESTROY_REQUESTED=false
AUTO_APPROVE=false
VAR_FILE=""
PLAN_FILE=""

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
  ./cleanup_resources.sh [options]

Options:
  --destroy             Execute the reviewed Terraform destroy plan.
                        Without this option, only a destroy plan is generated.
  --auto-approve        Skip the final interactive confirmation.
                        Requires --destroy and EXPECTED_AWS_ACCOUNT_ID.
  --region REGION       AWS Region. Defaults to ap-south-1 unless overridden
                        by AWS_REGION, AWS_DEFAULT_REGION, or TF_VAR_aws_region.
  --environment NAME    Deployment environment. Defaults to dev unless
                        overridden by ENVIRONMENT or TF_VAR_environment.
  --var-file PATH       Optional Terraform variable file.
  -h, --help            Display this help message.

Environment variables:
  AWS_PROFILE                 AWS CLI profile to use.
  EXPECTED_AWS_ACCOUNT_ID     Required for --auto-approve. Recommended for
                              every destructive execution.
  TF_WORKSPACE                Optional Terraform workspace name.
  TF_IN_AUTOMATION            Set to true in CI/CD environments.

Examples:
  ./cleanup_resources.sh
  ./cleanup_resources.sh --region ap-south-1 --environment dev
  ./cleanup_resources.sh --destroy --environment dev
  ./cleanup_resources.sh --destroy --var-file environments/dev.tfvars

Automated execution:
  EXPECTED_AWS_ACCOUNT_ID=123456789012 \
    TF_IN_AUTOMATION=true \
    ./cleanup_resources.sh --destroy --auto-approve

Safety:
  - The default operation is plan-only.
  - Destruction requires an exact AWS account ID confirmation unless
    --auto-approve is used with EXPECTED_AWS_ACCOUNT_ID.
  - The script never runs aws s3 rm or recursively empties buckets.
  - Review retained objects, versions, delete markers, and incomplete
    multipart uploads before attempting bucket deletion.
  - Terraform state and remote backend resources are retained.
EOF
}

cleanup() {
    if [[ -n "${PLAN_FILE}" && -f "${PLAN_FILE}" ]]; then
        rm -f -- "${PLAN_FILE}"
    fi
}

on_error() {
    local exit_code=$?

    error "Cleanup stopped at line ${BASH_LINENO[0]:-unknown}."
    error "Exit code: ${exit_code}."

    exit "${exit_code}"
}

trap cleanup EXIT
trap on_error ERR

while (($# > 0)); do
    case "$1" in
        --destroy)
            DESTROY_REQUESTED=true
            shift
            ;;
        --auto-approve)
            AUTO_APPROVE=true
            shift
            ;;
        --region)
            if [[ $# -lt 2 || -z "${2}" ]]; then
                error "--region requires a value."
                usage
                exit 2
            fi

            REGION="$2"
            shift 2
            ;;
        --environment)
            if [[ $# -lt 2 || -z "${2}" ]]; then
                error "--environment requires a value."
                usage
                exit 2
            fi

            ENVIRONMENT="$2"
            shift 2
            ;;
        --var-file)
            if [[ $# -lt 2 || -z "${2}" ]]; then
                error "--var-file requires a path."
                usage
                exit 2
            fi

            VAR_FILE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            usage
            exit 2
            ;;
    esac
done

if [[ "${AUTO_APPROVE}" == true && "${DESTROY_REQUESTED}" != true ]]; then
    error "--auto-approve requires --destroy."
    exit 2
fi

if [[ ! -d "${TERRAFORM_DIR}" ]]; then
    error "Terraform directory does not exist: ${TERRAFORM_DIR}"
    exit 1
fi

if [[ ! -f "${TERRAFORM_DIR}/versions.tf" ]]; then
    error "Terraform configuration is missing versions.tf."
    exit 1
fi

if [[ ! "${REGION}" =~ ^[a-z]{2}(-gov)?-[a-z]+-[0-9]+$ ]]; then
    error "Invalid AWS Region format: ${REGION}"
    exit 1
fi

if [[ ! "${ENVIRONMENT}" =~ ^[a-zA-Z0-9][a-zA-Z0-9_-]*$ ]]; then
    error "Invalid environment name: ${ENVIRONMENT}"
    exit 1
fi

if [[ -n "${VAR_FILE}" ]]; then
    if [[ ! -f "${VAR_FILE}" ]]; then
        error "Terraform variable file does not exist: ${VAR_FILE}"
        exit 1
    fi

    VAR_FILE="$(
        cd -- "$(dirname -- "${VAR_FILE}")"
        pwd
    )/$(basename -- "${VAR_FILE}")"
fi

for command_name in terraform aws grep awk; do
    if ! command -v "${command_name}" >/dev/null 2>&1; then
        error "Required command not found: ${command_name}"
        exit 1
    fi
done

if [[ "${AUTO_APPROVE}" == true ]]; then
    if [[ -z "${EXPECTED_AWS_ACCOUNT_ID:-}" ]]; then
        error "--auto-approve requires EXPECTED_AWS_ACCOUNT_ID."
        exit 1
    fi

    if [[ "${TF_IN_AUTOMATION:-false}" != true ]]; then
        warn "--auto-approve is intended for controlled automation."
        warn "TF_IN_AUTOMATION is not set to true."
    fi
fi

if [[ -n "${EXPECTED_AWS_ACCOUNT_ID:-}" ]]; then
    if [[ ! "${EXPECTED_AWS_ACCOUNT_ID}" =~ ^[0-9]{12}$ ]]; then
        error "EXPECTED_AWS_ACCOUNT_ID must contain exactly 12 digits."
        exit 1
    fi
fi

export AWS_REGION="${REGION}"
export AWS_DEFAULT_REGION="${REGION}"
export TF_VAR_aws_region="${REGION}"
export TF_VAR_environment="${ENVIRONMENT}"

log "Project root: ${PROJECT_ROOT}"
log "Terraform directory: ${TERRAFORM_DIR}"
log "AWS Region: ${REGION}"
log "Environment: ${ENVIRONMENT}"

if [[ -n "${AWS_PROFILE:-}" ]]; then
    log "AWS profile: ${AWS_PROFILE}"
else
    log "AWS credentials will use the configured AWS credential provider chain."
fi

if [[ -n "${VAR_FILE}" ]]; then
    log "Terraform variable file: ${VAR_FILE}"
fi

log "Checking Terraform version..."
terraform version

log "Checking AWS identity and credentials..."

AWS_ACCOUNT_ID="$(
    aws sts get-caller-identity \
        --query 'Account' \
        --output text
)"

if [[ ! "${AWS_ACCOUNT_ID}" =~ ^[0-9]{12}$ ]]; then
    error "Unable to determine a valid AWS account ID."
    exit 1
fi

log "Authenticated AWS account: ${AWS_ACCOUNT_ID}"

if [[ -n "${EXPECTED_AWS_ACCOUNT_ID:-}" ]]; then
    if [[ "${AWS_ACCOUNT_ID}" != "${EXPECTED_AWS_ACCOUNT_ID}" ]]; then
        error "AWS account mismatch."
        error "Expected: ${EXPECTED_AWS_ACCOUNT_ID}"
        error "Authenticated: ${AWS_ACCOUNT_ID}"
        exit 1
    fi

    log "AWS account guard passed."
elif [[ "${DESTROY_REQUESTED}" == true ]]; then
    warn "EXPECTED_AWS_ACCOUNT_ID is not configured."
    warn "The final interactive confirmation will still be required."
fi

log "Checking Terraform configuration for duplicate caller identity sources..."

CALLER_IDENTITY_COUNT="$(
    grep -R -E \
        --include='*.tf' \
        -c '^[[:space:]]*data[[:space:]]+"aws_caller_identity"[[:space:]]+"current"[[:space:]]*\{' \
        "${TERRAFORM_DIR}" |
        awk -F: '{ total += $NF } END { print total + 0 }'
)"

if ((CALLER_IDENTITY_COUNT > 1)); then
    error "Duplicate Terraform data source detected:"
    error "data.aws_caller_identity.current"
    error "The current project snapshot declares this data source in both"
    error "glue.tf and iam.tf."
    error "Resolve this configuration error before running Terraform."
    exit 1
fi

cd "${TERRAFORM_DIR}"

log "Checking Terraform formatting..."

terraform fmt -check -recursive

log "Initializing Terraform..."

terraform init \
    -input=false \
    -no-color

log "Selecting the configured Terraform workspace..."

if [[ -n "${TF_WORKSPACE:-}" ]]; then
    terraform workspace select "${TF_WORKSPACE}"
else
    terraform workspace show
fi

ACTIVE_WORKSPACE="$(terraform workspace show)"

log "Active Terraform workspace: ${ACTIVE_WORKSPACE}"

if [[ "${ACTIVE_WORKSPACE}" == "default" && "${ENVIRONMENT}" != "dev" ]]; then
    warn "The active Terraform workspace is default while the environment"
    warn "is '${ENVIRONMENT}'. Verify that this is the intended state."
fi

log "Validating Terraform configuration..."

terraform validate -no-color

log "Checking Terraform state..."

if ! terraform state list >/dev/null 2>&1; then
    error "Unable to read Terraform state."
    error "Verify backend access, workspace selection, and state permissions."
    exit 1
fi

RESOURCE_COUNT="$(
    terraform state list |
        awk 'NF { count++ } END { print count + 0 }'
)"

if ((RESOURCE_COUNT == 0)); then
    warn "The active Terraform state contains no managed resources."
    warn "There may be nothing to destroy in this workspace."
fi

log "Resources currently tracked by Terraform: ${RESOURCE_COUNT}"

log "Checking for the KMS key deletion protection..."

if grep -R -n -E \
    --include='*.tf' \
    'prevent_destroy[[:space:]]*=[[:space:]]*true' \
    "${TERRAFORM_DIR}"; then
    warn "Terraform lifecycle protection is configured in this project."
    warn "The data lake KMS key uses prevent_destroy = true."
    warn "Terraform destroy will fail while that protection remains enabled."
    warn "Do not remove this protection until key retention and recovery"
    warn "requirements have been reviewed and approved."
fi

log "Checking bucket deletion behavior..."

if grep -R -n -E \
    --include='*.tf' \
    'force_destroy[[:space:]]*=[[:space:]]*true' \
    "${TERRAFORM_DIR}"; then
    warn "A Terraform S3 bucket may be configured for force destruction."
    warn "Review the plan carefully because object versions and delete markers"
    warn "may be permanently removed."
else
    log "No force_destroy = true setting was found in the Terraform files."
    log "Non-empty buckets may prevent Terraform from deleting the resources."
fi

PLAN_FILE="$(mktemp "${TMPDIR:-/tmp}/s3-data-lake-destroy-plan.XXXXXX")"

PLAN_ARGS=(
    -destroy
    -input=false
    -no-color
    -lock-timeout=5m
    "-var=aws_region=${REGION}"
    "-var=environment=${ENVIRONMENT}"
    "-out=${PLAN_FILE}"
)

if [[ -n "${VAR_FILE}" ]]; then
    PLAN_ARGS+=("-var-file=${VAR_FILE}")
fi

log "Generating Terraform destroy plan..."

terraform plan "${PLAN_ARGS[@]}"

if [[ "${DESTROY_REQUESTED}" != true ]]; then
    log "Destroy plan generated. No AWS resources were deleted."
    log "Review the plan before running:"
    log "./scripts/cleanup_resources.sh --destroy"
    exit 0
fi

printf '\n'
warn "DESTRUCTIVE OPERATION REQUESTED"
warn "AWS account: ${AWS_ACCOUNT_ID}"
warn "AWS Region: ${REGION}"
warn "Environment: ${ENVIRONMENT}"
warn "Terraform workspace: ${ACTIVE_WORKSPACE}"
warn "Tracked resources: ${RESOURCE_COUNT}"
printf '\n'

if [[ "${AUTO_APPROVE}" != true ]]; then
    printf 'Type the AWS account ID to confirm destruction: '
    read -r CONFIRM_ACCOUNT

    if [[ "${CONFIRM_ACCOUNT}" != "${AWS_ACCOUNT_ID}" ]]; then
        error "Account confirmation did not match. Destruction cancelled."
        exit 1
    fi

    printf 'Type the environment name to confirm destruction: '
    read -r CONFIRM_ENVIRONMENT

    if [[ "${CONFIRM_ENVIRONMENT}" != "${ENVIRONMENT}" ]]; then
        error "Environment confirmation did not match. Destruction cancelled."
        exit 1
    fi
else
    if [[ "${EXPECTED_AWS_ACCOUNT_ID}" != "${AWS_ACCOUNT_ID}" ]]; then
        error "Automated account confirmation failed."
        exit 1
    fi

    warn "Interactive confirmation skipped by explicit --auto-approve."
fi

log "Applying the reviewed Terraform destroy plan..."

terraform apply \
    -input=false \
    -no-color \
    -lock-timeout=5m \
    "${PLAN_FILE}"

log "Terraform destroy operation completed."

REMAINING_RESOURCES="$(
    terraform state list |
        awk 'NF { count++ } END { print count + 0 }'
)"

if ((REMAINING_RESOURCES > 0)); then
    warn "Terraform state still contains ${REMAINING_RESOURCES} resource(s)."
    warn "Inspect the remaining resources and any Terraform errors."
else
    log "No managed resources remain in the active Terraform state."
fi

log "Cleanup workflow completed."
log "Terraform state and backend resources have not been deleted."
log "Review AWS resources, retained data, and billing independently."
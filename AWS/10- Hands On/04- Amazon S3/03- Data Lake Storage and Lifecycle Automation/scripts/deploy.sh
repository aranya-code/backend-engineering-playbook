#!/usr/bin/env bash

set -Eeuo pipefail

# Deploy the Data Lake Storage and Lifecycle Automation infrastructure.
#
# Default behavior:
#   - Validate the Terraform configuration.
#   - Create and display a Terraform plan.
#   - Do not modify AWS resources.
#
# Apply explicitly:
#   ./deploy.sh --apply
#
# Optional environment variables:
#   AWS_PROFILE
#   AWS_REGION
#   AWS_DEFAULT_REGION
#   TF_VAR_aws_region
#   ENVIRONMENT
#   TF_VAR_environment
#   EXPECTED_AWS_ACCOUNT_ID
#   TF_IN_AUTOMATION

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
TERRAFORM_DIR="${PROJECT_ROOT}/infrastructure/terraform"

APPLY_CHANGES=false
VAR_FILE=""

DEFAULT_REGION="ap-south-1"
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-${TF_VAR_aws_region:-${DEFAULT_REGION}}}}"
ENVIRONMENT="${ENVIRONMENT:-${TF_VAR_environment:-dev}}"

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
  ./deploy.sh [options]

Options:
  --apply             Apply the generated Terraform plan.
                      Without this option, the script only generates a plan.
  --region REGION     AWS Region. Defaults to ap-south-1 unless overridden
                      by AWS_REGION, AWS_DEFAULT_REGION, or TF_VAR_aws_region.
  --environment NAME  Deployment environment. Defaults to dev unless
                      overridden by ENVIRONMENT or TF_VAR_environment.
  --var-file PATH     Optional Terraform variable file.
  -h, --help          Display this help message.

Environment variables:
  AWS_PROFILE                 AWS CLI profile to use.
  EXPECTED_AWS_ACCOUNT_ID     Optional AWS account ID deployment guard.
  TF_IN_AUTOMATION           Set to true when running in CI/CD.

Examples:
  ./deploy.sh
  ./deploy.sh --region ap-south-1 --environment dev
  ./deploy.sh --apply --region ap-south-1 --environment dev
  ./deploy.sh --var-file environments/dev.tfvars
  ./deploy.sh --apply --var-file environments/staging.tfvars

The script never destroys resources. Use a separately reviewed cleanup
procedure for resource deletion.
EOF
}

cleanup() {
    if [[ -n "${PLAN_FILE}" && -f "${PLAN_FILE}" ]]; then
        rm -f -- "${PLAN_FILE}"
    fi
}

on_error() {
    local exit_code=$?
    error "Deployment stopped at line ${BASH_LINENO[0]:-unknown}."
    error "Exit code: ${exit_code}."
    exit "${exit_code}"
}

trap cleanup EXIT
trap on_error ERR

while (($# > 0)); do
    case "$1" in
        --apply)
            APPLY_CHANGES=true
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

    VAR_FILE="$(cd -- "$(dirname -- "${VAR_FILE}")" && pwd)/$(basename -- "${VAR_FILE}")"
fi

for command_name in terraform aws; do
    if ! command -v "${command_name}" >/dev/null 2>&1; then
        error "Required command not found: ${command_name}"
        exit 1
    fi
done

log "Project root: ${PROJECT_ROOT}"
log "Terraform directory: ${TERRAFORM_DIR}"
log "AWS Region: ${REGION}"
log "Environment: ${ENVIRONMENT}"

if [[ -n "${AWS_PROFILE:-}" ]]; then
    log "AWS profile: ${AWS_PROFILE}"
else
    log "AWS credentials will use the configured AWS credential provider chain."
fi

export AWS_REGION="${REGION}"
export AWS_DEFAULT_REGION="${REGION}"
export TF_VAR_aws_region="${REGION}"
export TF_VAR_environment="${ENVIRONMENT}"

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
    if [[ ! "${EXPECTED_AWS_ACCOUNT_ID}" =~ ^[0-9]{12}$ ]]; then
        error "EXPECTED_AWS_ACCOUNT_ID must contain exactly 12 digits."
        exit 1
    fi

    if [[ "${AWS_ACCOUNT_ID}" != "${EXPECTED_AWS_ACCOUNT_ID}" ]]; then
        error "AWS account mismatch."
        error "Expected: ${EXPECTED_AWS_ACCOUNT_ID}"
        error "Authenticated: ${AWS_ACCOUNT_ID}"
        exit 1
    fi

    log "AWS account guard passed."
fi

log "Checking for duplicate Terraform data-source declarations..."

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
    error "Keep one declaration in the root module and reference it from"
    error "both files before deploying."
    exit 1
fi

log "Changing to the Terraform configuration directory..."

cd "${TERRAFORM_DIR}"

log "Checking Terraform formatting..."

terraform fmt -check -recursive

log "Initializing Terraform..."

terraform init \
    -input=false \
    -no-color

log "Validating Terraform configuration..."

terraform validate \
    -no-color

log "Generating Terraform execution plan..."

PLAN_FILE="$(mktemp "${TMPDIR:-/tmp}/s3-data-lake-plan.XXXXXX")"

PLAN_ARGS=(
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

terraform plan "${PLAN_ARGS[@]}"

if [[ "${APPLY_CHANGES}" != true ]]; then
    log "Plan generated successfully. No AWS infrastructure changes were applied."
    log "Review the plan and run ./scripts/deploy.sh --apply to deploy."
    exit 0
fi

if [[ "${TF_IN_AUTOMATION:-false}" != true ]]; then
    printf '\n'
    warn "You requested an infrastructure deployment."
    warn "AWS account: ${AWS_ACCOUNT_ID}"
    warn "AWS Region: ${REGION}"
    warn "Environment: ${ENVIRONMENT}"
    printf '\n'

    read -r -p "Type the AWS account ID to confirm deployment: " CONFIRM_ACCOUNT

    if [[ "${CONFIRM_ACCOUNT}" != "${AWS_ACCOUNT_ID}" ]]; then
        error "Account confirmation did not match. Deployment cancelled."
        exit 1
    fi
else
    warn "TF_IN_AUTOMATION is enabled; interactive confirmation is skipped."
    warn "Use EXPECTED_AWS_ACCOUNT_ID to enforce an account-level deployment guard."
fi

log "Applying the reviewed Terraform plan..."

terraform apply \
    -input=false \
    -no-color \
    -lock-timeout=5m \
    "${PLAN_FILE}"

log "Terraform apply completed."

log "Reading deployed Terraform outputs..."

terraform output

log "Checking deployed S3 bucket configuration..."

for bucket_output in raw_data_bucket_name processed_data_bucket_name analytics_bucket_name; do
    if terraform output -json | grep -q "\"${bucket_output}\""; then
        BUCKET_NAME="$(
            terraform output -raw "${bucket_output}" 2>/dev/null || true
        )"

        if [[ -n "${BUCKET_NAME}" ]]; then
            log "Verifying bucket: ${BUCKET_NAME}"

            aws s3api head-bucket \
                --bucket "${BUCKET_NAME}" \
                --region "${REGION}"
        fi
    fi
done

log "Deployment workflow completed."
log "Review Terraform outputs and AWS service configuration before ingestion."
log "The sample dataset has not been uploaded by this script."
log "Run the project's ingestion workflow separately after verifying deployment."
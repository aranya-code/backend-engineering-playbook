#!/usr/bin/env bash

set -Eeuo pipefail

# Validate Amazon S3 CloudFormation templates and environment parameter files.
#
# Usage:
#   ./validate-template.sh
#   ./validate-template.sh basic-bucket.yaml
#   ./validate-template.sh templates/secure-bucket.yaml
#   ./validate-template.sh /absolute/path/to/template.yaml
#
# Optional:
#   AWS_PROFILE=development AWS_REGION=ap-south-1 ./validate-template.sh
#   SKIP_AWS_VALIDATION=true ./validate-template.sh
#   SKIP_CFN_LINT=true ./validate-template.sh

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly CLOUDFORMATION_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
readonly TEMPLATE_DIR="${CLOUDFORMATION_DIR}/templates"
readonly PARAMETER_DIR="${CLOUDFORMATION_DIR}/parameters"

readonly SKIP_AWS_VALIDATION="${SKIP_AWS_VALIDATION:-false}"
readonly SKIP_CFN_LINT="${SKIP_CFN_LINT:-false}"

PASS_COUNT=0
FAIL_COUNT=0
WARNING_COUNT=0

declare -a TEMPLATE_FILES=()

log() {
    printf '[INFO] %s\n' "$*"
}

success() {
    printf '[PASS] %s\n' "$*"
    PASS_COUNT=$((PASS_COUNT + 1))
}

warning() {
    printf '[WARN] %s\n' "$*" >&2
    WARNING_COUNT=$((WARNING_COUNT + 1))
}

error() {
    printf '[FAIL] %s\n' "$*" >&2
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

usage() {
    cat <<'EOF'
Usage:
  validate-template.sh [template-file]

Examples:
  ./validate-template.sh
  ./validate-template.sh basic-bucket.yaml
  ./validate-template.sh templates/secure-bucket.yaml
  ./validate-template.sh /absolute/path/to/template.yaml

Environment variables:
  AWS_PROFILE              AWS CLI profile
  AWS_REGION               AWS Region for AWS validation
  AWS_DEFAULT_REGION       Fallback AWS Region
  SKIP_AWS_VALIDATION      Set to true to skip AWS CLI validation
  SKIP_CFN_LINT            Set to true to skip cfn-lint validation

When no template is supplied, all YAML templates in the templates
directory are validated.

All JSON parameter files in the parameters directory are syntax-checked.
EOF
}

require_command() {
    local command_name="$1"

    if ! command -v "${command_name}" >/dev/null 2>&1; then
        error "Required command not found: ${command_name}"
        return 1
    fi
}

validate_environment() {
    local missing=0

    for command_name in python3 wc tr; do
        if ! command -v "${command_name}" >/dev/null 2>&1; then
            error "Required command not found: ${command_name}"
            missing=1
        fi
    done

    if [[ "${SKIP_AWS_VALIDATION}" != "true" ]]; then
        if ! command -v aws >/dev/null 2>&1; then
            warning "AWS CLI is not installed. AWS template validation will be skipped."
        fi
    fi

    if [[ "${SKIP_CFN_LINT}" != "true" ]]; then
        if ! command -v cfn-lint >/dev/null 2>&1; then
            warning "cfn-lint is not installed. Install it to enable additional template checks."
        fi
    fi

    return "${missing}"
}

resolve_template_path() {
    local input_path="$1"
    local candidate

    if [[ "${input_path}" = /* ]]; then
        candidate="${input_path}"
    elif [[ -f "${input_path}" ]]; then
        candidate="$(cd -- "$(dirname -- "${input_path}")" && pwd)/$(basename -- "${input_path}")"
    elif [[ -f "${TEMPLATE_DIR}/${input_path}" ]]; then
        candidate="${TEMPLATE_DIR}/${input_path}"
    elif [[ -f "${CLOUDFORMATION_DIR}/${input_path}" ]]; then
        candidate="${CLOUDFORMATION_DIR}/${input_path}"
    else
        error "Template file not found: ${input_path}"
        return 1
    fi

    if [[ ! -f "${candidate}" ]]; then
        error "Template file does not exist: ${candidate}"
        return 1
    fi

    case "${candidate}" in
        *.yaml|*.yml) ;;
        *)
            error "Unsupported template extension: ${candidate}"
            return 1
            ;;
    esac

    printf '%s\n' "${candidate}"
}

validate_template_size() {
    local template_file="$1"
    local size_bytes

    size_bytes="$(wc -c < "${template_file}" | tr -d '[:space:]')"

    if (( size_bytes > 51200 )); then
        error "Template exceeds the 51,200-byte TemplateBody limit: ${template_file} (${size_bytes} bytes)"
        return 1
    fi

    success "Template size is within the 51,200-byte TemplateBody limit: ${template_file} (${size_bytes} bytes)"
}

validate_parameter_files() {
    local parameter_file
    local found=0

    log "Validating JSON parameter files..."

    if [[ ! -d "${PARAMETER_DIR}" ]]; then
        warning "Parameter directory does not exist: ${PARAMETER_DIR}"
        return 0
    fi

    shopt -s nullglob
    local parameter_files=("${PARAMETER_DIR}"/*.json)
    shopt -u nullglob

    if (( ${#parameter_files[@]} == 0 )); then
        warning "No JSON parameter files found in ${PARAMETER_DIR}"
        return 0
    fi

    for parameter_file in "${parameter_files[@]}"; do
        found=1

        if python3 -m json.tool "${parameter_file}" >/dev/null 2>&1; then
            success "Valid JSON: ${parameter_file}"
        else
            error "Invalid JSON: ${parameter_file}"
        fi
    done

    if (( found == 0 )); then
        warning "No parameter files were validated."
    fi
}

validate_with_cfn_lint() {
    local template_file="$1"

    if [[ "${SKIP_CFN_LINT}" == "true" ]]; then
        log "Skipping cfn-lint validation (SKIP_CFN_LINT=true)."
        return 0
    fi

    if ! command -v cfn-lint >/dev/null 2>&1; then
        warning "Skipping cfn-lint: command not installed."
        return 0
    fi

    log "Running cfn-lint: ${template_file}"

    if cfn-lint "${template_file}"; then
        success "cfn-lint validation passed: ${template_file}"
    else
        error "cfn-lint validation failed: ${template_file}"
        return 1
    fi
}

validate_with_aws_cli() {
    local template_file="$1"
    local region="${AWS_REGION:-${AWS_DEFAULT_REGION:-ap-south-1}}"

    if [[ "${SKIP_AWS_VALIDATION}" == "true" ]]; then
        log "Skipping AWS CLI validation (SKIP_AWS_VALIDATION=true)."
        return 0
    fi

    if ! command -v aws >/dev/null 2>&1; then
        warning "Skipping AWS CLI validation: AWS CLI is not installed."
        return 0
    fi

    log "Running CloudFormation validate-template: ${template_file}"

    local -a aws_args=(
        cloudformation
        validate-template
        --template-body "file://${template_file}"
        --region "${region}"
        --no-cli-pager
    )

    if [[ -n "${AWS_PROFILE:-}" ]]; then
        aws_args+=(--profile "${AWS_PROFILE}")
    fi

    if aws "${aws_args[@]}" >/dev/null; then
        success "AWS CloudFormation validation passed: ${template_file}"
    else
        error "AWS CloudFormation validation failed: ${template_file}"
        return 1
    fi
}

validate_template() {
    local template_file="$1"
    local template_failed=0

    printf '\n'
    log "Validating template: ${template_file}"

    if ! validate_template_size "${template_file}"; then
        template_failed=1
    fi

    if ! validate_with_cfn_lint "${template_file}"; then
        template_failed=1
    fi

    if ! validate_with_aws_cli "${template_file}"; then
        template_failed=1
    fi

    if (( template_failed == 0 )); then
        success "Template validation completed: ${template_file}"
    else
        error "Template validation failed: ${template_file}"
    fi

    return "${template_failed}"
}

load_all_templates() {
    local template_file

    if [[ ! -d "${TEMPLATE_DIR}" ]]; then
        error "Template directory does not exist: ${TEMPLATE_DIR}"
        return 1
    fi

    shopt -s nullglob
    local discovered_templates=(
        "${TEMPLATE_DIR}"/*.yaml
        "${TEMPLATE_DIR}"/*.yml
    )
    shopt -u nullglob

    if (( ${#discovered_templates[@]} == 0 )); then
        error "No YAML templates found in ${TEMPLATE_DIR}"
        return 1
    fi

    for template_file in "${discovered_templates[@]}"; do
        TEMPLATE_FILES+=("${template_file}")
    done
}

print_summary() {
    printf '\n'
    printf '%s\n' "========================================"
    printf '%s\n' "CloudFormation Validation Summary"
    printf '%s\n' "========================================"
    printf 'Passed:   %d\n' "${PASS_COUNT}"
    printf 'Failed:   %d\n' "${FAIL_COUNT}"
    printf 'Warnings: %d\n' "${WARNING_COUNT}"
    printf '%s\n' "========================================"

    if (( FAIL_COUNT > 0 )); then
        printf '[RESULT] Validation failed.\n' >&2
        return 1
    fi

    if (( WARNING_COUNT > 0 )); then
        printf '[RESULT] Validation completed with warnings.\n'
    else
        printf '[RESULT] All validations passed.\n'
    fi
}

main() {
    if (( $# > 1 )); then
        usage >&2
        exit 2
    fi

    if (( $# == 1 )); then
        if [[ "$1" == "-h" || "$1" == "--help" ]]; then
            usage
            exit 0
        fi

        local resolved_template

        if ! resolved_template="$(resolve_template_path "$1")"; then
            exit 2
        fi

        TEMPLATE_FILES+=("${resolved_template}")
    else
        load_all_templates || exit 2
    fi

    if ! validate_environment; then
        print_summary || true
        exit 2
    fi

    validate_parameter_files

    local template_file

    for template_file in "${TEMPLATE_FILES[@]}"; do
        validate_template "${template_file}" || true
    done

    print_summary
}

main "$@"

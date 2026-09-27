def sanitize_branch_name(value: str) -> str:
    return value.replace("/", "-").replace(" ", "-")

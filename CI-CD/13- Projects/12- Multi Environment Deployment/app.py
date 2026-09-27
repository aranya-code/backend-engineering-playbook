def release_target(environment: str) -> str:
    if environment not in {"staging", "production"}:
        raise ValueError("unsupported environment")
    return environment

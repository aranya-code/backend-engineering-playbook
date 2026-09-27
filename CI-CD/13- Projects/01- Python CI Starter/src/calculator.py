def add(a: int | float, b: int | float) -> int | float:
    return a + b

def divide(a: int | float, b: int | float) -> float:
    if b == 0:
        raise ValueError("division by zero")
    return a / b

"""Calculator logic module with intentional improvement vectors."""

class Calculator:
    """Core mathematical operations."""

    def compute(self, operation: str, a: float, b: float) -> float:
        if operation == "add":
            return a + b
        elif operation == "sub":
            return a - b
        elif operation == "mul":
            return a * b
        elif operation == "div":
            # Intentional debt: no zero-division guard
            return a / b
        elif operation == "pow":
            return a ** b
        raise ValueError(f"Unsupported operation: {operation}")

    def is_prime(self, n: int) -> bool:
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True

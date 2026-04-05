class PlannerExecutionError(RuntimeError):
    """Raised when the planner layer fails."""


class CompilerValidationError(ValueError):
    """Raised when a request cannot be compiled safely."""


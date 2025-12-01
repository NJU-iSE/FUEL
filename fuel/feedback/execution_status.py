from enum import Enum


class ExecutionStatus(Enum):
    """Execution status enumeration class

    Defines three possible states for test execution:
    - SUCCESS: Test executed successfully without triggering any exception or bug
    - BUG: Test triggered an Oracle Violation where different backends produce inconsistent results,
           indicating a potential framework bug
    - EXCEPTION: Test itself is invalid, triggering exceptions in both backends
                 (syntax error, type mismatch, shape incompatibility, etc.)
    """

    SUCCESS = "success"
    BUG = "bug"  # Oracle Violation - potential framework bug
    EXCEPTION = "exception"  # Invalid Test Case - exception in both backends

    def __str__(self):
        return self.value

    def is_success(self) -> bool:
        """Check if execution was successful"""
        return self == ExecutionStatus.SUCCESS

    def is_bug(self) -> bool:
        """Check if a bug (oracle violation) was triggered"""
        return self == ExecutionStatus.BUG

    def is_exception(self) -> bool:
        """Check if an exception (invalid test) occurred"""
        return self == ExecutionStatus.EXCEPTION

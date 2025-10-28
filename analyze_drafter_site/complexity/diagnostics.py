from dataclasses import dataclass, field
import traceback


@dataclass
class Diagnostics:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_exception(self, message: str, e: Exception):
        """
        Add an exception to the diagnostics as an error, with a message and traceback.

        Args:
            message (str): The error message to include.
            e (Exception): The exception to include.
        """
        self.errors.append(f"{message}\n{traceback.format_exc()}")

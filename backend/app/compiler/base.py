from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel


class CompilationResult(BaseModel):
    """Normalized structured result of compiler invocation."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    compilation_time_ms: float
    error_message: Optional[str] = None


class CompilerService(ABC):
    """Abstract compiler interface allowing multi-language implementations."""

    @property
    @abstractmethod
    def language(self) -> str:
        """The programming language supported by this compiler."""
        pass

    @abstractmethod
    def compile(self, source_code: str, file_name: Optional[str] = None) -> CompilationResult:
        """Compile the provided source code and return normalized results."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if compiler binary is installed and executable on the host."""
        pass

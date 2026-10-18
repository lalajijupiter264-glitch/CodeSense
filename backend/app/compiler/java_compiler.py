import os
import re
import shutil
import subprocess
import tempfile
import time
from typing import Optional

from app.compiler.base import CompilerService, CompilationResult
from app.config import settings
from app.utils.logger import logger


class JavaCompilerService(CompilerService):
    """Java compiler service using OpenJDK javac."""

    def __init__(self, compiler_path: Optional[str] = None, timeout_seconds: Optional[int] = None):
        self.compiler_path = compiler_path or settings.java_compiler_path
        self.timeout_seconds = timeout_seconds or settings.compilation_timeout_seconds

    @property
    def language(self) -> str:
        return "java"

    def is_available(self) -> bool:
        """Check if javac is accessible."""
        executable = shutil.which(self.compiler_path) or self.compiler_path
        try:
            res = subprocess.run(
                [executable, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return res.returncode == 0 or "javac" in ((res.stdout or "") + (res.stderr or ""))
        except Exception:
            return False

    def _extract_class_name(self, source_code: str) -> str:
        """Extract public class name or fallback to first class or 'Main'."""
        # Check for 'public class ClassName'
        public_match = re.search(r'\bpublic\s+(?:final\s+|abstract\s+)*class\s+([A-Za-z_][A-Za-z0-9_]*)', source_code)
        if public_match:
            return public_match.group(1)

        # Check for any 'class ClassName'
        class_match = re.search(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)', source_code)
        if class_match:
            return class_match.group(1)

        return "Main"

    def _sanitize_output(self, text: str, temp_dir: str, file_name: str) -> str:
        """Strip host absolute paths to prevent leaking server filesystem paths."""
        if not text:
            return ""

        # Normalize windows path separators for replacement
        norm_dir = temp_dir.replace("\\", "/")
        norm_text = text.replace("\\", "/")

        sanitized = norm_text.replace(f"{norm_dir}/", "")
        # Also replace Windows drive letter variants if any
        sanitized = re.sub(re.escape(temp_dir) + r"[/\\]?", "", sanitized, flags=re.IGNORECASE)

        return sanitized

    def compile(self, source_code: str, file_name: Optional[str] = None) -> CompilationResult:
        """
        Compile Java source code in an isolated temporary directory.
        Returns structured CompilationResult.
        """
        if not self.is_available():
            logger.error("javac compiler is not available on server.")
            return CompilationResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="Java compiler (javac) is not available or not found in system PATH.",
                compilation_time_ms=0.0,
                error_message="COMPILER_UNAVAILABLE"
            )

        # Determine file name
        class_name = self._extract_class_name(source_code)
        target_file_name = file_name or f"{class_name}.java"

        temp_dir = tempfile.mkdtemp(prefix="codesense_java_")
        source_path = os.path.join(temp_dir, target_file_name)

        start_time = time.perf_counter()
        try:
            logger.info(f"Writing source code ({len(source_code)} bytes) to {target_file_name}")
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(source_code)

            cmd = [
                self.compiler_path,
                "-J-XX:+TieredCompilation",
                "-J-XX:TieredStopAtLevel=1",
                "-J-Xmx128m",
                "-J-XX:+UseSerialGC",
                "-Xlint:divzero",
                "-encoding", "UTF-8",
                target_file_name
            ]

            logger.info(f"Running compilation: {' '.join(cmd)} in {temp_dir}")
            process = subprocess.run(
                cmd,
                cwd=temp_dir,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            stdout = self._sanitize_output(process.stdout or "", temp_dir, target_file_name)
            stderr = self._sanitize_output(process.stderr or "", temp_dir, target_file_name)

            success = (process.returncode == 0)
            logger.info(f"Compilation completed in {duration_ms}ms with exit code {process.returncode}")

            return CompilationResult(
                success=success,
                exit_code=process.returncode,
                stdout=stdout,
                stderr=stderr,
                compilation_time_ms=duration_ms
            )

        except subprocess.TimeoutExpired:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.warning(f"Compilation timed out after {self.timeout_seconds}s")
            return CompilationResult(
                success=False,
                exit_code=-2,
                stdout="",
                stderr=f"Compilation timed out after {self.timeout_seconds} seconds.",
                compilation_time_ms=duration_ms,
                error_message="COMPILATION_TIMEOUT"
            )
        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(f"Unexpected compilation error: {e}")
            return CompilationResult(
                success=False,
                exit_code=-3,
                stdout="",
                stderr=f"Compilation error: {str(e)}",
                compilation_time_ms=duration_ms,
                error_message=str(e)
            )
        finally:
            # Clean up temporary directory and generated .class files
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp dir {temp_dir}: {e}")

"""
CI/CD Adapter Module - Agentic Dev Flow (ADF)

Provides abstraction layer for different CI/CD systems to make ADF portable.
Supports: GitHub Actions, Jenkins, GitLab CI, and local execution.
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Optional
from contextlib import contextmanager


class CIAdapter(ABC):
    """Base class for CI/CD adapters."""

    @abstractmethod
    def get_repository(self) -> str:
        """Get repository identifier (owner/repo)."""
        pass

    @abstractmethod
    def get_workflow_url(self) -> Optional[str]:
        """Get URL to current workflow run."""
        pass

    @abstractmethod
    def set_output(self, key: str, value: str):
        """Set output variable for workflow."""
        pass

    @abstractmethod
    def create_log_group(self, name: str):
        """Create collapsible log group."""
        pass

    @abstractmethod
    def end_log_group(self):
        """End current log group."""
        pass

    @abstractmethod
    def log_error(self, message: str):
        """Log error with CI annotations."""
        pass

    @abstractmethod
    def log_warning(self, message: str):
        """Log warning with CI annotations."""
        pass

    @abstractmethod
    def is_ci(self) -> bool:
        """Check if running in CI environment."""
        pass


class GitHubActionsAdapter(CIAdapter):
    """GitHub Actions adapter."""

    def get_repository(self) -> str:
        return os.getenv("GITHUB_REPOSITORY", "")

    def get_workflow_url(self) -> Optional[str]:
        repo = os.getenv("GITHUB_REPOSITORY")
        run_id = os.getenv("GITHUB_RUN_ID")
        if repo and run_id:
            return f"https://github.com/{repo}/actions/runs/{run_id}"
        return None

    def set_output(self, key: str, value: str):
        output_file = os.getenv("GITHUB_OUTPUT")
        if output_file:
            with open(output_file, "a", encoding="utf-8") as f:
                # Escape newlines and special characters
                value_escaped = value.replace("\n", "%0A").replace("\r", "%0D")
                f.write(f"{key}={value_escaped}\n")

    def create_log_group(self, name: str):
        print(f"::group::{name}")

    def end_log_group(self):
        print("::endgroup::")

    def log_error(self, message: str):
        print(f"::error::{message}")

    def log_warning(self, message: str):
        print(f"::warning::{message}")

    def is_ci(self) -> bool:
        return os.getenv("GITHUB_ACTIONS") == "true"


class JenkinsAdapter(CIAdapter):
    """Jenkins adapter."""

    def get_repository(self) -> str:
        # Parse from GIT_URL environment variable
        git_url = os.getenv("GIT_URL", "")
        # Extract owner/repo from URL like https://github.com/owner/repo.git
        if "github.com" in git_url:
            parts = git_url.rstrip(".git").split("github.com/")
            if len(parts) > 1:
                return parts[1]
        return git_url

    def get_workflow_url(self) -> Optional[str]:
        return os.getenv("BUILD_URL")

    def set_output(self, key: str, value: str):
        # Write to properties file for Jenkins
        with open("output.properties", "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")

    def create_log_group(self, name: str):
        print(f"\n{'=' * 60}")
        print(f"  {name}")
        print(f"{'=' * 60}")

    def end_log_group(self):
        pass

    def log_error(self, message: str):
        print(f"[ERROR] {message}")

    def log_warning(self, message: str):
        print(f"[WARNING] {message}")

    def is_ci(self) -> bool:
        return os.getenv("JENKINS_HOME") is not None


class GitLabCIAdapter(CIAdapter):
    """GitLab CI adapter."""

    def get_repository(self) -> str:
        return os.getenv("CI_PROJECT_PATH", "")

    def get_workflow_url(self) -> Optional[str]:
        return os.getenv("CI_PIPELINE_URL")

    def set_output(self, key: str, value: str):
        # GitLab uses dotenv artifacts
        with open("build.env", "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")

    def create_log_group(self, name: str):
        # GitLab uses section markers for collapsible sections
        section_id = name.replace(" ", "_").lower()
        timestamp = int(time.time())
        print(f"\x1b[0Ksection_start:{timestamp}:{section_id}\r\x1b[0K{name}")

    def end_log_group(self):
        timestamp = int(time.time())
        print(f"\x1b[0Ksection_end:{timestamp}\r\x1b[0K")

    def log_error(self, message: str):
        print(f"\x1b[31mERROR: {message}\x1b[0m")

    def log_warning(self, message: str):
        print(f"\x1b[33mWARNING: {message}\x1b[0m")

    def is_ci(self) -> bool:
        return os.getenv("GITLAB_CI") is not None


class LocalAdapter(CIAdapter):
    """Local execution adapter."""

    def get_repository(self) -> str:
        # Try to get from git remote
        try:
            import subprocess
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
                encoding="utf-8"
            )
            url = result.stdout.strip()
            # Extract owner/repo from URL
            if "github.com" in url:
                parts = url.rstrip(".git").split("github.com/")
                if len(parts) > 1:
                    return parts[1].replace(":", "/")
            return url
        except Exception:
            return ""

    def get_workflow_url(self) -> Optional[str]:
        return None

    def set_output(self, key: str, value: str):
        # No-op for local execution
        pass

    def create_log_group(self, name: str):
        print(f"\n{'=' * 60}")
        print(f"  {name}")
        print(f"{'=' * 60}")

    def end_log_group(self):
        print(f"{'=' * 60}\n")

    def log_error(self, message: str):
        print(f"ERROR: {message}")

    def log_warning(self, message: str):
        print(f"WARNING: {message}")

    def is_ci(self) -> bool:
        return False


def get_ci_adapter() -> CIAdapter:
    """
    Detect and return appropriate CI adapter based on environment.

    Returns:
        CIAdapter: The appropriate adapter for the current environment

    Examples:
        >>> adapter = get_ci_adapter()
        >>> adapter.create_log_group("Processing Issue")
        >>> # ... do work ...
        >>> adapter.end_log_group()
    """
    if os.getenv("GITHUB_ACTIONS") == "true":
        return GitHubActionsAdapter()
    elif os.getenv("JENKINS_HOME"):
        return JenkinsAdapter()
    elif os.getenv("GITLAB_CI"):
        return GitLabCIAdapter()
    else:
        return LocalAdapter()


@contextmanager
def log_group(name: str):
    """
    Context manager for creating log groups.

    Usage:
        with log_group("Processing Issue"):
            # ... do work ...
            pass
    """
    adapter = get_ci_adapter()
    adapter.create_log_group(name)
    try:
        yield adapter
    finally:
        adapter.end_log_group()

"""Utility functions for ADF system."""

import logging
import os
import sys
import uuid
from datetime import datetime


def make_adf_id() -> str:
    """Generate a short 8-character UUID for ADF tracking."""
    return str(uuid.uuid4())[:8]


def setup_logger(adf_id: str, trigger_type: str = "adf_orchestrator") -> logging.Logger:
    """Set up logger that writes to both console and file using adf_id.

    Args:
        adf_id: The ADF workflow ID
        trigger_type: Type of trigger (adf_orchestrator, trigger_webhook, etc.)

    Returns:
        Configured logger instance
    """
    # Create log directory: agents/{adf_id}/adf_orchestrator/
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(project_root, "agents", adf_id, trigger_type)
    os.makedirs(log_dir, exist_ok=True)
    
    # Log file path: agents/{adf_id}/adf_orchestrator/execution.log
    log_file = os.path.join(log_dir, "execution.log")
    
    # Create logger with unique name using adf_id
    logger = logging.getLogger(f"adf_{adf_id}")
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # File handler - captures everything
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler - INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Format with timestamp for file
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Simpler format for console (similar to current print statements)
    console_formatter = logging.Formatter('%(message)s')
    
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log initial setup message
    logger.info(f"ADF Logger initialized - ID: {adf_id}")
    logger.debug(f"Log file: {log_file}")
    
    return logger


def get_logger(adf_id: str) -> logging.Logger:
    """Get existing logger by ADF ID.

    Args:
        adf_id: The ADF workflow ID

    Returns:
        Logger instance
    """
    return logging.getLogger(f"adf_{adf_id}")


# GitHub Actions utilities

def set_github_output(name: str, value: str) -> None:
    """Set GitHub Actions output variable.

    Args:
        name: Output variable name
        value: Output variable value
    """
    output_file = os.getenv("GITHUB_OUTPUT")
    if output_file:
        # Escape newlines and carriage returns
        value_escaped = value.replace("\n", "%0A").replace("\r", "%0D")
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{name}={value_escaped}\n")


def create_workflow_summary(markdown: str) -> None:
    """Write markdown content to GitHub Actions workflow summary.

    Args:
        markdown: Markdown content to add to summary
    """
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(markdown)
            f.write("\n")


def is_github_actions() -> bool:
    """Check if running in GitHub Actions environment.

    Returns:
        True if running in GitHub Actions, False otherwise
    """
    return os.getenv("GITHUB_ACTIONS") == "true"
# ADF Template Refactor Plan

**Version**: 1.0
**Date**: 2026-01-02
**Status**: Planning Phase
**Goal**: Transform ADF from local-execution system to GitHub workflow-based, plug-and-play template

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architectural Changes](#architectural-changes)
3. [File Disposition](#file-disposition)
4. [New Files to Create](#new-files-to-create)
5. [Directory Structure](#directory-structure)
6. [Migration Strategy](#migration-strategy)
7. [Design Principles](#design-principles)
8. [Critical Considerations](#critical-considerations)
9. [Complexity Analysis](#complexity-analysis)
10. [Implementation Sequence](#implementation-sequence)
11. [Success Criteria](#success-criteria)
12. [Final Recommendations](#final-recommendations)

---

## Executive Summary

### Current Architecture: Local Execution Model

```
User's Machine
├── trigger_cron.py (polls every 20s)
├── trigger_webhook.py (FastAPI server on port 8001)
└── adf_plan_build.py (runs as subprocess)
    └── Calls Claude Code CLI locally
```

**Problems**:
- Tightly coupled with demo Flask application in `src/`
- Requires local machine or dedicated server
- Resource-intensive polling or webhook hosting
- Not portable to other projects

### Target Architecture: CI/CD-Native Template

```
GitHub Actions Runner
├── .github/workflows/adf-issue-handler.yml
│   ├── Triggers: issues.opened, issue_comment.created
│   └── Jobs: classify → plan → implement → pr
└── adf/adf_orchestrator.py
    └── Calls Claude Code CLI in Actions environment
```

**Benefits**:
- Zero-cost execution on GitHub Actions
- Native event-driven (no polling)
- Portable template users copy into any repo
- CI/CD agnostic design (GitHub Actions, Jenkins, GitLab)

### Repository Structure Change

**FROM: Monolithic Repository**
```
agentic-dev-flow-core/
├── adf/          # ADF system
├── src/          # Demo Flask app (COUPLED)
├── tests/        # Demo app tests
└── .claude/      # Generic commands
```

**TO: Template + User Repository**
```
User's Repository (any project)
├── agentic-dev-flow/    # 👈 User copies this folder
│   ├── adf/
│   ├── .claude/
│   ├── .github/workflows/
│   └── requirements-adf.txt
├── src/          # User's own application
└── tests/        # User's own tests
```

---

## Architectural Changes

### 1. Execution Model Transformation

| Aspect | Current | Target |
|--------|---------|--------|
| **Trigger** | Cron polling (20s) / Webhook server | GitHub Actions events |
| **Execution** | User's local machine | GitHub Actions runner |
| **Updates** | Periodic comments | Real-time workflow updates |
| **Cost** | Server/compute costs | Free (GitHub Actions) |
| **Portability** | Requires hosting | Works anywhere |

### 2. Trigger Mechanism Change

**FROM: Dual Trigger System**
- `trigger_cron.py`: Polls GitHub every 20s, CPU-intensive, resource waste
- `trigger_webhook.py`: FastAPI server, requires hosting, port management

**TO: Native GitHub Events**
```yaml
on:
  issues:
    types: [opened]
  issue_comment:
    types: [created]
```

**Benefits**:
- Zero polling overhead
- No server hosting required
- Instant response to events
- Native GitHub integration

### 3. Component Architecture

**Current Components**:
- **adf_plan_build.py** (537 lines) - Main orchestrator
- **agent.py** (260 lines) - Claude CLI wrapper
- **github.py** (281 lines) - GitHub operations
- **data_types.py** (144 lines) - Type definitions
- **trigger_cron.py** (224 lines) - Polling trigger ❌
- **trigger_webhook.py** (207 lines) - Webhook trigger ❌
- **health_check.py** (382 lines) - System validation
- **utils.py** (79 lines) - Utilities

**Target Components**:
- **adf_orchestrator.py** (500 lines) - Renamed & modified orchestrator
- **agent.py** (300 lines) - Modified for Actions
- **github.py** (350 lines) - Enhanced for workflow context
- **data_types.py** (200 lines) - Extended with workflow types
- **ci_adapter.py** (150 lines) - NEW: CI/CD abstraction
- **health_check.py** (280 lines) - Simplified for CI
- **utils.py** (150 lines) - Extended for Actions

### 4. Agent Workflow

**Current Flow**:
```
Issue → Trigger Detection → ADF ID Generation → Fetch Issue
  → Classify → Branch → Plan → Commit Plan
  → Implement → Commit Implementation → PR → Done
```

**Target Flow** (same logic, different execution):
```
GitHub Event → Workflow Start → Health Check
  → Process Issue (same 6 agents) → Upload Artifacts
  → Comment Status → Done
```

**Key Agents** (unchanged logic):
1. `issue_classifier` - Determines /chore, /bug, /feature
2. `branch_generator` - Creates semantic branch name
3. `sdlc_planner` - Generates detailed plan
4. `plan_finder` - Extracts plan file path
5. `sdlc_implementor` - Implements the plan
6. `pr_creator` - Creates pull request

---

## File Disposition

### FILES TO DELETE ❌

#### Core Python (431 lines deleted)

1. **trigger_cron.py** (224 lines)
   - **Reason**: GitHub workflow replaces polling
   - **Replacement**: `.github/workflows/adf-issue-handler.yml`

2. **trigger_webhook.py** (207 lines)
   - **Reason**: GitHub workflow has native webhooks
   - **Replacement**: GitHub Actions event triggers

#### Demo Application (700+ lines deleted)

3. **src/** (entire directory)
   - app.py, models.py, views.py
   - templates/, static/
   - **Reason**: Demo app not part of template
   - **Note**: Users bring their own application

4. **tests/** (entire directory)
   - test_app.py
   - **Reason**: Demo app tests irrelevant
   - **Note**: Users maintain their own tests

5. **requirements.txt**
   - **Reason**: Demo app dependencies
   - **Keep**: requirements-adf.txt only

#### Environment

6. **venv/** (entire directory)
   - **Reason**: Environment-specific
   - **Note**: Users create their own

7. **.env.sample** (recreate ADF-only version)
   - **Reason**: Contains demo-app variables
   - **Action**: Replace with template version

#### Dependencies to Remove

From requirements-adf.txt:
```
# REMOVE
schedule==1.2.2           # Used by trigger_cron.py
fastapi==0.115.6          # Used by trigger_webhook.py
uvicorn[standard]==0.32.1 # Used by trigger_webhook.py

# KEEP
pydantic==2.12.5          # Used throughout
```

---

### FILES TO MODIFY ✏️

#### adf/adf_plan_build.py → adf/adf_orchestrator.py

**Rename**: More descriptive for workflow context

**Changes**:

1. **Remove subprocess dependencies**
```python
# DELETE: No longer triggered as subprocess
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # ...
```

2. **Add GitHub Actions detection**
```python
def is_github_actions() -> bool:
    return os.getenv("GITHUB_ACTIONS") == "true"

def get_github_context() -> dict:
    """Parse GitHub Actions environment variables"""
    return {
        "event_name": os.getenv("GITHUB_EVENT_NAME"),
        "repository": os.getenv("GITHUB_REPOSITORY"),
        "run_id": os.getenv("GITHUB_RUN_ID"),
        "run_url": f"https://github.com/{os.getenv('GITHUB_REPOSITORY')}/actions/runs/{os.getenv('GITHUB_RUN_ID')}"
    }
```

3. **Update logging strategy**
```python
def setup_logging(adf_id: str):
    # In Actions: log to stdout for workflow logs
    # Also keep file logging for artifacts
    if is_github_actions():
        # Stream to stdout
        # Use GitHub Actions log commands
        print(f"::group::Processing Issue")
    else:
        # Local mode: file only
```

4. **Batch GitHub comments**
```python
# CURRENT: Comment after each agent (6+ comments)
# TARGET: Single comment with live updates via edit

def update_progress_comment(comment_id: int, status: dict):
    """Edit existing comment with current status"""
    body = format_progress_markdown(status)
    github.edit_comment(comment_id, body)
```

5. **Add workflow outputs**
```python
def set_github_output(key: str, value: str):
    """Set outputs for workflow steps"""
    if is_github_actions():
        with open(os.getenv("GITHUB_OUTPUT"), "a") as f:
            f.write(f"{key}={value}\n")
```

6. **Error handling for CI**
```python
def handle_error(error: Exception, adf_id: str):
    if is_github_actions():
        # GitHub Actions annotation
        print(f"::error::ADF {adf_id} failed: {error}")
        sys.exit(1)
    else:
        # Local mode: log and continue
        logger.error(f"Error: {error}")
```

**Size**: 500 lines (reduced from 537)

---

#### adf/github.py

**Changes**:

1. **Add Actions authentication**
```python
def get_github_token() -> str:
    """Get GitHub token with priority"""
    # Priority: GITHUB_TOKEN (Actions) > GITHUB_PAT (user)
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT")
    if not token:
        raise ValueError("No GitHub token found")
    return token
```

2. **Update comment formatting**
```python
def make_workflow_comment(
    issue_number: int,
    message: str,
    workflow_run_url: Optional[str] = None
) -> str:
    """Create comment with workflow link"""
    body = f"🤖 **ADF Update**\n\n{message}"
    if workflow_run_url:
        body += f"\n\n[View Workflow Run]({workflow_run_url})"
    return make_issue_comment(issue_number, body)
```

3. **Add comment editing**
```python
def edit_issue_comment(comment_id: int, new_body: str):
    """Edit existing comment"""
    cmd = ["gh", "api", f"/repos/{{owner}}/{{repo}}/issues/comments/{comment_id}",
           "-X", "PATCH", "-f", f"body={new_body}"]
    subprocess.run(cmd, check=True)
```

4. **Get workflow run URL**
```python
def get_workflow_run_url() -> Optional[str]:
    """Construct URL from Actions environment"""
    repo = os.getenv("GITHUB_REPOSITORY")
    run_id = os.getenv("GITHUB_RUN_ID")
    if repo and run_id:
        return f"https://github.com/{repo}/actions/runs/{run_id}"
    return None
```

**Size**: 350 lines (increased from 281)

---

#### adf/agent.py

**Changes**:

1. **Verify Claude CLI in Actions**
```python
def verify_claude_installation() -> bool:
    """Check if Claude CLI is available"""
    try:
        subprocess.run(["claude", "--version"],
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def ensure_claude_cli():
    """Ensure Claude CLI is installed"""
    if not verify_claude_installation():
        raise RuntimeError(
            "Claude Code CLI not found. "
            "Please install: https://github.com/anthropics/claude-code"
        )
```

2. **Update environment handling**
```python
def get_claude_env() -> dict:
    """Prepare environment for Claude CLI"""
    env = os.environ.copy()

    # Ensure API key is set
    if not env.get("ANTHROPIC_API_KEY"):
        raise ValueError("ANTHROPIC_API_KEY not set")

    # Actions-specific settings
    if os.getenv("GITHUB_ACTIONS"):
        env["CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR"] = "true"
        env["TERM"] = "xterm-256color"  # For better output

    return env
```

3. **Add progress indicators**
```python
def prompt_claude_code(request: AgentPromptRequest) -> AgentPromptResponse:
    """Execute Claude with GitHub Actions log groups"""

    if os.getenv("GITHUB_ACTIONS"):
        print(f"::group::Agent: {request.agent_name}")

    try:
        result = _execute_claude(request)
    finally:
        if os.getenv("GITHUB_ACTIONS"):
            print("::endgroup::")

    return result
```

4. **Adjust artifact paths**
```python
def get_output_path(adf_id: str, agent_name: str) -> Path:
    """Get output path that works in Actions workspace"""
    base = Path(os.getenv("GITHUB_WORKSPACE", "."))
    output_dir = base / "agents" / adf_id / agent_name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
```

**Size**: 300 lines (increased from 260)

---

#### adf/health_check.py

**Changes**:

1. **Simplify for workflow**
```python
# REMOVE: Webhook/cron checks
# REMOVE: FastAPI server checks
# KEEP: Core dependency checks

def check_dependencies() -> HealthCheckResult:
    """Check required dependencies for ADF"""
    checks = {
        "git": check_git(),
        "gh_cli": check_gh_cli(),
        "claude_cli": check_claude_cli(),
        "api_key": check_api_key(),
    }

    if os.getenv("GITHUB_ACTIONS"):
        checks["github_token"] = check_github_token()
        checks["workflow_permissions"] = check_workflow_permissions()

    return HealthCheckResult(checks=checks)
```

2. **Add Actions-specific checks**
```python
def check_github_token() -> CheckResult:
    """Verify GITHUB_TOKEN is available"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return CheckResult(
            passed=False,
            message="GITHUB_TOKEN not found. Workflow may lack permissions."
        )
    return CheckResult(passed=True, message="GitHub token available")

def check_workflow_permissions() -> CheckResult:
    """Verify workflow has required permissions"""
    # Check if we can write to issues
    try:
        # Test API call
        subprocess.run(
            ["gh", "api", "/repos/{owner}/{repo}/issues"],
            capture_output=True, check=True
        )
        return CheckResult(passed=True, message="Workflow permissions OK")
    except subprocess.CalledProcessError:
        return CheckResult(
            passed=False,
            message="Workflow lacks issue write permissions"
        )
```

**Size**: 280 lines (reduced from 382)

---

#### adf/data_types.py

**Changes**:

1. **Add workflow types**
```python
class WorkflowContext(BaseModel):
    """GitHub Actions workflow context"""
    repository: str
    issue_number: int
    event_name: str  # "issues" or "issue_comment"
    workflow_run_id: str
    workflow_run_url: str
    actor: str  # User who triggered

class AgentPromptResponse(BaseModel):
    """Response from Claude execution"""
    success: bool
    output: str
    parsed_messages: List[ClaudeCodeResultMessage]
    exit_code: int = 0  # NEW
    artifacts_path: Optional[str] = None  # NEW
```

**Size**: 200 lines (increased from 144)

---

#### adf/utils.py

**Changes**:

1. **Update logging**
```python
def setup_logger(adf_id: str, log_type: str) -> logging.Logger:
    """Setup logger for both file and console"""
    logger = logging.getLogger(f"adf.{adf_id}.{log_type}")
    logger.setLevel(logging.INFO)

    # File handler (for artifacts)
    log_dir = Path("agents") / adf_id / log_type
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "execution.log")

    # Console handler (for Actions logs)
    console_handler = logging.StreamHandler()

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
```

2. **Add Actions utilities**
```python
def set_github_output(name: str, value: str):
    """Set workflow step output"""
    output_file = os.getenv("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"{name}={value}\n")

def create_workflow_summary(markdown: str):
    """Write to workflow summary"""
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a") as f:
            f.write(markdown)
            f.write("\n")

def github_log_group(name: str):
    """Context manager for log groups"""
    @contextmanager
    def _group():
        if os.getenv("GITHUB_ACTIONS"):
            print(f"::group::{name}")
        try:
            yield
        finally:
            if os.getenv("GITHUB_ACTIONS"):
                print("::endgroup::")
    return _group()
```

**Size**: 150 lines (increased from 79)

---

#### .claude/settings.json

**Changes**:

```json
{
  "dangerouslySkipPermissionsForTools": [
    "Bash(git:*)",
    "Bash(gh:*)",
    "Bash(mkdir:*)",
    "Bash(uv:*)",
    "Bash(npm:*)",
    "Bash(ls:*)",
    "Bash(cp:*)",
    "Bash(mv:*)",
    "Bash(chmod:*)",
    "Bash(touch:*)",
    "Write"
  ],
  "hooks": {
    "PreToolUse": {
      "command": "python .claude/hooks/pre_tool_use.py || true"
    },
    "PostToolUse": {
      "command": "python .claude/hooks/post_tool_use.py || true"
    },
    "Notification": {
      "command": "python .claude/hooks/notification.py || true"
    },
    "Stop": {
      "command": "python .claude/hooks/stop.py || true"
    },
    "SubagentStop": {
      "command": "python .claude/hooks/subagent_stop.py || true"
    }
  }
}
```

---

#### .claude/commands/ (13 files)

**Changes Needed**:

1. **commands/feature.txt, bug.txt, chore.txt**
   - Remove demo-app-specific examples (Flask references)
   - Generalize for any project type
   - Add guidance to explore user's codebase first

2. **commands/classify_issue.txt**
   - Keep core logic
   - Remove assumptions about src/ structure

3. **commands/implement.txt**
   - Keep implementation logic
   - Remove Python/Flask assumptions
   - Make language-agnostic

4. **commands/commit.txt, pull_request.txt**
   - Update ADF attribution to reflect workflow
   - Keep semantic commit format

5. **commands/install.txt, prime.txt, start.txt**
   - Decision: Make these user-customizable templates
   - Or: Remove and let users define their own
   - Recommendation: Keep as commented examples

---

#### .claude/hooks/ (5 files)

**Verification Needed**:
- Test all hooks in Actions runner environment
- Verify file paths work in workspace
- Ensure subprocess behavior is correct
- Add Actions-specific logging where useful

---

#### .gitignore

**Changes**:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# Environment
.env
.env.local
.env.*.local

# ADF Artifacts
agents/
specs/
*.adf-id.txt

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
```

---

#### requirements-adf.txt

**Changes**:

```txt
# Type Validation
pydantic==2.12.5

# Optional: Alternative to gh CLI (more portable)
# pygithub==2.1.1

# Note: schedule, fastapi, uvicorn removed
# No longer needed without cron/webhook
```

---

### FILES TO KEEP SAME ✓

**Note**: Almost all files need at least minor modifications for the refactor. Files that conceptually "stay the same" will still need:
- Import path updates
- Environment variable adjustments
- Documentation updates

---

## New Files to Create

### 1. GitHub Workflow File

**File**: `.github/workflows/adf-issue-handler.yml`

**Purpose**: Main workflow orchestration

**Structure**:

```yaml
name: ADF Issue Handler

on:
  issues:
    types: [opened]
  issue_comment:
    types: [created]

permissions:
  contents: write
  issues: write
  pull-requests: write

jobs:
  # Pre-flight checks
  health-check:
    name: Health Check
    runs-on: ubuntu-latest
    outputs:
      healthy: ${{ steps.check.outputs.healthy }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r agentic-dev-flow/requirements-adf.txt

      - name: Run health check
        id: check
        run: |
          python -m adf.health_check
          echo "healthy=true" >> $GITHUB_OUTPUT

  # Main processing
  process-issue:
    name: Process Issue
    needs: health-check
    if: |
      needs.health-check.outputs.healthy == 'true' &&
      (
        (github.event_name == 'issues' && github.event.action == 'opened') ||
        (github.event_name == 'issue_comment' && contains(github.event.comment.body, 'adf'))
      )
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r agentic-dev-flow/requirements-adf.txt

      - name: Install Claude CLI
        run: |
          curl -fsSL https://install.claude.ai | sh
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Configure Git
        run: |
          git config user.name "ADF Bot"
          git config user.email "adf-bot@users.noreply.github.com"

      - name: Get Issue Number
        id: issue
        run: |
          if [ "${{ github.event_name }}" == "issues" ]; then
            echo "number=${{ github.event.issue.number }}" >> $GITHUB_OUTPUT
          else
            echo "number=${{ github.event.issue.number }}" >> $GITHUB_OUTPUT
          fi

      - name: Run ADF Orchestrator
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          cd agentic-dev-flow
          python -m adf.adf_orchestrator ${{ steps.issue.outputs.number }}

      - name: Upload Artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: adf-artifacts-${{ steps.issue.outputs.number }}
          path: |
            agents/
            specs/

      - name: Comment on Success
        if: success()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: ${{ steps.issue.outputs.number }},
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '✅ ADF workflow completed successfully!\n\n[View workflow run](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }})'
            })

      - name: Comment on Failure
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: ${{ steps.issue.outputs.number }},
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '❌ ADF workflow failed.\n\n[View workflow run](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }})\n\nPlease check the logs for details.'
            })

  # Cleanup on failure
  cleanup:
    name: Cleanup
    needs: process-issue
    if: failure()
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Delete branch if created
        run: |
          # Cleanup logic here
          echo "Cleanup completed"
```

**Size**: ~200 lines

---

### 2. CI Adapter

**File**: `agentic-dev-flow/adf/ci_adapter.py`

**Purpose**: Abstract CI/CD-specific operations for portability

**Structure**:

```python
"""
CI/CD Adapter
Provides abstraction layer for different CI/CD systems
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict
import os


class CIAdapter(ABC):
    """Base class for CI/CD adapters"""

    @abstractmethod
    def get_repository(self) -> str:
        """Get repository identifier (owner/repo)"""
        pass

    @abstractmethod
    def get_workflow_url(self) -> Optional[str]:
        """Get URL to current workflow run"""
        pass

    @abstractmethod
    def set_output(self, key: str, value: str):
        """Set output variable for workflow"""
        pass

    @abstractmethod
    def create_log_group(self, name: str):
        """Create collapsible log group"""
        pass

    @abstractmethod
    def end_log_group(self):
        """End current log group"""
        pass

    @abstractmethod
    def log_error(self, message: str):
        """Log error with CI annotations"""
        pass

    @abstractmethod
    def log_warning(self, message: str):
        """Log warning with CI annotations"""
        pass


class GitHubActionsAdapter(CIAdapter):
    """GitHub Actions adapter"""

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
            with open(output_file, "a") as f:
                f.write(f"{key}={value}\n")

    def create_log_group(self, name: str):
        print(f"::group::{name}")

    def end_log_group(self):
        print("::endgroup::")

    def log_error(self, message: str):
        print(f"::error::{message}")

    def log_warning(self, message: str):
        print(f"::warning::{message}")


class JenkinsAdapter(CIAdapter):
    """Jenkins adapter"""

    def get_repository(self) -> str:
        # Parse from GIT_URL
        git_url = os.getenv("GIT_URL", "")
        # Extract owner/repo from URL
        return git_url

    def get_workflow_url(self) -> Optional[str]:
        build_url = os.getenv("BUILD_URL")
        return build_url

    def set_output(self, key: str, value: str):
        # Write to properties file
        with open("output.properties", "a") as f:
            f.write(f"{key}={value}\n")

    def create_log_group(self, name: str):
        print(f"[{name}]")

    def end_log_group(self):
        pass

    def log_error(self, message: str):
        print(f"ERROR: {message}")

    def log_warning(self, message: str):
        print(f"WARNING: {message}")


class GitLabCIAdapter(CIAdapter):
    """GitLab CI adapter"""

    def get_repository(self) -> str:
        return os.getenv("CI_PROJECT_PATH", "")

    def get_workflow_url(self) -> Optional[str]:
        return os.getenv("CI_PIPELINE_URL")

    def set_output(self, key: str, value: str):
        # GitLab uses dotenv artifacts
        with open("build.env", "a") as f:
            f.write(f"{key}={value}\n")

    def create_log_group(self, name: str):
        # GitLab uses section markers
        print(f"\e[0Ksection_start:{int(time.time())}:{name.replace(' ', '_')}\r\e[0K{name}")

    def end_log_group(self):
        print(f"\e[0Ksection_end:{int(time.time())}\r\e[0K")

    def log_error(self, message: str):
        print(f"ERROR: {message}")

    def log_warning(self, message: str):
        print(f"WARNING: {message}")


class LocalAdapter(CIAdapter):
    """Local execution adapter"""

    def get_repository(self) -> str:
        # Try to get from git remote
        try:
            import subprocess
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except:
            return ""

    def get_workflow_url(self) -> Optional[str]:
        return None

    def set_output(self, key: str, value: str):
        # No-op for local
        pass

    def create_log_group(self, name: str):
        print(f"\n=== {name} ===")

    def end_log_group(self):
        pass

    def log_error(self, message: str):
        print(f"ERROR: {message}")

    def log_warning(self, message: str):
        print(f"WARNING: {message}")


def get_ci_adapter() -> CIAdapter:
    """Detect and return appropriate CI adapter"""
    if os.getenv("GITHUB_ACTIONS"):
        return GitHubActionsAdapter()
    elif os.getenv("JENKINS_HOME"):
        return JenkinsAdapter()
    elif os.getenv("GITLAB_CI"):
        return GitLabCIAdapter()
    else:
        return LocalAdapter()
```

**Size**: ~150 lines

---

### 3. Setup Script

**File**: `agentic-dev-flow/setup.sh`

**Purpose**: One-command setup for users

**Structure**:

```bash
#!/bin/bash
set -e

echo "🚀 ADF Setup Script"
echo "==================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

# Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    echo "Please install Python 3.12+: https://www.python.org/downloads/"
    exit 1
fi
echo -e "${GREEN}✓${NC} Python 3 found"

# Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git not found${NC}"
    echo "Please install Git: https://git-scm.com/downloads"
    exit 1
fi
echo -e "${GREEN}✓${NC} Git found"

# GitHub CLI
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} GitHub CLI not found"
    echo "Installing gh CLI..."
    # Try to install based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install gh
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Please install gh CLI: https://cli.github.com/"
        exit 1
    else
        echo "Please install gh CLI: https://cli.github.com/"
        exit 1
    fi
fi
echo -e "${GREEN}✓${NC} GitHub CLI found"

# Claude CLI
if ! command -v claude &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} Claude CLI not found"
    echo "Installing Claude CLI..."
    curl -fsSL https://install.claude.ai | sh
    echo "Please restart your shell and run this script again"
    exit 0
fi
echo -e "${GREEN}✓${NC} Claude CLI found"

echo ""
echo "📦 Installing dependencies..."
pip install -r requirements-adf.txt
echo -e "${GREEN}✓${NC} Dependencies installed"

echo ""
echo "🔑 Configuring environment..."

# Check if .env exists
if [ ! -f "../.env" ]; then
    echo "Creating .env file..."
    cp .env.template ../.env
    echo -e "${YELLOW}⚠${NC} Please edit .env and add your ANTHROPIC_API_KEY"
    echo ""
    read -p "Press Enter to open .env in editor..."
    ${EDITOR:-nano} ../.env
fi

# Verify API key
source ../.env
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}❌ ANTHROPIC_API_KEY not set${NC}"
    echo "Please add your API key to .env file"
    exit 1
fi
echo -e "${GREEN}✓${NC} API key configured"

echo ""
echo "🏥 Running health check..."
python -m adf.health_check
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Health check failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Health check passed"

echo ""
echo "🔐 Configuring GitHub Secrets..."
echo "You need to add ANTHROPIC_API_KEY to GitHub Secrets"
echo ""
echo "Run this command:"
echo "  gh secret set ANTHROPIC_API_KEY --body \"\$ANTHROPIC_API_KEY\""
echo ""
read -p "Press Enter to continue..."

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create a test issue in your repository"
echo "2. Comment 'adf' on the issue"
echo "3. Watch the workflow run in the Actions tab"
echo ""
echo "Documentation: ./README.md"
echo "Customization: ./CUSTOMIZATION.md"
```

**Size**: ~150 lines

---

### 4. Configuration File

**File**: `agentic-dev-flow/adf-config.yml`

**Purpose**: User-customizable behavior

**Structure**:

```yaml
# ADF Configuration File
# Customize ADF behavior for your project

adf:
  version: "1.0"

  # Issue Processing
  issue_types:
    - feature
    - bug
    - chore

  # Trigger Configuration
  trigger:
    # Auto-process new issues?
    auto_process_new_issues: false

    # Keyword to trigger processing in comments
    trigger_keyword: "adf"

  # Branch Naming
  branch:
    prefix:
      feature: "feat"
      bug: "fix"
      chore: "chore"
    include_adf_id: true
    include_issue_number: true

  # Agent Configuration
  agents:
    classifier:
      command: "/classify_issue"

    planner:
      feature: "/feature"
      bug: "/bug"
      chore: "/chore"

    implementor:
      command: "/implement"

    branch_generator:
      command: "/generate_branch_name"

    pr_creator:
      command: "/pull_request"

  # Output Paths
  paths:
    specs: "specs"
    agents: "agents"

  # GitHub Integration
  github:
    # Comment frequency
    comment_strategy: "single_updated"  # or "multiple"

    # Include workflow link in comments?
    include_workflow_link: true

    # Auto-assign PR to issue creator?
    auto_assign_pr: true

  # Execution Options
  execution:
    # Maximum execution time (minutes)
    max_execution_time: 30

    # Enable verbose logging?
    verbose: false

    # Upload artifacts on failure?
    upload_artifacts_on_failure: true

# Project-Specific Settings
project:
  # Programming language (auto-detected if not set)
  language: null  # python, javascript, go, rust, etc.

  # Test command (run before creating PR)
  test_command: null  # "pytest", "npm test", "go test ./...", etc.

  # Build command
  build_command: null  # "python -m build", "npm run build", etc.

  # Linter command
  lint_command: null  # "ruff check", "eslint .", etc.
```

**Size**: ~80 lines

---

### 5. Documentation Files

#### agentic-dev-flow/README.md

**Structure**:

```markdown
# Agentic Dev Flow (ADF)

Transform GitHub issues into pull requests automatically using Claude Code.

## What is ADF?

ADF is a GitHub Actions-based workflow that:
1. Monitors your GitHub issues
2. Classifies them as features, bugs, or chores
3. Creates detailed implementation plans
4. Implements the changes automatically
5. Opens pull requests for review

## Quick Start

### Prerequisites

- Python 3.12+
- Git
- GitHub CLI (`gh`)
- Claude Code CLI (`claude`)
- Anthropic API key

### Installation

1. Copy `agentic-dev-flow/` folder to your repository root

2. Run setup script:
```bash
cd agentic-dev-flow
./setup.sh
```

3. Configure GitHub Secrets:
```bash
gh secret set ANTHROPIC_API_KEY
```

4. Create a test issue and comment `adf`

5. Watch the magic happen in Actions tab!

## How It Works

[Architecture diagram here]

When you comment `adf` on an issue:

1. **Classify**: Determines if it's a feature, bug, or chore
2. **Branch**: Creates a semantic branch name
3. **Plan**: Generates a detailed implementation plan
4. **Implement**: Writes the code following the plan
5. **Pull Request**: Opens a PR with summary and test plan

## Configuration

See `adf-config.yml` for all configuration options.

## Customization

Want to customize behavior? See [CUSTOMIZATION.md](./CUSTOMIZATION.md)

## CI/CD Portability

Using Jenkins or GitLab CI? See [examples/](./examples/)

## Troubleshooting

See [TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)

## License

MIT
```

**Size**: ~300 lines (with expanded sections)

---

#### agentic-dev-flow/SETUP.md

**Detailed setup instructions with screenshots**

**Size**: ~300 lines

---

#### agentic-dev-flow/CUSTOMIZATION.md

**How to extend and customize ADF**

**Size**: ~400 lines

---

#### agentic-dev-flow/docs/ARCHITECTURE.md

**System design and architecture documentation**

**Size**: ~500 lines

---

### 6. Environment Template

**File**: `agentic-dev-flow/.env.template`

```bash
# Anthropic API Key (Required)
# Get your key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=

# GitHub Personal Access Token (Optional for local testing)
# Not needed in GitHub Actions (uses GITHUB_TOKEN)
GITHUB_PAT=

# Claude CLI Configuration
CLAUDE_CODE_PATH=claude
CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=true

# ADF Configuration
ADF_LOG_LEVEL=INFO
ADF_ENABLE_VERBOSE=false
ADF_MAX_EXECUTION_TIME=30

# Debugging
# Set to 'true' to save all agent prompts and outputs
ADF_DEBUG=false
```

---

### 7. CI/CD Examples

#### agentic-dev-flow/examples/jenkins/Jenkinsfile

**Jenkins pipeline example**

```groovy
pipeline {
    agent any

    environment {
        ANTHROPIC_API_KEY = credentials('anthropic-api-key')
    }

    triggers {
        // Poll GitHub for new issues
        pollSCM('H/5 * * * *')
    }

    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r agentic-dev-flow/requirements-adf.txt'
            }
        }

        stage('Health Check') {
            steps {
                sh 'python -m adf.health_check'
            }
        }

        stage('Process Issue') {
            when {
                // Add logic to detect new issues
                expression { return true }
            }
            steps {
                sh '''
                    cd agentic-dev-flow
                    python -m adf.adf_orchestrator ${ISSUE_NUMBER}
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'agents/**, specs/**', allowEmptyArchive: true
        }
    }
}
```

**Size**: ~100 lines

---

#### agentic-dev-flow/examples/gitlab/.gitlab-ci.yml

**GitLab CI example**

```yaml
variables:
  ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY

stages:
  - health-check
  - process

health-check:
  stage: health-check
  image: python:3.12
  script:
    - pip install -r agentic-dev-flow/requirements-adf.txt
    - python -m adf.health_check

process-issue:
  stage: process
  image: python:3.12
  rules:
    - if: $CI_PIPELINE_SOURCE == "issue"
  script:
    - pip install -r agentic-dev-flow/requirements-adf.txt
    - cd agentic-dev-flow
    - python -m adf.adf_orchestrator $CI_ISSUE_IID
  artifacts:
    paths:
      - agents/
      - specs/
    when: always
```

**Size**: ~100 lines

---

## Directory Structure

### Current Structure (Before Refactor)

```
agentic-dev-flow-core/
├── adf/
│   ├── adf_plan_build.py      (537 lines)
│   ├── agent.py               (260 lines)
│   ├── github.py              (281 lines)
│   ├── data_types.py          (144 lines)
│   ├── trigger_cron.py        (224 lines) ❌ DELETE
│   ├── trigger_webhook.py     (207 lines) ❌ DELETE
│   ├── health_check.py        (382 lines)
│   └── utils.py               (79 lines)
│
├── src/                       ❌ DELETE (demo app)
│   ├── app.py
│   ├── models.py
│   ├── views.py
│   ├── templates/
│   └── static/
│
├── tests/                     ❌ DELETE (demo tests)
│   └── test_app.py
│
├── .claude/
│   ├── settings.json
│   ├── commands/             (13 files)
│   └── hooks/                (5 files)
│
├── .github/
│   └── workflows/            (empty)
│
├── specs/                    (generated)
├── agents/                   (generated)
├── venv/                     ❌ DELETE
├── requirements.txt          ❌ DELETE
├── requirements-adf.txt
└── .env.sample
```

---

### Target Structure (After Refactor)

```
agentic-dev-flow/              👈 This is the template
│
├── adf/
│   ├── __init__.py
│   ├── adf_orchestrator.py    (500 lines) - Renamed & modified
│   ├── agent.py               (300 lines) - Modified
│   ├── github.py              (350 lines) - Enhanced
│   ├── data_types.py          (200 lines) - Extended
│   ├── ci_adapter.py          (150 lines) 🆕 NEW
│   ├── health_check.py        (280 lines) - Simplified
│   └── utils.py               (150 lines) - Extended
│
├── .claude/
│   ├── settings.json
│   ├── commands/              (13 files - generalized)
│   │   ├── feature.txt
│   │   ├── bug.txt
│   │   ├── chore.txt
│   │   ├── classify_issue.txt
│   │   ├── implement.txt
│   │   ├── find_plan_file.txt
│   │   ├── generate_branch_name.txt
│   │   ├── commit.txt
│   │   ├── pull_request.txt
│   │   └── tools.txt
│   └── hooks/                 (5 files - verified)
│       ├── notification.py
│       ├── pre_tool_use.py
│       ├── post_tool_use.py
│       ├── stop.py
│       └── subagent_stop.py
│
├── .github/
│   └── workflows/
│       └── adf-issue-handler.yml  🆕 NEW (200 lines)
│
├── examples/                  🆕 NEW
│   ├── jenkins/
│   │   └── Jenkinsfile
│   ├── gitlab/
│   │   └── .gitlab-ci.yml
│   └── circleci/
│       └── config.yml
│
├── docs/                      🆕 NEW
│   ├── ARCHITECTURE.md        (500 lines)
│   ├── CUSTOMIZATION.md       (400 lines)
│   └── TROUBLESHOOTING.md     (300 lines)
│
├── requirements-adf.txt       (simplified)
├── adf-config.yml             🆕 NEW (80 lines)
├── .env.template              🆕 NEW
├── setup.sh                   🆕 NEW (150 lines)
├── README.md                  🆕 NEW (500 lines)
└── SETUP.md                   🆕 NEW (300 lines)
```

---

### User's Repository (After Copying Template)

```
user-awesome-project/
│
├── agentic-dev-flow/          👈 Copied from template
│   ├── adf/
│   ├── .claude/
│   ├── .github/workflows/
│   ├── examples/
│   ├── docs/
│   ├── requirements-adf.txt
│   ├── adf-config.yml
│   ├── .env.template
│   ├── setup.sh
│   ├── README.md
│   └── SETUP.md
│
├── src/                       # User's app
│   └── ...
│
├── tests/                     # User's tests
│   └── ...
│
├── specs/                     # Generated by ADF
│   └── feature-123-plan.md
│
├── agents/                    # Generated by ADF
│   └── a1b2c3d4/
│
└── .github/
    └── workflows/
        ├── adf-issue-handler.yml    # From ADF
        ├── ci.yml                   # User's existing
        └── deploy.yml               # User's existing
```

---

## Migration Strategy

### Phase 1: Cleanup & Simplification

**Goal**: Remove demo app and local-execution code

**Tasks**:
1. ❌ Delete `src/`, `tests/`, `venv/`
2. ❌ Delete `trigger_cron.py`, `trigger_webhook.py`
3. ❌ Remove dependencies: schedule, fastapi, uvicorn
4. ✅ Verify core still works: `python -m adf.adf_plan_build <issue>`
5. ✅ Update imports

**Validation**:
- Core orchestrator runs independently
- No import errors
- Health check passes

**Duration**: 2-3 days

---

### Phase 2: GitHub Actions Integration

**Goal**: Create workflow that executes orchestrator

**Tasks**:
1. 🆕 Create `.github/workflows/adf-issue-handler.yml`
2. ✏️ Add Actions detection to orchestrator
3. ✏️ Update logging for stdout
4. ✏️ Add workflow outputs
5. ✅ Test with real issue

**Validation**:
- Workflow triggers correctly
- Logs visible in Actions
- Issue gets progress comments
- PR created successfully

**Duration**: 1 week

---

### Phase 3: Template Packaging

**Goal**: Structure as copyable template

**Tasks**:
1. 📁 Create `agentic-dev-flow/` folder
2. 📁 Move files into template structure
3. 🆕 Create `setup.sh` script
4. 🆕 Create `adf-config.yml`
5. 🆕 Write README.md

**Validation**:
- Can copy folder to new repo
- Setup script works end-to-end
- Test issue processes successfully

**Duration**: 1 week

---

### Phase 4: Generalization

**Goal**: Remove project-specific assumptions

**Tasks**:
1. ✏️ Update slash commands (remove Python-specific)
2. ✏️ Make commands language-agnostic
3. ✏️ Add project type detection
4. ✅ Test with non-Python projects

**Validation**:
- Works with Node.js project
- Works with Go project
- Commands adapt to structure

**Duration**: 1 week

---

### Phase 5: CI/CD Portability

**Goal**: Abstract CI-specific logic

**Tasks**:
1. 🆕 Create `ci_adapter.py`
2. ✏️ Refactor orchestrator to use adapter
3. 🆕 Create Jenkins example
4. 🆕 Create GitLab CI example

**Validation**:
- Jenkins example works
- GitLab CI example works
- Easy to add new adapters

**Duration**: 1 week

---

### Phase 6: Documentation & Polish

**Goal**: Production-ready release

**Tasks**:
1. 🆕 Write ARCHITECTURE.md
2. 🆕 Write CUSTOMIZATION.md
3. 🆕 Write TROUBLESHOOTING.md
4. 🆕 Create video walkthrough
5. ✅ End-to-end testing
6. ✅ Security audit

**Validation**:
- New user can setup in < 10 min
- Docs answer common questions
- No security vulnerabilities

**Duration**: 2 weeks

---

### Phase 7: Release

**Goal**: Public release

**Tasks**:
1. Version tagging (v1.0.0)
2. Release notes
3. Publish to GitHub
4. Announce to community

**Duration**: 3-5 days

---

**Total Timeline**: 7-8 weeks

---

## Design Principles

### 1. Portability (CI/CD Agnostic)

**Goal**: Work in ANY CI/CD system with minimal changes

**Implementation**:
- Abstract CI-specific logic into `ci_adapter.py`
- Provide adapters for: GitHub Actions, Jenkins, GitLab
- Core orchestrator uses adapter interface

**Example**:
```python
# GOOD: CI-agnostic
ci = get_ci_adapter()
ci.log_error("Failed to process issue")
ci.set_output("status", "failed")

# BAD: GitHub Actions specific
print("::error::Failed to process issue")
```

---

### 2. Simplicity (Plug & Play)

**Goal**: Users shouldn't need to understand internals

**Implementation**:
- Single `setup.sh` handles everything
- Configuration via YAML (no code editing)
- Sane defaults work out-of-box
- Advanced features optional

**Anti-patterns**:
- ❌ Requiring Python code edits
- ❌ Complex multi-step setup
- ❌ Undocumented dependencies
- ❌ Magic environment variables

---

### 3. Transparency (Observability)

**Goal**: Users know what ADF is doing

**Implementation**:
- Real-time issue comments
- Detailed workflow logs
- Upload artifacts (plans, logs)
- Link issue to workflow run

**Example Comment**:
```markdown
## 🤖 ADF Status Update

**Workflow**: [#123](https://...)
**ADF ID**: a1b2c3d4

### Progress
- ✅ Issue classified as: feature
- ✅ Plan created: `specs/plan.md`
- 🔄 Implementing...

**Branch**: `feat-456-a1b2c3d4-add-auth`

_Last updated: 2024-01-15 10:30 UTC_
```

---

### 4. Extensibility (User Customization)

**Goal**: Extend without forking

**Levels**:
1. **Configuration**: Edit `adf-config.yml`
2. **Commands**: Modify `.claude/commands/`
3. **Hooks**: Customize `.claude/hooks/`
4. **Agents**: Create new commands

---

### 5. Maintainability (Clear Architecture)

**Goal**: Easy to understand and modify

**Separation of Concerns**:
```
adf/
├── orchestrator.py    # Workflow logic
├── agent.py           # Claude CLI
├── github.py          # GitHub API
├── ci_adapter.py      # CI abstraction
├── data_types.py      # Types
└── utils.py           # Utilities
```

**Documentation**:
- Docstrings on all public functions
- Type hints throughout
- Architecture docs
- Inline comments for complex logic

---

## Critical Considerations

### 1. GitHub Actions Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| 6 hour timeout | Long implementations fail | Add timeout checks, break large issues |
| 20-40 concurrent jobs | Can't process 100 issues | Queue system, concurrency groups |
| API rate limits (5000/hr) | Frequent calls hit limits | Cache data, batch updates |

---

### 2. Claude Code CLI in CI

| Issue | Impact | Mitigation |
|-------|--------|------------|
| Expects interactive terminal | Features don't work | Test in non-interactive mode, use `--dangerously-skip-permissions` |
| Not in Actions by default | Need installation step | Add install to workflow, cache between runs |

---

### 3. Security Concerns

| Risk | Impact | Mitigation |
|------|--------|------------|
| API key exposure | Key leaked in logs | Use GitHub Secrets (auto-masked) |
| Untrusted code execution | Malicious injection | Validate input, isolated environment |
| Token permissions | Overly permissive | Minimal required permissions |

---

### 4. User Experience

| Issue | Impact | Mitigation |
|-------|--------|------------|
| Don't understand changes | Low trust | Comprehensive PR descriptions, link plan |
| Failed workflows | Repository clutter | Cleanup job, document manual steps |
| Customization learning curve | Can't extend | Detailed docs, examples, videos |

---

## Complexity Analysis

### Lines of Code Comparison

| Component | Current | After | Change |
|-----------|---------|-------|--------|
| **Core Python** | | | |
| Orchestrator | 537 | 500 | -37 |
| Trigger files | 431 | 0 | -431 |
| agent.py | 260 | 300 | +40 |
| github.py | 281 | 350 | +69 |
| health_check.py | 382 | 280 | -102 |
| data_types.py | 144 | 200 | +56 |
| utils.py | 79 | 150 | +71 |
| **Subtotal** | **2,114** | **1,780** | **-334 (-16%)** |
| | | | |
| **Demo App** | ~700 | 0 | -700 |
| **Configuration** | ~1,000 | ~1,000 | ~0 |
| **New Infrastructure** | 0 | 600 | +600 |
| **Documentation** | ~100 | ~2,000 | +1,900 |
| | | | |
| **TOTAL** | ~3,914 | ~5,380 | **+1,466 (+37%)** |

**Interpretation**:
- Core logic: **-16%** (simpler, more focused)
- Demo app: **-100%** (removed)
- Infrastructure: **+600 lines** (workflow, adapters)
- Documentation: **+1,900 lines** (5x better)

**Net Effect**:
- More maintainable (removed coupling)
- Better documented (5x docs)
- Production-ready (setup automation)
- +37% overall, but -16% core logic

---

## Implementation Sequence

### Sprint 1: Foundation (Week 1)
1. Create branch: `refactor/template-based-adf`
2. Delete demo app (src/, tests/)
3. Delete trigger files
4. Update requirements
5. Verify core works

### Sprint 2: Actions Integration (Week 2)
6. Create workflow file
7. Add Actions detection
8. Update logging
9. Test workflow
10. Fix issues

### Sprint 3: Template Packaging (Week 3)
11. Create folder structure
12. Move files
13. Create setup script
14. Create config
15. Test template copy

### Sprint 4: Generalization (Week 4)
16. Update commands
17. Add project detection
18. Test non-Python projects
19. Add examples

### Sprint 5: Documentation (Week 5)
20. Write README
21. Write SETUP.md
22. Write ARCHITECTURE.md
23. Write CUSTOMIZATION.md
24. Create video

### Sprint 6: CI/CD Portability (Week 6)
25. Create CI adapter
26. Write Jenkins example
27. Write GitLab example
28. Document porting

### Sprint 7: Polish (Week 7)
29. End-to-end testing
30. Fix bugs
31. Optimize performance
32. Security audit

### Sprint 8: Release (Week 8)
33. Version tagging
34. Release notes
35. Publish
36. Announce

---

## Success Criteria

### Functional Requirements

**Must Have**:
- [ ] Works in GitHub Actions
- [ ] Copy into any repository
- [ ] Processes issues automatically
- [ ] Creates branches, plans, PRs
- [ ] Updates issue with progress
- [ ] Handles failures gracefully
- [ ] Works with Python projects

**Should Have**:
- [ ] Works with Node.js, Go, Rust
- [ ] Configurable via YAML
- [ ] Extensible via commands
- [ ] Portable to Jenkins/GitLab
- [ ] Clear error messages
- [ ] Health check validation

**Nice to Have**:
- [ ] Dashboard with statistics
- [ ] Success rate metrics
- [ ] Cost tracking
- [ ] Multi-issue parallelization
- [ ] Preview/dry-run mode

---

### User Experience

**Setup**:
- [ ] Complete in < 10 minutes
- [ ] Single command: `./setup.sh`
- [ ] Clear error messages
- [ ] Works on macOS, Linux, Windows (WSL)

**Usage**:
- [ ] Comment "adf" → workflow starts
- [ ] Progress in issue comments
- [ ] Link to workflow logs
- [ ] Tagged when PR ready
- [ ] Clear failure messages

**Customization**:
- [ ] Modify without touching Python
- [ ] Config changes don't need restart
- [ ] Examples provided
- [ ] Extension points documented

---

### Quality

**Reliability**:
- [ ] Handles network failures
- [ ] Retries transient errors
- [ ] Cleans up on failure
- [ ] Never leaves broken state

**Performance**:
- [ ] Simple issues < 5 minutes
- [ ] Complex issues < 30 minutes
- [ ] No timeout exceeded
- [ ] Efficient API usage

**Security**:
- [ ] Keys never in logs
- [ ] Minimal permissions
- [ ] Input validation
- [ ] Dependencies updated

**Maintainability**:
- [ ] Coverage > 70%
- [ ] All functions documented
- [ ] Architecture explained
- [ ] Example customizations

---

## Final Recommendations

### Priority 1: Start Simple

**Recommendation**: MVP first, optimize later

**MVP**:
- Basic workflow for features only
- Python projects only
- Minimal docs (README + SETUP)
- No CI portability yet

**Timeline**: 2-3 weeks

---

### Priority 2: Focus on DX

**Recommendation**: Make setup effortless

**Key**:
- `setup.sh` that Just Works™
- Health check explains issues
- Clear progress in comments
- Actionable error messages

---

### Priority 3: Document During Development

**Recommendation**: Write docs AS you build

**Why**:
- Forces UX thinking
- Easier when context fresh
- Enables early feedback

---

### Priority 4: Beta Test

**Recommendation**: 3-5 testers before release

**Who**:
- Python project user
- Node.js project user
- DevOps engineer
- Documentation writer
- Security-focused user

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Claude CLI breaks in Actions | High | Medium | Test early, document workarounds |
| Setup too complex | High | High | Invest in setup.sh + docs |
| Rate limits hit | Medium | Medium | Caching, batching |
| Security vulnerability | High | Low | Audit, input validation |
| Poor adoption | Medium | Medium | Focus on DX, beta test |
| Maintenance burden | Low | High | Simple architecture, good docs |

---

## Summary

### What We're Doing

**Transform ADF from**:
- Local execution → GitHub workflow
- Monolithic → Portable template
- Demo-coupled → Framework-agnostic
- Polling/webhooks → Native CI events

### Key Changes

**DELETE** (1,131 lines):
- Demo app
- Trigger files
- Unused dependencies

**MODIFY** (all core files):
- Orchestrator for Actions
- GitHub ops for workflow
- Logging for CI
- Commands for generalization

**CREATE** (2,600 lines):
- GitHub workflow
- Setup automation
- CI adapter
- Documentation
- Examples

### End State

**Production-ready template**:
1. Copy to repo
2. Run `./setup.sh`
3. Comment "adf"
4. Get PRs

**Simple. Powerful. Extensible.**

---

## Next Steps

1. ✅ Get approval on this plan
2. Create detailed tasks in project board
3. Begin Sprint 1: Foundation
4. Weekly progress reviews
5. Adjust plan based on learnings

---

**Version**: 1.0
**Date**: 2026-01-02
**Status**: Awaiting Approval

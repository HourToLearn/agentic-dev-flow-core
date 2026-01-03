# Agentic Dev Flow (ADF) System

ADF automates software development by integrating GitHub issues with Claude Code CLI to classify issues, generate plans, implement solutions, and create pull requests.

## Quick Start

### 1. Set Environment Variables

```bash
export GITHUB_REPO_URL="https://github.com/owner/repository"
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export CLAUDE_CODE_PATH="/path/to/claude"  # Optional, defaults to "claude"
export GITHUB_PAT="gh_xxxxxxxxxxxxxxxxxxxxxxx"  # Optional, only if using different account than 'gh auth login'
```

### 2. Install Prerequisites

```bash
# GitHub CLI
brew install gh              # macOS
# or: sudo apt install gh    # Ubuntu/Debian
# or: winget install --id GitHub.cli  # Windows

# Claude Code CLI
# Follow instructions at https://docs.anthropic.com/en/docs/claude-code

# Python dependency manager (uv)
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# or: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Install ADF dependencies
uv pip install -r ../requirements-adf.txt

# Authenticate GitHub
gh auth login
```

### 3. Run ADF

```bash
cd agentic-dev-flow-core/adf/

# Process a single issue manually
uv run adf_orchestrator.py 123

```

## Script Usage Guide

### adf_orchestrator.py - Process Single Issue

Executes the complete ADF workflow for a specific GitHub issue.

```bash
# Basic usage
uv run adf_orchestrator.py 456

# What it does:
# 1. Fetches issue #456 from GitHub
# 2. Creates feature branch
# 3. Classifies issue type (/chore, /bug, /feature)
# 4. Generates implementation plan
# 5. Implements the solution
# 6. Creates commits and pull request
```

**Example output:**

```
ADF ID: e5f6g7h8
issue_command: /feature
Working on branch: feat-456-e5f6g7h8-add-user-authentication
plan_file_path: specs/add-user-authentication-system-plan.md
Pull request created: https://github.com/owner/repo/pull/789
```

## How ADF Works

1. **Issue Classification**: Analyzes GitHub issue and determines type:

   - `/chore` - Maintenance, documentation, refactoring
   - `/bug` - Bug fixes and corrections
   - `/feature` - New features and enhancements

2. **Planning**: `sdlc_planner` agent creates implementation plan with technical approach and step-by-step tasks.

3. **Implementation**: `sdlc_implementor` agent executes the plan, implements changes, and runs tests.

4. **Integration**: Creates git commits and pull request with semantic commit messages.

## Troubleshooting

### Environment Issues

```bash
# Check required variables
env | grep -E "(GITHUB|ANTHROPIC|CLAUDE)"

# Verify GitHub auth
gh auth status

# Test Claude Code
claude --version
```

### Common Errors

**"Claude Code CLI is not installed"**

```bash
which claude  # Check if installed
# Reinstall from https://docs.anthropic.com/en/docs/claude-code
```

**"Missing GITHUB_PAT"** (Optional - only needed if using different account than 'gh auth login')

```bash
export GITHUB_PAT=$(gh auth token)
```

**"Agent execution failed"**

```bash
# Check agent output
cat agents/*/sdlc_planner/raw_output.jsonl | tail -1 | jq .
```

### Debug Mode

```bash
export ADF_DEBUG=true
uv run adf_orchestrator.py 123  # Verbose output
```

## Configuration

### ADF Tracking

Each workflow run gets a unique 8-character ID (e.g., `a1b2c3d4`) that appears in issue comments, output files, git commits and PRs.

### Model Selection

Edit `data_types.py` to change default model in `AgentTemplateRequest`:

- `model="sonnet"` - Faster, lower cost (default)
- `model="opus"` - Better for complex tasks

### Output Structure

```
agents/
├── a1b2c3d4/
│   ├── sdlc_planner/
│   │   └── raw_output.jsonl
│   └── sdlc_implementor/
│       └── raw_output.jsonl
```

## Technical Details

### Core Components

- `agent.py` - Claude Code CLI integration
- `data_types.py` - Pydantic models for type safety
- `github.py` - GitHub API operations
- `adf_orchestrator.py` - Main workflow orchestration

### Branch Naming

```
{type}-{issue_number}-{adf_id}-{slug}
```

Example: `feat-456-e5f6g7h8-add-user-authentication`

### Commit Format

```
{type}: {description} for #{issue_number}

Generated with ADF ID: {adf_id}
🤖 Generated with [Claude Code](https://claude.ai/code)
```

### API Rate Limits

- GitHub: 5000 requests/hour (authenticated)
- Anthropic: Based on your plan tier
- Automatic retry with exponential backoff

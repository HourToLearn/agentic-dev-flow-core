# Agentic Dev Flow (ADF)

**Transform GitHub Issues into Pull Requests Automatically using Claude Code**

---

## What is ADF?

ADF (Agentic Dev Flow) is a GitHub Actions-based workflow that automatically transforms GitHub issues into production-ready pull requests. It uses Claude Code to understand your issue, create an implementation plan, write the code, and open a PR for review.

### Key Features

- **Zero-cost Execution**: Runs on GitHub Actions (free for public repos)
- **Fully Automated**: From issue to PR without manual intervention
- **Intelligent Planning**: Creates detailed implementation plans before coding
- **Multi-language Support**: Works with Python, JavaScript, Go, Rust, and more
- **Customizable**: Extensive configuration options via YAML
- **CI/CD Agnostic**: Works with GitHub Actions, Jenkins, GitLab CI, and more

---

## How It Works

When you comment `adf` on a GitHub issue, ADF automatically:

1. **Classifies** the issue as a feature, bug, or chore
2. **Creates** a semantic branch name
3. **Plans** a detailed implementation strategy
4. **Implements** the solution following the plan
5. **Tests** the changes (if configured)
6. **Opens** a pull request for review

All progress is tracked with real-time comments on the original issue.

---

## Quick Start

### Prerequisites

- GitHub repository
- [Anthropic API key](https://console.anthropic.com/)
- Python 3.12+

### Installation

**Step 1: Configure Environment**

Copy the environment template and add your API key:

```bash
cp .env.template .env
# Edit .env and add your ANTHROPIC_API_KEY
```

**Step 2: Configure GitHub Secrets**

Add your Anthropic API key to GitHub Secrets:

```bash
gh secret set ANTHROPIC_API_KEY
```

Or manually:
1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `ANTHROPIC_API_KEY`
5. Value: Your Anthropic API key from https://console.anthropic.com/

**Step 3: Enable GitHub Actions**

Ensure GitHub Actions is enabled for your repository:
1. Go to Settings → Actions → General
2. Allow all actions and reusable workflows
3. Set workflow permissions to "Read and write permissions"

**Step 4: Test It!**

1. Create a new issue in your repository
2. Add a clear description of what you want (e.g., "Add user authentication")
3. Comment `adf` on the issue
4. Watch the magic happen in the Actions tab!

---

## Configuration

ADF can be customized via `adf-config.yml`:

```yaml
adf:
  trigger:
    # Keyword to trigger ADF
    trigger_keyword: "adf"
    # Auto-process new issues?
    auto_process_new_issues: false

  github:
    # Comment strategy
    comment_strategy: "single_updated"
    # Auto-assign PRs?
    auto_assign_pr: true

  project:
    # Test command to run before creating PR
    test_command: "pytest"
    # Build command
    build_command: "python -m build"
```

See `adf-config.yml` for all configuration options.

---

## Usage

### Basic Usage

1. Create or open an issue
2. Comment `adf` to trigger processing
3. ADF will:
   - Comment with workflow status
   - Create a branch
   - Commit the plan
   - Implement the solution
   - Create a pull request

### Advanced Usage

**Custom Issue Types**

ADF supports three issue types:
- **Feature**: New functionality (uses `/feature` command)
- **Bug**: Bug fixes (uses `/bug` command)
- **Chore**: Maintenance tasks (uses `/chore` command)

**Customizing Commands**

Edit `.claude/commands/` to customize how ADF plans and implements:
- `feature.txt`: Feature planning template
- `bug.txt`: Bug fix template
- `chore.txt`: Chore template
- `implement.txt`: Implementation instructions

**Testing Locally**

You can run ADF locally for testing:

```bash
# Install dependencies
pip install -r requirements-adf.txt

# Run on an issue
python -m adf.adf_orchestrator 123  # Replace 123 with issue number
```

---

## Architecture

```
┌─────────────────┐
│  GitHub Issue   │
└────────┬────────┘
         │
         │ trigger: "adf" comment
         ▼
┌─────────────────────────┐
│  GitHub Actions         │
│  Workflow              │
└────────┬────────────────┘
         │
         ▼
┌──────────────────────────┐
│  ADF Orchestrator        │
└────────┬─────────────────┘
         │
         ├──► Classifier Agent
         ├──► Branch Generator
         ├──► Planner Agent
         ├──► Implementor Agent
         └──► PR Creator
                │
                ▼
         ┌─────────────────┐
         │  Pull Request   │
         └─────────────────┘
```

---

## Project Structure

```
agentic-dev-flow-core/
├── adf/                          # Core ADF modules
│   ├── adf_orchestrator.py      # Main orchestration logic
│   ├── agent.py                 # Claude CLI integration
│   ├── github.py                # GitHub API operations
│   ├── data_types.py            # Type definitions
│   ├── utils.py                 # Utility functions
│   ├── ci_adapter.py            # CI/CD abstraction
│   └── health_check.py          # System validation
│
├── .claude/                      # Claude Code configuration
│   ├── commands/                # Slash commands
│   │   ├── feature.txt          # Feature planning
│   │   ├── bug.txt              # Bug fix planning
│   │   ├── chore.txt            # Chore planning
│   │   ├── implement.txt        # Implementation instructions
│   │   └── ...                  # Other commands
│   ├── hooks/                   # Lifecycle hooks
│   └── settings.json            # Permissions and config
│
├── .github/
│   └── workflows/
│       └── adf-issue-handler.yml # Main workflow
│
├── adf-config.yml               # User configuration
├── .env.template                # Environment template
├── requirements-adf.txt         # Python dependencies
└── README.md                    # This file
```

---

## Customization

### Modifying Planning Behavior

Edit `.claude/commands/feature.txt` (or `bug.txt`, `chore.txt`):

```markdown
You are planning implementation for: {issue_title}

Steps:
1. Analyze the requirements
2. Identify files to modify
3. Create implementation plan
4. Consider edge cases
5. Plan testing strategy

[Your custom instructions here]
```

### Adding Hooks

Add custom hooks in `.claude/hooks/`:
- `pre_tool_use.py`: Runs before each tool
- `post_tool_use.py`: Runs after each tool
- `notification.py`: Custom notifications

---

## Troubleshooting

### ADF doesn't trigger

**Check:**
- GitHub Actions is enabled
- Workflow has write permissions
- `ANTHROPIC_API_KEY` secret is set correctly
- You commented exactly `adf` (case-sensitive)

### Workflow fails immediately

**Check:**
- Anthropic API key is valid
- GitHub token has required permissions
- Python 3.12+ is being used

### Need help?

- Check workflow logs in Actions tab
- Review uploaded artifacts
- Open an issue on GitHub

---

## License

MIT License

---

**Made with Claude Code**

Transform your development workflow today!

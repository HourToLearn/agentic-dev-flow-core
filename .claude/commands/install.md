# Install ADF & Application Dependencies

## Read

.env.sample (never read .env)
requirements-adf.txt
\*.claude/commands/user_project_setup.md (if exists)

## Read and Execute

.claude/commands/user_project_setup.md

## Run

- `python --version - Verify Python 3.12+
- `pip install -r requirements-adf.txt Install ADF dependencies
- `cp .env.template .env Create environment file
- `git config --local user.name "ADF Bot" - Configure git user only in this specific project
- `git config --local user.email "adf-bot@users.noreply.github.com" - Configure git email only in this specific project

## Report

- Output the work you've just done in a concise bullet point list.
- Instruct the user to fill out the root level ./.env based on .env.sample.

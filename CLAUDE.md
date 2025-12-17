# Game Time - Claude Code Configuration

This file configures allowed Bash commands for Claude Code to execute without user approval.

## Allowed Tools

### Git - Version Control
```
Bash(git:*)
```

### GitHub CLI - Repository and Workflow Management
```
Bash(gh:*)
Bash(gh auth:*)
Bash(gh repo:*)
Bash(gh pr:*)
Bash(gh issue:*)
Bash(gh workflow:*)
Bash(gh run:*)
Bash(gh release:*)
Bash(gh gist:*)
Bash(gh api:*)
Bash(gh codespace:*)
Bash(gh search:*)
Bash(gh alias:*)
```

### Python - Package Management and Virtual Environments
```
Bash(python:*)
Bash(python3:*)
Bash(pip:*)
Bash(pip3:*)
Bash(pip-compile:*)
Bash(pip-sync:*)
Bash(source */bin/activate:*)
Bash(deactivate:*)
```

### Database - PostgreSQL
```
Bash(createdb:*)
Bash(dropdb:*)
Bash(psql:*)
Bash(pg_dump:*)
Bash(pg_restore:*)
```

### Database Migrations - Alembic
```
Bash(alembic:*)
```

### Docker - Container Management
```
Bash(docker:*)
Bash(docker-compose:*)
Bash(docker compose:*)
```

### Testing - Pytest
```
Bash(pytest:*)
Bash(python -m pytest:*)
Bash(python3 -m pytest:*)
```

### Testing - Playwright
```
Bash(npx playwright:*)
Bash(npm test:*)
Bash(npm run test:*)
```

### Code Quality - Linting and Formatting
```
Bash(ruff:*)
Bash(mypy:*)
Bash(black:*)
Bash(isort:*)
Bash(flake8:*)
Bash(pylint:*)
```

### Security Scanning
```
Bash(bandit:*)
Bash(safety:*)
```

### Pre-commit Hooks
```
Bash(pre-commit:*)
```

### Web Server - Uvicorn and Gunicorn
```
Bash(uvicorn:*)
Bash(gunicorn:*)
```

### Redis - Cache Management
```
Bash(redis-cli:*)
```

### Node.js - Package Management
```
Bash(node:*)
Bash(npm:*)
Bash(npx:*)
Bash(yarn:*)
```

### Load Testing - Locust
```
Bash(locust:*)
```

### File Operations
```
Bash(mkdir:*)
Bash(rmdir:*)
Bash(rm:*)
Bash(cp:*)
Bash(mv:*)
Bash(touch:*)
Bash(cat:*)
Bash(less:*)
Bash(more:*)
Bash(head:*)
Bash(tail:*)
Bash(wc:*)
Bash(find:*)
Bash(grep:*)
Bash(sed:*)
Bash(awk:*)
Bash(ls:*)
Bash(pwd:*)
Bash(cd:*)
Bash(tree:*)
```

### Archive and Compression
```
Bash(tar:*)
Bash(zip:*)
Bash(unzip:*)
Bash(gzip:*)
Bash(gunzip:*)
```

### Process Management
```
Bash(ps:*)
Bash(pgrep:*)
Bash(pkill:*)
Bash(kill:*)
Bash(killall:*)
Bash(jobs:*)
Bash(fg:*)
Bash(bg:*)
Bash(nohup:*)
Bash(top:*)
Bash(htop:*)
```

### Environment Variables
```
Bash(export:*)
Bash(env:*)
Bash(printenv:*)
Bash(source:*)
```

### Networking
```
Bash(curl:*)
Bash(wget:*)
Bash(http:*)
Bash(netstat:*)
Bash(lsof:*)
Bash(ping:*)
Bash(telnet:*)
```

### System Information
```
Bash(uname:*)
Bash(df:*)
Bash(du:*)
Bash(free:*)
Bash(uptime:*)
Bash(whoami:*)
Bash(hostname:*)
```

### Text Processing
```
Bash(echo:*)
Bash(printf:*)
Bash(tr:*)
Bash(cut:*)
Bash(paste:*)
Bash(sort:*)
Bash(uniq:*)
Bash(diff:*)
```

### Shell Utilities
```
Bash(which:*)
Bash(whereis:*)
Bash(basename:*)
Bash(dirname:*)
Bash(xargs:*)
Bash(tee:*)
Bash(watch:*)
Bash(timeout:*)
Bash(sleep:*)
Bash(date:*)
```

### Permissions (read-only operations)
```
Bash(chmod:*)
Bash(chown:*)
```

### Symbolic Links
```
Bash(ln:*)
Bash(readlink:*)
```

### Disk Usage
```
Bash(ncdu:*)
```

### JSON Processing
```
Bash(jq:*)
```

### YAML Processing
```
Bash(yq:*)
```

### Make
```
Bash(make:*)
```

### Shell Scripts
```
Bash(bash:*)
Bash(sh:*)
Bash(./*)
```

### Package Managers (System)
```
Bash(apt:*)
Bash(apt-get:*)
Bash(brew:*)
Bash(yum:*)
```

## Read-Only Access Patterns

Allow reading any files in common project locations:
```
Read(/home/dan/game-time/**)
Read(/home/dan/game-time/.*)
```

## Notes

- All Git operations are allowed for seamless version control
- All GitHub CLI operations are allowed for CI/CD and collaboration
- All testing tools (pytest, playwright) are allowed for TDD workflow
- All Docker operations are allowed for containerized development
- File operations are broadly allowed for project management
- Database operations are allowed for migrations and seeding
- Code quality tools are allowed for automated formatting and linting

## Security Considerations

While these tools are broadly allowed, Claude Code will:
- Never run destructive operations without clear context
- Confirm before force-pushing to main/master branches
- Ask before dropping databases or removing production data
- Validate before running commands with `sudo` or elevated privileges
- Check before making network requests to external services

## Usage

This configuration enables fully automated development workflow:
1. ✅ Create and manage files
2. ✅ Run tests automatically
3. ✅ Format and lint code
4. ✅ Manage Git commits
5. ✅ Run Docker containers
6. ✅ Execute database migrations
7. ✅ Install dependencies
8. ✅ Build and deploy

Last updated: 2025-01-15

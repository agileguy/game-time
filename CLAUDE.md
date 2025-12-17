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

## Phase Implementation Workflow

When implementing any phase from PLAN.md, follow this workflow:

### 1. Branch Creation
```bash
# Create feature branch from main for the phase
git checkout main
git pull origin main
git checkout -b phase/N-phase-name
```

**Branch Naming Convention:**
- `phase/1-core-infrastructure`
- `phase/2-lobby-system`
- `phase/3-game-base-system`
- `phase/4-horse-race-game`
- `phase/5-trivia-game`
- `phase/6-memory-game`
- `phase/7-polish-testing`

### 2. Implementation Steps

**For each step within the phase:**

a. **Create the implementation**
   - Write code following the plan
   - Use TodoWrite to track progress
   - Follow security best practices from SECURITY.md

b. **Write tests FIRST or ALONGSIDE**
   - Unit tests for new functions/classes
   - Integration tests for API endpoints
   - E2E tests for user flows (where applicable)
   - Aim for 80%+ coverage

c. **Run tests and verify**
   ```bash
   # Unit tests
   pytest tests/unit -v

   # Integration tests (if applicable)
   pytest tests/integration -v

   # Code quality
   ruff format .
   ruff check .
   mypy app
   ```

d. **Update documentation**
   - Update relevant .md files if APIs change
   - Add docstrings to new functions
   - Update PLAN.md progress checkboxes
   - Keep README.md current

e. **Commit the step**
   ```bash
   git add .
   git commit -m "Phase N: Implement [specific feature]

   - Add [component/feature]
   - Add tests for [component/feature]
   - Update [documentation]

   Tests: X passing
   Coverage: X%"
   ```

**Commit Message Format:**
```
Phase N: [Short description]

[Detailed description of what was implemented]

- Bullet point of changes
- Another change
- Tests added/updated

Tests: [test results]
Coverage: [coverage %]
```

### 3. Continuous Integration

After each commit:
```bash
# Ensure tests pass
pytest

# Check code quality
ruff check .
mypy app

# Verify no regressions
pytest tests/ --cov=app
```

### 4. Documentation Maintenance

Keep these files updated throughout the phase:
- **PLAN.md**: Mark completed items with `[x]`
- **README.md**: Update if new features added
- **SECURITY.md**: Update if security features added
- **TESTING.md**: Add new test examples
- **API docs**: Update OpenAPI/Swagger specs

### 5. Pull Request Creation

When phase is complete:

a. **Final verification**
   ```bash
   # Run full test suite
   pytest tests/ -v --cov=app --cov-report=term

   # Check coverage threshold
   pytest --cov=app --cov-fail-under=80

   # Security scan
   bandit -r app
   safety check

   # Code quality
   ruff check .
   mypy app --strict
   ```

b. **Push branch**
   ```bash
   git push -u origin phase/N-phase-name
   ```

c. **Create PR with GitHub CLI**
   ```bash
   gh pr create \
     --title "Phase N: [Phase Name]" \
     --body "$(cat <<'EOF'
   ## Summary
   Implements Phase N: [Phase Name] from PLAN.md

   ### What's Included
   - Feature 1
   - Feature 2
   - Feature 3

   ### Tests Added
   - Unit tests: X files, Y tests
   - Integration tests: X files, Y tests
   - E2E tests: X scenarios

   ### Coverage
   - Overall: X%
   - New code: Y%

   ### Documentation Updated
   - [x] PLAN.md progress tracked
   - [x] README.md updated
   - [x] API documentation current
   - [x] Tests documented in TESTING.md

   ### Checklist
   - [x] All tests passing
   - [x] Coverage >= 80%
   - [x] Code formatted (ruff)
   - [x] Type checks passing (mypy)
   - [x] Security scan clean (bandit)
   - [x] No dependency vulnerabilities (safety)
   - [x] Documentation updated

   ### How to Test
   \`\`\`bash
   # Setup
   git checkout phase/N-phase-name
   docker-compose up -d

   # Run tests
   pytest tests/unit
   pytest tests/integration
   \`\`\`

   ### Screenshots (if applicable)
   [Add screenshots of new UI features]

   ---
   🤖 Generated with Claude Code
   EOF
   )"
   ```

d. **PR Review Checklist**
   - All CI checks passing
   - Code review completed
   - Tests demonstrate functionality
   - Documentation is clear
   - No merge conflicts
   - Security considerations addressed

### 6. Merge Strategy

**After PR approval:**
```bash
# Squash and merge (keep history clean)
gh pr merge --squash --delete-branch

# Or rebase and merge (preserve commits)
gh pr merge --rebase --delete-branch
```

### 7. Post-Merge

```bash
# Update local main
git checkout main
git pull origin main

# Delete local branch
git branch -d phase/N-phase-name

# Update PLAN.md on main if needed
# Ready for next phase
```

## Implementation Principles

### Test-Driven Development (TDD)
1. Write failing test
2. Implement minimal code to pass
3. Refactor while keeping tests green
4. Commit

### Incremental Commits
- Each commit should be logical and atomic
- Commit message should explain WHY, not just what
- Include test results in commit message
- Each commit should leave the codebase in a working state

### Documentation-as-Code
- Document while coding, not after
- Code comments explain complex logic
- README updates with feature additions
- API docs auto-generated from code

### Security-First
- Validate all inputs
- Sanitize all outputs
- Test security features
- Follow SECURITY.md guidelines

### Quality Gates
Every commit must:
- ✅ Pass all existing tests
- ✅ Add tests for new code
- ✅ Maintain or improve coverage
- ✅ Pass linting (ruff)
- ✅ Pass type checking (mypy)
- ✅ Be properly formatted

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

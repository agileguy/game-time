# Tools Inventory - Game Time Development

## Overview
This document lists all the tools (Claude Code tools and CLI tools) that will be used to build the Game Time application with minimal user interaction.

## Claude Code Tools

### File Operations
| Tool | Usage | Frequency |
|------|-------|-----------|
| **Write** | Create new files (Python, JS, HTML, CSS, configs, Dockerfiles) | Very High |
| **Edit** | Modify existing files (bug fixes, refactoring, updates) | Very High |
| **Read** | Read files to understand context before editing | Very High |
| **Glob** | Find files by pattern (e.g., `**/*.py`, `*.html`) | High |
| **Grep** | Search code for specific patterns or keywords | Medium |

### Execution & Testing
| Tool | Usage | Frequency |
|------|-------|-----------|
| **Bash** | Execute all CLI commands (git, pip, docker, tests, etc.) | Very High |
| **TodoWrite** | Track implementation progress and tasks | High |
| **Task** | Delegate complex sub-tasks (used sparingly for efficiency) | Low |

### Planning & Documentation
| Tool | Usage | Frequency |
|------|-------|-----------|
| **EnterPlanMode** | Plan complex features before implementation | Low |
| **ExitPlanMode** | Exit planning and start implementation | Low |

## CLI Tools (via Bash)

### Version Control

#### Git
```bash
# Git - Version control and collaboration
git init                          # Initialize repository
git add .                         # Stage files
git add -A                        # Stage all changes
git commit -m "message"           # Commit changes
git commit --amend                # Amend last commit
git branch                        # List branches
git branch feature/name           # Create branch
git branch -d feature/name        # Delete branch
git checkout branch_name          # Switch branch
git checkout -b feature/name      # Create and switch to branch
git merge feature/name            # Merge branches
git rebase main                   # Rebase on main
git log --oneline                 # View commit history
git log --graph --oneline --all   # Visual commit history
git status                        # Check working tree status
git diff                          # View unstaged changes
git diff --staged                 # View staged changes
git diff branch1..branch2         # Compare branches
git stash                         # Stash changes
git stash pop                     # Apply stashed changes
git stash list                    # List stashes
git remote -v                     # List remotes
git remote add origin url         # Add remote
git push origin branch            # Push to remote
git push -u origin branch         # Push and set upstream
git pull origin branch            # Pull from remote
git fetch                         # Fetch from remote
git clone url                     # Clone repository
git tag v1.0.0                    # Create tag
git push --tags                   # Push tags
git reset --soft HEAD~1           # Undo last commit (keep changes)
git reset --hard HEAD~1           # Undo last commit (discard changes)
git clean -fd                     # Remove untracked files
```

#### GitHub CLI
```bash
# Authentication
gh auth login                     # Authenticate with GitHub
gh auth status                    # Check authentication status
gh auth logout                    # Logout
gh auth refresh                   # Refresh authentication

# Repository Management
gh repo create                    # Create repository
gh repo create org/repo --public  # Create public repo
gh repo create --private          # Create private repo
gh repo clone owner/repo          # Clone repository
gh repo fork owner/repo           # Fork repository
gh repo view                      # View repository details
gh repo view --web                # Open in browser
gh repo list                      # List your repositories
gh repo delete owner/repo         # Delete repository
gh repo sync                      # Sync fork with upstream

# Pull Requests
gh pr create                      # Create pull request
gh pr create --title "Title" --body "Description"
gh pr create --draft              # Create draft PR
gh pr list                        # List pull requests
gh pr list --state open           # List open PRs
gh pr view 123                    # View PR details
gh pr view 123 --web              # Open PR in browser
gh pr checkout 123                # Checkout PR locally
gh pr diff 123                    # View PR diff
gh pr review 123                  # Review PR
gh pr review 123 --approve        # Approve PR
gh pr review 123 --comment        # Comment on PR
gh pr merge 123                   # Merge pull request
gh pr merge 123 --squash          # Squash and merge
gh pr merge 123 --rebase          # Rebase and merge
gh pr close 123                   # Close PR
gh pr reopen 123                  # Reopen PR
gh pr ready 123                   # Mark draft as ready
gh pr checks                      # View PR checks status
gh pr comment 123 --body "text"   # Add comment

# Issues
gh issue create                   # Create issue
gh issue create --title "Bug" --body "Description"
gh issue list                     # List issues
gh issue view 123                 # View issue
gh issue close 123                # Close issue
gh issue reopen 123               # Reopen issue
gh issue comment 123 --body "text"  # Comment on issue
gh issue edit 123                 # Edit issue

# GitHub Actions / Workflows
gh workflow list                  # List workflows
gh workflow view workflow.yml     # View workflow
gh workflow run workflow.yml      # Trigger workflow
gh workflow enable workflow.yml   # Enable workflow
gh workflow disable workflow.yml  # Disable workflow
gh run list                       # List workflow runs
gh run view 123456                # View run details
gh run watch 123456               # Watch run in real-time
gh run rerun 123456               # Re-run workflow
gh run cancel 123456              # Cancel run

# Releases
gh release create v1.0.0          # Create release
gh release create v1.0.0 --notes "Release notes"
gh release list                   # List releases
gh release view v1.0.0            # View release
gh release download v1.0.0        # Download release assets
gh release delete v1.0.0          # Delete release

# Gists
gh gist create file.txt           # Create gist
gh gist list                      # List gists
gh gist view gist_id              # View gist
gh gist edit gist_id              # Edit gist
gh gist delete gist_id            # Delete gist

# API Access
gh api repos/owner/repo           # Make API request
gh api graphql -f query='...'     # GraphQL query

# Codespaces
gh codespace create               # Create codespace
gh codespace list                 # List codespaces
gh codespace ssh                  # SSH into codespace
gh codespace stop                 # Stop codespace
gh codespace delete               # Delete codespace

# Search
gh search repos keyword           # Search repositories
gh search issues keyword          # Search issues
gh search prs keyword             # Search pull requests

# Aliases (custom shortcuts)
gh alias set                      # Create alias
gh alias list                     # List aliases
```

### Python Development
```bash
# Python & Virtual Environment
python3 --version                 # Check Python version
python3 -m venv venv              # Create virtual environment
source venv/bin/activate          # Activate venv (Linux/Mac)
deactivate                        # Deactivate venv

# Package Management
pip install -r requirements.txt   # Install dependencies
pip install -e .                  # Install package in dev mode
pip freeze > requirements.txt     # Export dependencies
pip list                          # List installed packages
pip show package_name             # Show package info

# pip-tools (for dependency management)
pip-compile requirements.in       # Compile dependencies
pip-sync requirements.txt         # Sync environment
```

### Database Tools
```bash
# PostgreSQL
createdb gametime                 # Create database
dropdb gametime                   # Drop database
psql -d gametime                  # Connect to database
psql -l                          # List databases
pg_dump gametime > backup.sql     # Backup database
psql gametime < backup.sql        # Restore database

# Alembic (Database Migrations)
alembic init alembic              # Initialize Alembic
alembic revision --autogenerate -m "message"  # Create migration
alembic upgrade head              # Apply migrations
alembic downgrade -1              # Rollback one migration
alembic current                   # Show current revision
alembic history                   # Show migration history
alembic stamp head                # Mark current state
```

### Docker & Containers
```bash
# Docker
docker build -t gametime:latest . # Build image
docker run -p 8000:8000 gametime  # Run container
docker ps                         # List running containers
docker ps -a                      # List all containers
docker logs container_id          # View logs
docker exec -it container_id bash # Enter container
docker stop container_id          # Stop container
docker rm container_id            # Remove container
docker images                     # List images
docker rmi image_id               # Remove image
docker system prune               # Clean up

# Docker Compose
docker-compose up                 # Start services
docker-compose up -d              # Start in background
docker-compose down               # Stop services
docker-compose down -v            # Stop and remove volumes
docker-compose logs -f service    # Follow logs
docker-compose exec service bash  # Enter service container
docker-compose build              # Build images
docker-compose ps                 # List services
docker-compose restart service    # Restart service

# Test environment
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
docker-compose -f docker-compose.test.yml down -v
```

### Testing Tools
```bash
# Pytest
pytest                            # Run all tests
pytest tests/unit                 # Run unit tests
pytest tests/integration          # Run integration tests
pytest -v                         # Verbose output
pytest -k "test_name"             # Run specific test
pytest -m "unit"                  # Run tests with marker
pytest -x                         # Stop on first failure
pytest --lf                       # Run last failed tests
pytest --pdb                      # Drop to debugger on failure
pytest -n auto                    # Parallel execution
pytest --cov=app                  # Coverage report
pytest --cov-report=html          # HTML coverage report
pytest --durations=10             # Show slowest tests

# Playwright (E2E Tests)
npx playwright install            # Install browsers
npx playwright test               # Run tests
npx playwright test --headed      # Run with visible browser
npx playwright test --debug       # Debug mode
npx playwright show-report        # Show test report
npx playwright codegen            # Generate test code

# Locust (Load Testing)
locust -f locustfile.py           # Start Locust
locust --headless -u 100 -r 10    # Headless mode
```

### Code Quality Tools
```bash
# Ruff (Linter & Formatter)
ruff check .                      # Lint code
ruff check --fix .                # Fix auto-fixable issues
ruff format .                     # Format code
ruff format --check .             # Check formatting

# Mypy (Type Checking)
mypy app                          # Type check
mypy --strict app                 # Strict mode
mypy --install-types              # Install type stubs

# Bandit (Security Scanning)
bandit -r app                     # Scan for security issues
bandit -r app -f json             # JSON output
bandit -r app -ll                 # Only high severity

# Safety (Dependency Security)
safety check                      # Check dependencies
safety check --json               # JSON output

# Pre-commit Hooks
pre-commit install                # Install hooks
pre-commit run --all-files        # Run all hooks
pre-commit autoupdate             # Update hook versions
```

### Node.js & NPM (for E2E tests)
```bash
# Node & NPM
node --version                    # Check Node version
npm --version                     # Check npm version
npm init -y                       # Initialize package.json
npm install                       # Install dependencies
npm install --save-dev package    # Install dev dependency
npm run test                      # Run tests
npm run build                     # Build project
npm audit                         # Check vulnerabilities
npm audit fix                     # Fix vulnerabilities
```

### FastAPI & Uvicorn
```bash
# Uvicorn (ASGI Server)
uvicorn app.main:app --reload     # Dev server with reload
uvicorn app.main:app --host 0.0.0.0 --port 8000  # Production
uvicorn app.main:app --workers 4  # Multiple workers

# Gunicorn (Process Manager)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### File & Directory Operations
```bash
# Directory Management
mkdir -p backend/app/models       # Create directories
rmdir directory                   # Remove empty directory
rm -rf directory                  # Remove directory and contents
tree                              # Display directory tree
ls -la                            # List files with details
cd directory                      # Change directory
pwd                               # Print working directory

# File Operations
touch filename                    # Create empty file
cp source dest                    # Copy file
mv source dest                    # Move/rename file
rm filename                       # Remove file
cat filename                      # Display file contents
less filename                     # Page through file
head -n 10 filename               # First 10 lines
tail -n 10 filename               # Last 10 lines
tail -f filename                  # Follow file (logs)
wc -l filename                    # Count lines
```

### Search & Text Processing
```bash
# Find (prefer Glob tool)
find . -name "*.py"               # Find Python files
find . -type f -name "test_*.py"  # Find test files

# Grep (prefer Grep tool)
grep -r "pattern" .               # Recursive search
grep -i "pattern" file            # Case-insensitive
grep -n "pattern" file            # Show line numbers
grep -v "pattern" file            # Invert match

# Sed (prefer Edit tool)
sed 's/old/new/g' file            # Replace text
sed -i 's/old/new/g' file         # In-place replace

# Awk
awk '{print $1}' file             # Print first column
```

### Process Management
```bash
# Process Control
ps aux                            # List all processes
ps aux | grep python              # Find Python processes
kill PID                          # Kill process
killall process_name              # Kill all by name
pgrep process_name                # Find process ID
pkill process_name                # Kill by name

# Background Jobs
command &                         # Run in background
jobs                              # List background jobs
fg %1                             # Bring to foreground
bg %1                             # Resume in background
nohup command &                   # Run immune to hangup
```

### Environment & Configuration
```bash
# Environment Variables
export VAR=value                  # Set variable
echo $VAR                         # Display variable
env                               # List all variables
printenv                          # List all variables
source .env                       # Load .env file

# Dotenv
cp .env.example .env              # Copy template
```

### Networking & HTTP
```bash
# curl (HTTP requests)
curl http://localhost:8000        # GET request
curl -X POST http://localhost:8000/api/rooms  # POST
curl -H "Content-Type: application/json" -d '{"key":"value"}' url

# httpie (Better curl alternative)
http GET localhost:8000           # GET request
http POST localhost:8000/api/rooms name=test  # POST

# netstat
netstat -tulpn                    # Show listening ports
netstat -tulpn | grep 8000        # Check specific port

# lsof
lsof -i :8000                     # What's using port 8000
```

### Redis
```bash
# Redis CLI
redis-cli                         # Connect to Redis
redis-cli ping                    # Test connection
redis-cli FLUSHDB                 # Clear database
redis-cli KEYS '*'                # List all keys
redis-cli GET key                 # Get value
redis-cli SET key value           # Set value
redis-cli DEL key                 # Delete key
redis-cli INFO                    # Server info
```

### System Information
```bash
# System Info
uname -a                          # System information
df -h                             # Disk space
du -sh directory                  # Directory size
free -h                           # Memory usage
top                               # Process monitor
htop                              # Better process monitor
uptime                            # System uptime
```

### Compression & Archives
```bash
# tar
tar -czf archive.tar.gz directory # Create archive
tar -xzf archive.tar.gz           # Extract archive
tar -tzf archive.tar.gz           # List contents

# zip
zip -r archive.zip directory      # Create zip
unzip archive.zip                 # Extract zip
unzip -l archive.zip              # List contents
```

## Development Workflow Sequence

### Phase 1: Project Setup
```bash
# 1. Initialize project structure
mkdir -p backend/app/{models,schemas,services,games,routes,middleware,utils}
mkdir -p frontend/{display,controller,shared}/{css,js}
mkdir -p tests/{unit,integration,e2e,load,security,fixtures}

# 2. Initialize Git
git init
git add .
git commit -m "Initial commit"

# 3. Create virtual environment
python3 -m venv backend/venv
source backend/venv/bin/activate

# 4. Install dependencies (after creating requirements files)
pip install -r backend/requirements/dev.txt

# 5. Initialize database
createdb gametime
alembic init alembic
```

### Phase 2: Backend Development
```bash
# 1. Database migrations
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head

# 2. Run tests
pytest tests/unit -v

# 3. Start dev server
uvicorn app.main:app --reload

# 4. Format & lint
ruff format backend/app
ruff check backend/app
mypy backend/app
```

### Phase 3: Frontend Development
```bash
# 1. Install Playwright (for testing)
cd tests/e2e
npm install
npx playwright install

# 2. Run E2E tests
npx playwright test
```

### Phase 4: Docker Setup
```bash
# 1. Build images
docker-compose build

# 2. Start services
docker-compose up -d

# 3. Run migrations in container
docker-compose exec backend alembic upgrade head

# 4. View logs
docker-compose logs -f backend
```

### Phase 5: Testing
```bash
# 1. Unit tests
pytest tests/unit --cov=app --cov-report=html

# 2. Integration tests
pytest tests/integration -v

# 3. E2E tests
docker-compose -f docker-compose.test.yml run --rm playwright npm test

# 4. Load tests
docker-compose -f docker-compose.test.yml run --rm locust

# 5. Security tests
bandit -r backend/app
safety check
```

### Phase 6: Deployment
```bash
# 1. Build production images
docker-compose -f docker-compose.prod.yml build

# 2. Tag images
docker tag gametime:latest registry/gametime:v1.0.0

# 3. Push to registry
docker push registry/gametime:v1.0.0

# 4. Deploy
docker-compose -f docker-compose.prod.yml up -d
```

## Tool Categories Summary

### Essential Daily Tools (Very High Usage)
- Write, Edit, Read (file operations)
- Bash (command execution)
- git (version control)
- pytest (testing)
- uvicorn (dev server)
- docker-compose (services)

### Regular Tools (High Usage)
- Glob, Grep (code search)
- TodoWrite (progress tracking)
- alembic (migrations)
- ruff, mypy (code quality)
- pip (package management)

### Occasional Tools (Medium Usage)
- Task (complex sub-tasks)
- playwright (E2E tests)
- locust (load testing)
- bandit, safety (security)
- redis-cli (cache management)

### Specialized Tools (Low Usage)
- EnterPlanMode/ExitPlanMode (planning)
- docker build (image creation)
- pg_dump/restore (backups)
- netstat, lsof (debugging)

## Tool Installation Requirements

### Required on Host System
```bash
# Core
- Python 3.11+
- Git
- Docker & Docker Compose

# Database
- PostgreSQL 15+
- Redis 7+

# Optional (can run in Docker)
- Node.js 18+ (for Playwright)
- npm (for E2E tests)
```

### Python Packages (installed via pip)
```bash
# Core
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
alembic>=1.12.0
pydantic>=2.0.0
redis>=5.0.0
asyncpg>=0.29.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-xdist>=3.3.0
httpx>=0.25.0
factory-boy>=3.3.0
faker>=20.0.0

# Code Quality
ruff>=0.1.0
mypy>=1.7.0
bandit>=1.7.0
safety>=2.3.0
pre-commit>=3.5.0

# Load Testing
locust>=2.17.0
```

### Node Packages (for E2E tests)
```bash
# Testing
@playwright/test>=1.40.0
playwright>=1.40.0
```

## Automation Strategy

### Automated via Scripts
- Database setup and seeding
- Test execution
- Code quality checks
- Docker builds and deployment
- Migration application

### Manual Intervention Required
- Code reviews (logical decisions)
- Architectural decisions
- Security policy reviews
- Production deployment approval
- Database schema changes review

## Efficiency Optimization

### Parallel Execution
```bash
# Multiple test suites
pytest -n auto              # Use all CPU cores

# Multiple services
docker-compose up -d        # All services in background
```

### Caching
```bash
# Docker layer caching
# Pip caching
# npm caching
# Pre-commit caching
```

### Minimal Rebuilds
```bash
# Hot reload for development
uvicorn app.main:app --reload

# Volume mounts for live updates
docker-compose with volume mounts
```

## Expected Tool Usage by Phase

| Phase | Primary Tools | Secondary Tools |
|-------|--------------|-----------------|
| Setup | Write, Bash, git | mkdir, pip, createdb |
| Backend Dev | Write, Edit, pytest | uvicorn, alembic, mypy |
| Frontend Dev | Write, Edit, Read | browser testing |
| Testing | pytest, playwright | Bash, docker-compose |
| Docker | docker, docker-compose | Bash |
| Deployment | docker-compose, git | bash scripts |

---

**Note**: This list represents the comprehensive toolset. In practice, 80% of development will use the top 10-15 tools, while the remaining tools handle edge cases and specific tasks.

**Last Updated**: 2025-01-15

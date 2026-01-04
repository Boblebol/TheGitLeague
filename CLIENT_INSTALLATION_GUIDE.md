# 🐍 GitLeague Client Installation Guide

Complete guide to install and configure the **gitleague-client** — the Python CLI for syncing Git commits to The Git League.

---

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
- [Initial Setup](#initial-setup)
- [Configuration](#configuration)
- [First Sync](#first-sync)
- [Troubleshooting](#troubleshooting)
- [Updating](#updating)

---

## 📦 System Requirements

### Required
- **Python**: 3.10, 3.11, 3.12, or 3.13
- **pip**: Package manager for Python
- **Git**: Installed and accessible from command line
- **GitHub/GitLab/Gitea**: Account with repositories to sync (optional if using local repos)

### Optional
- **SSH key**: For secure Git authentication (recommended over passwords)
- **Virtual environment**: To isolate dependencies (recommended)

### Check Your System

```bash
# Check Python version
python --version
# Output: Python 3.11.x (must be 3.10+)

# Check pip
pip --version
# Output: pip 24.x.x from ...

# Check Git
git --version
# Output: git version 2.4x.x
```

If any are missing, install them:

**macOS:**
```bash
brew install python git
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install python3 python3-pip git
```

**Windows:**
- Download [Python](https://www.python.org/downloads/)
- Download [Git](https://git-scm.com/download/win)
- Ensure both are added to PATH

---

## 🚀 Installation Methods

### Method 1: From PyPI (Recommended) ⭐

The easiest way — install from the official Python Package Index.

**View on PyPI:** https://pypi.org/project/gitleague-client/

```bash
pip install gitleague-client
```

Verify installation:

```bash
gitleague-client --version
# Output: gitleague-client version 0.1.0
```

### Method 2: From Source

For development or if you want the latest code.

```bash
# Clone the repository
git clone https://github.com/Boblebol/TheGitLeague.git
cd TheGitLeague/gitleague-client

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Method 3: Development Installation

If you want to contribute to the client:

```bash
# Clone and enter directory
git clone https://github.com/Boblebol/TheGitLeague.git
cd TheGitLeague/gitleague-client

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Code quality checks
black --check gitleague_client/
ruff check gitleague_client/
mypy gitleague_client/
```

### Virtual Environment (Best Practice)

Isolate the package in a virtual environment:

```bash
# Create virtual environment
python -m venv gitleague-env

# Activate it
# On macOS/Linux:
source gitleague-env/bin/activate
# On Windows:
gitleague-env\Scripts\activate

# Install the client
pip install gitleague-client

# When done, deactivate:
deactivate
```

---

## ⚙️ Initial Setup

### Step 1: Create a GitLeague Account

1. Go to your GitLeague instance (e.g., `http://localhost:3000` for local, or your hosted URL)
2. Sign up with email or magic link
3. Create an account (first user becomes Commissioner)

### Step 2: Generate an API Key

**From the Web UI:**
1. Log in to GitLeague
2. Go to **Settings** → **API Keys**
3. Click **"Create New Key"**
4. Copy the key (displayed once only!)
   - Format: `tgl_xxxxxxxx_yyyyyyyyyyyy`

**Security note:** Store this key securely. Don't commit it to Git.

### Step 3: Initialize Client Configuration

Run the interactive setup:

```bash
gitleague-client init
```

This creates a `repos.yaml` file with prompts:

```
Enter GitLeague API URL [http://localhost:8000]: http://localhost:8000
Enter API Key (or leave empty to use GITLEAGUE_API_KEY env var): tgl_xxx...
Add repositories? [y/n]: y
```

---

## 🔧 Configuration

### repos.yaml Structure

The `repos.yaml` file defines your API settings and repositories:

```yaml
# GitLeague API settings
api:
  url: "http://localhost:8000"
  key: "tgl_xxxxxxxxxxxxx_yyyyyyyyyyyyy"

# Optional: Override default batch size and retries
settings:
  batch_size: 100  # Commits per request (1-1000)
  max_retries: 3   # Retry attempts on error

# Git repositories to sync
repositories:
  # SSH authentication (recommended)
  - name: "backend"
    path: /home/user/projects/my-backend
    # SSH key optional if in default location (~/.ssh/id_ed25519)
    ssh_key: ~/.ssh/id_ed25519

  # HTTPS with token
  - name: "frontend"
    path: /home/user/projects/my-frontend
    git_url: "https://github.com/user/my-frontend.git"
    username: "myusername"
    password_env: "GITHUB_TOKEN"  # Will use $GITHUB_TOKEN env var

  # Public repo (no auth needed)
  - name: "docs"
    path: /home/user/projects/my-docs
```

### Using Environment Variables

For security, store your API key in an environment variable instead of the config file:

```bash
# Set the environment variable
export GITLEAGUE_API_KEY="tgl_xxxxxxxxxxxxx_yyyyyyyyyyyyy"

# In repos.yaml, omit the key or leave it blank
api:
  url: "http://localhost:8000"
  # key: (will use GITLEAGUE_API_KEY env var)
```

### Authentication Methods

#### SSH (Recommended)

Most secure for private repositories:

```yaml
repositories:
  - name: "private-repo"
    path: ~/projects/my-repo
    ssh_key: ~/.ssh/id_ed25519  # Or id_rsa, etc.
```

**Setup SSH key:**
```bash
# Generate a new key (if needed)
ssh-keygen -t ed25519 -C "your-email@example.com"

# Add to GitHub/GitLab:
# 1. Copy public key: cat ~/.ssh/id_ed25519.pub
# 2. Paste into Settings → SSH Keys
```

#### HTTPS with Token

For GitHub/GitLab:

```yaml
repositories:
  - name: "repo"
    path: ~/projects/repo
    git_url: "https://github.com/user/repo.git"
    username: "your-github-username"
    password_env: "GITHUB_TOKEN"  # Uses $GITHUB_TOKEN
```

**Create a personal access token (PAT):**

**GitHub:**
1. Settings → Developer settings → Personal access tokens
2. "Tokens (classic)" → "Generate new token"
3. Scopes: `repo` (or minimal: `public_repo`)
4. Copy the token to environment:
   ```bash
   export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxx"
   ```

**GitLab:**
1. Settings → Access Tokens
2. Create token with `read_repository` scope
3. ```bash
   export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxx"
   ```

#### Public Repositories

No authentication needed:

```yaml
repositories:
  - name: "open-source"
    path: ~/projects/open-source-repo
    # No git_url, ssh_key, or credentials needed
```

---

## ✅ Verify Configuration

Before syncing, test your setup:

```bash
gitleague-client test --config repos.yaml
```

**Successful output:**
```
✓ API connectivity: OK
✓ Backend: backend - OK
✓ Frontend: frontend - OK
✓ Docs: docs - OK

All checks passed! Ready to sync.
```

**Troubleshooting errors:**
- "Invalid API key" → Check `api.key` in repos.yaml
- "Repository not found" → Verify repository path exists
- "SSH permission denied" → Check SSH key setup and GitHub/GitLab settings

---

## 🔄 First Sync

### Preview Changes (Dry Run)

Before actually syncing, see what would be uploaded:

```bash
gitleague-client sync --config repos.yaml --dry-run
```

**Output example:**
```
Scanning repositories...
  Backend: Found 245 new commits
  Frontend: Found 128 new commits
  Docs: Found 32 new commits

Total commits to sync: 405

Would submit 5 batches (100 commits each)
Last batch: 5 commits

Dry run completed. No data sent.
Run again without --dry-run to actually sync.
```

### Perform the Sync

Once you're happy with the preview:

```bash
gitleague-client sync --config repos.yaml
```

**Output example:**
```
Syncing commits...
[████████████████████] 100% - 405/405 commits

Sync completed:
  ✓ Backend: 245 commits
  ✓ Frontend: 128 commits
  ✓ Docs: 32 commits

Total: 405 commits synced in 12.3s
```

### View Results

1. Go to GitLeague web UI
2. Check **Leaderboard** — Players appear with commit stats
3. View **Player Profiles** — Individual statistics
4. Check **Stats** — Project and period breakdowns

---

## 📖 Usage Examples

### Sync Specific Repository

```bash
gitleague-client sync --config repos.yaml --repo backend
```

### Sync with Custom Batch Size

```bash
gitleague-client sync --config repos.yaml --batch-size 500
```

### Verbose Output

```bash
gitleague-client sync --config repos.yaml --verbose
```

### Schedule Regular Syncs

#### macOS/Linux (Cron)

Edit crontab:
```bash
crontab -e
```

Add a job (every hour):
```bash
0 * * * * source ~/.bashrc && gitleague-client sync --config ~/repos.yaml
```

Or (every 30 minutes):
```bash
*/30 * * * * /path/to/gitleague-env/bin/gitleague-client sync --config ~/repos.yaml
```

#### Windows (Task Scheduler)

1. Open **Task Scheduler**
2. **Create Basic Task**
3. Set trigger (e.g., "Daily" at 9:00 AM)
4. Set action: Run program
   - Program: `C:\path\to\gitleague-env\Scripts\gitleague-client.exe`
   - Arguments: `sync --config C:\path\to\repos.yaml`

#### Docker (Recommended)

Schedule syncs in a Docker container:

```dockerfile
FROM python:3.11-slim

RUN pip install gitleague-client

COPY repos.yaml /app/repos.yaml

# Run every hour
CMD ["sh", "-c", "while true; do gitleague-client sync --config /app/repos.yaml && sleep 3600; done"]
```

---

## 🔍 Troubleshooting

### "gitleague-client: command not found"

**Problem:** CLI not installed or not in PATH

**Solutions:**
```bash
# Reinstall
pip install --force-reinstall gitleague-client

# Or, verify installation
python -m gitleague_client.cli --version

# Or, use full path to virtual environment
/path/to/venv/bin/gitleague-client --version
```

### "Invalid API key"

**Problem:** API key is wrong or expired

**Solutions:**
```bash
# Verify key in repos.yaml (should be "tgl_...")
cat repos.yaml | grep key

# Regenerate in GitLeague web UI:
# Settings → API Keys → Create New Key
# Copy and update repos.yaml

# Or use environment variable
export GITLEAGUE_API_KEY="tgl_xxx..."
gitleague-client sync --config repos.yaml
```

### "Repository not found" or "No such file or directory"

**Problem:** Repository path doesn't exist or is incorrect

**Solutions:**
```bash
# Check path exists
ls -la ~/projects/my-backend

# Update repos.yaml with correct path
# Use absolute paths, not relative (~/my-project instead of ./my-project)

# Verify with test command
gitleague-client test --config repos.yaml
```

### "SSH permission denied"

**Problem:** SSH key not accessible or not authorized

**Solutions:**
```bash
# Check key exists
ls -la ~/.ssh/id_ed25519

# Add key to SSH agent
ssh-add ~/.ssh/id_ed25519

# Test SSH connection
ssh -T git@github.com
# Output: Hi username! You've successfully authenticated...

# Add public key to GitHub/GitLab:
cat ~/.ssh/id_ed25519.pub  # Copy this
# GitHub: Settings → SSH Keys → Add key
# GitLab: Settings → SSH Keys → Add key
```

### "No new commits found"

**Problem:** Client finds no new commits to sync

**Possible reasons:**
- All commits already synced (first sync was complete)
- Repository has no commits in the time period
- Wrong repository path

**Solutions:**
```bash
# Check git log
cd /path/to/repo
git log --oneline | head -10

# Force resync from web UI:
# GitLeague → Settings → Repositories → Reset sync state

# Then re-run
gitleague-client sync --config repos.yaml
```

### "Cannot connect to API"

**Problem:** Can't reach GitLeague server

**Troubleshooting:**
```bash
# Check URL and connectivity
curl -v http://localhost:8000/health

# For remote servers
curl -v https://your-gitleague.com/health

# Verify repos.yaml
cat repos.yaml | grep url

# Check firewall/network
ping localhost:8000
```

### "Out of memory" on large repositories

**Problem:** Too many commits at once

**Solutions:**
```bash
# Reduce batch size
gitleague-client sync --config repos.yaml --batch-size 10

# Or sync repositories separately
gitleague-client sync --config repos.yaml --repo backend
gitleague-client sync --config repos.yaml --repo frontend
```

---

## 🔄 Updating

### Check Current Version

```bash
gitleague-client --version
```

### Update to Latest

```bash
pip install --upgrade gitleague-client
```

### What's New

Check the [CHANGELOG](https://github.com/Boblebol/TheGitLeague/blob/main/gitleague-client/CHANGELOG.md) for release notes.

---

## 🆘 Getting Help

- **Documentation**: [gitleague-client README](./gitleague-client/README.md)
- **Issues**: [GitHub Issues](https://github.com/Boblebol/TheGitLeague/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Boblebol/TheGitLeague/discussions)

---

## ✨ Next Steps

1. ✅ Install the client
2. ✅ Create repos.yaml configuration
3. ✅ Test with `gitleague-client test`
4. ✅ Perform initial sync with `--dry-run`
5. ✅ Schedule regular syncs (cron, Task Scheduler, etc.)
6. ✨ Watch your Git stats appear in GitLeague!

**Ready?** Run:
```bash
gitleague-client init
```

---

**Happy syncing! 🚀**

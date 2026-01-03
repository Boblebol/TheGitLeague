# GitLeague Client

Push commits from your local Git repositories to [GitLeague](https://thegitleague.com).

## Features

- **Push-based synchronization**: Your local repository data stays on your machine
- **PAT tokens are local**: GitHub/GitLab tokens never leave your computer
- **Batch processing**: Efficiently sync multiple repositories and commits
- **Retry logic**: Automatic retries with exponential backoff
- **YAML configuration**: Simple, readable configuration format
- **Multiple auth methods**: SSH, HTTPS with tokens, or public repos
- **Dry-run mode**: Preview what would be synced before sending data

## Installation

```bash
pip install gitleague-client
```

Or from source:

```bash
git clone https://github.com/thegitleague/gitleague-client
cd gitleague-client
pip install -e .
```

## Quick Start

### 1. Get Your API Key

1. Log in to [GitLeague](https://thegitleague.com)
2. Go to Settings → API Keys
3. Create a new API key
4. Copy the key (shown only once!)

### 2. Create Configuration File

Generate a template:

```bash
gitleague-client init
```

This creates `repos.yaml`. Edit it to add your repositories:

```yaml
api_url: "https://api.thegitleague.com"
# api_key: "tgl_xxx_yyy"  # Or use GITLEAGUE_API_KEY env var

projects:
  - name: "My Project"
    project_id: "PROJECT_ID"  # From GitLeague web UI
    repos:
      - path: "~/code/my-repo"
        git_url: "git@github.com:user/my-repo.git"
        ssh_key: "~/.ssh/id_ed25519"
```

### 3. Test Connection

```bash
gitleague-client test --config repos.yaml
```

### 4. Sync Commits

```bash
# Preview what would be synced
gitleague-client sync --config repos.yaml --dry-run

# Actually sync
gitleague-client sync --config repos.yaml
```

## Configuration

### API Key

Set your API key in one of two ways:

```yaml
# Method 1: In config file (not recommended - don't commit!)
api_key: "tgl_xxxxxxxx_yyyyyyyyyyyyyyyyyyyyyyyyyyyy"
```

```bash
# Method 2: Environment variable (recommended)
export GITLEAGUE_API_KEY="tgl_xxxxxxxx_yyyyyyyyyyyyyyyyyyyyyyyyyyyy"
gitleague-client sync
```

### Authentication Methods

```yaml
repos:
  # SSH with key
  - path: "~/repo1"
    git_url: "git@github.com:user/repo1.git"
    ssh_key: "~/.ssh/id_ed25519"

  # HTTPS with personal access token
  - path: "~/repo2"
    git_url: "https://github.com/user/repo2.git"
    username: "myuser"
    password_env: "GITHUB_TOKEN"

  # Public repo (no auth)
  - path: "~/repo3"
    git_url: "https://github.com/user/repo3.git"
```

### Settings

```yaml
api_url: "https://api.thegitleague.com"  # API endpoint
batch_size: 100                           # Commits per request (1-1000)
max_retries: 3                            # Retries on errors
```

## Usage

### Sync All Repositories

```bash
gitleague-client sync --config repos.yaml
```

### Dry Run (Preview)

```bash
gitleague-client sync --config repos.yaml --dry-run
```

### Test API Connection

```bash
gitleague-client test --config repos.yaml
```

### Generate Template Config

```bash
gitleague-client init --config my-config.yaml
```

## How It Works

1. **Config Loading**: Reads YAML configuration with repository paths and credentials
2. **Git Scanning**: Extracts commits from local repositories since last sync
3. **Batching**: Groups commits into batches (up to 1000)
4. **API Push**: Sends commits to GitLeague API via HTTPS
5. **Deduplication**: API skips commits that already exist
6. **Status Update**: Tracks sync status for resume capability

### Data Flow

```
Local Git Repos
       ↓
Git Scanner (extract commits)
       ↓
API Client (batch & send)
       ↓
GitLeague API (/sync/projects/{id}/repos/{id}/commits)
       ↓
GitLeague Database
```

## Security

- **PAT tokens stay local**: Only your API key is sent to GitLeague
- **HTTPS required**: All API communication is encrypted
- **API key rotation**: You can revoke API keys instantly from the web UI
- **No token storage**: Credentials are never saved in the client
- **Audit logging**: All syncs are logged on the server

## Troubleshooting

### "Invalid API key"

- Check that `GITLEAGUE_API_KEY` is set correctly
- Or verify `api_key` in `repos.yaml`
- Regenerate the key from GitLeague web UI if needed

### "Repository not found"

- Verify the repository path exists locally
- Ensure the `project_id` matches your GitLeague project
- Check that the repository is configured as `push_client` (not `pull_celery`)

### "No new commits"

- The client uses the `last_ingested_sha` to find new commits
- First sync may be slow if repository has many commits
- You can force a resync from the web UI

### SSH Key Issues

- Ensure SSH agent is running: `ssh-add ~/.ssh/id_ed25519`
- Or use HTTPS authentication instead

## Development

### Install with dev dependencies

```bash
pip install -e ".[dev]"
```

### Run tests

```bash
pytest tests/
```

### Code quality

```bash
black gitleague_client/
ruff check gitleague_client/
mypy gitleague_client/
```

## Architecture

```
gitleague_client/
├── __init__.py           # Package metadata
├── exceptions.py         # Custom exceptions
├── config.py            # YAML config loading & validation
├── git_scanner.py       # Git repository scanning
├── api_client.py        # API client with retry logic
├── sync.py              # Sync orchestration
└── cli.py               # CLI entry point
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run code quality checks
5. Submit a pull request

## License

MIT - See LICENSE file

## Support

- Documentation: https://docs.thegitleague.com/client
- Issues: https://github.com/thegitleague/gitleague-client/issues
- Email: hello@thegitleague.com

"""Command-line interface for GitLeague Client."""

import sys

import click

from gitleague_client import __version__
from gitleague_client.config import ConfigLoader
from gitleague_client.exceptions import ConfigError, GitLeagueError
from gitleague_client.sync import SyncOrchestrator


@click.group()
@click.version_option(version=__version__)
def cli():
    """GitLeague Client - Push commits to GitLeague."""
    pass


@cli.command()
@click.option(
    "--config",
    default="repos.yaml",
    help="Path to configuration file (default: repos.yaml)",
    type=click.Path(exists=False),
)
def init(config):
    """Generate a template configuration file."""
    from pathlib import Path

    config_path = Path(config)

    if config_path.exists():
        click.echo(f"Error: {config} already exists", err=True)
        sys.exit(1)

    template = """# GitLeague Client Configuration
# Save this as repos.yaml and customize it

api_url: "https://api.thegitleague.com"
# api_key: "tgl_xxx_yyy"  # Or set GITLEAGUE_API_KEY environment variable
batch_size: 100
max_retries: 3

projects:
  - name: "My Project"
    project_id: "PROJECT_UUID_HERE"  # Get this from GitLeague web UI
    repos:
      - path: "~/code/repo1"
        git_url: "git@github.com:myorg/repo1.git"
        ssh_key: "~/.ssh/id_ed25519"  # For SSH authentication

      - path: "~/code/repo2"
        git_url: "https://github.com/myorg/repo2.git"
        username: "myuser"
        password_env: "GITHUB_TOKEN"  # Environment variable with token
"""

    config_path.write_text(template)
    click.echo(f"✓ Created template configuration: {config}")
    click.echo(f"  Edit {config} and add your API key and project details")


@cli.command()
@click.option(
    "--config",
    default="repos.yaml",
    help="Path to configuration file",
    type=click.Path(exists=True),
)
def test(config):
    """Test connection to GitLeague API."""
    try:
        click.echo("Loading configuration...")
        client_config = ConfigLoader.load(config)

        click.echo("Testing API connection...")
        orchestrator = SyncOrchestrator(client_config)

        if orchestrator.test_connection():
            click.echo(f"✓ API Key: {client_config.api_key[:10]}***")
            click.echo(f"✓ Projects: {len(client_config.projects)}")
            for project in client_config.projects:
                click.echo(f"  - {project.name} ({len(project.repos)} repos)")
            sys.exit(0)
        else:
            sys.exit(1)

    except ConfigError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)
    except GitLeagueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    default="repos.yaml",
    help="Path to configuration file",
    type=click.Path(exists=True),
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be synced without sending data",
)
@click.option(
    "--api-key",
    default=None,
    envvar="GITLEAGUE_API_KEY",
    help="API key (or GITLEAGUE_API_KEY env var)",
)
def sync(config, dry_run, api_key):
    """Synchronize commits to GitLeague."""
    try:
        click.echo("Loading configuration...")
        client_config = ConfigLoader.load(config)

        # Override API key if provided
        if api_key:
            client_config.api_key = api_key

        click.echo()
        orchestrator = SyncOrchestrator(client_config, dry_run=dry_run)

        if not orchestrator.test_connection():
            sys.exit(1)

        click.echo()
        success = orchestrator.sync_all()

        sys.exit(0 if success else 1)

    except ConfigError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)
    except GitLeagueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()

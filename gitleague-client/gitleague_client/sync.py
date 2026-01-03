"""Synchronization orchestrator."""

from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from gitleague_client.api_client import GitLeagueAPIClient
from gitleague_client.config import ClientConfig, ProjectConfig, RepositoryConfig
from gitleague_client.git_scanner import GitScanner
from gitleague_client.exceptions import GitScanError, APIError


class SyncOrchestrator:
    """Orchestrate synchronization of repositories."""

    def __init__(self, config: ClientConfig, dry_run: bool = False):
        """
        Initialize sync orchestrator.

        Args:
            config: Client configuration
            dry_run: If True, don't actually send data to API
        """
        self.config = config
        self.dry_run = dry_run
        self.console = Console()
        self.api_client = GitLeagueAPIClient(
            api_url=config.api_url,
            api_key=config.api_key,
            max_retries=config.max_retries,
        )

    def test_connection(self) -> bool:
        """
        Test connection to GitLeague API.

        Returns:
            True if connection successful
        """
        with self.console.status("Testing connection to GitLeague API..."):
            try:
                self.api_client.test_connection()
                self.console.print("[green]✓[/green] Connected to GitLeague API")
                return True
            except Exception as e:
                self.console.print(f"[red]✗[/red] Connection failed: {e}")
                return False

    def sync_project(self, project: ProjectConfig) -> bool:
        """
        Sync all repositories in a project.

        Args:
            project: Project configuration

        Returns:
            True if all repos synced successfully

        Raises:
            APIError: If API communication fails
        """
        self.console.print(f"\n[bold blue]Project: {project.name}[/bold blue]")

        all_success = True
        for repo_config in project.repos:
            try:
                success = self.sync_repo(project.project_id, repo_config)
                if not success:
                    all_success = False
            except Exception as e:
                self.console.print(f"[red]Error syncing {repo_config.path}: {e}[/red]")
                all_success = False

        return all_success

    def sync_repo(self, project_id: str, repo_config: RepositoryConfig) -> bool:
        """
        Sync a single repository.

        Args:
            project_id: Project ID
            repo_config: Repository configuration

        Returns:
            True if sync successful

        Raises:
            GitScanError: If Git operation fails
            APIError: If API communication fails
        """
        self.console.print(f"\n  [bold cyan]Repository: {repo_config.path}[/bold cyan]")

        # Initialize Git scanner
        try:
            scanner = GitScanner(repo_config.path)
        except GitScanError as e:
            self.console.print(f"  [red]✗ Failed to open repository: {e}[/red]")
            return False

        # Validate branch
        if not scanner.validate_branch():
            self.console.print(f"  [red]✗ Branch 'main' not found[/red]")
            return False

        # Get repo status from API
        try:
            status = self.api_client.get_repo_status(project_id, repo_config.git_url)
            last_sha = status.get("last_ingested_sha")
        except APIError as e:
            self.console.print(f"  [red]✗ Failed to get repo status: {e}[/red]")
            return False

        # Scan commits
        with self.console.status("  Scanning commits..."):
            try:
                commits = scanner.get_commits_since_sha(last_sha, self.config.batch_size)
            except GitScanError as e:
                self.console.print(f"  [red]✗ Failed to scan commits: {e}[/red]")
                return False

        if not commits:
            self.console.print("  [yellow]No new commits[/yellow]")
            return True

        self.console.print(f"  Found {len(commits)} new commits")

        # In dry-run mode, just show what would be synced
        if self.dry_run:
            self.console.print("  [yellow][DRY RUN][/yellow] Would sync commits:")
            for i, commit in enumerate(commits, 1):
                self.console.print(f"    {i}. {commit.sha[:7]} - {commit.message_title}")
            return True

        # Sync commits in batches
        return self._sync_commits_batched(project_id, repo_config.git_url, commits)

    def _sync_commits_batched(
        self, project_id: str, repo_id: str, commits
    ) -> bool:
        """
        Sync commits in batches to API.

        Args:
            project_id: Project ID
            repo_id: Repository ID
            commits: List of CommitData objects

        Returns:
            True if all batches synced successfully
        """
        total = len(commits)
        batches = [
            commits[i : i + self.config.batch_size]
            for i in range(0, total, self.config.batch_size)
        ]

        all_success = True

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            for batch_num, batch in enumerate(batches, 1):
                task = progress.add_task(
                    f"  Uploading batch {batch_num}/{len(batches)}...", total=None
                )

                try:
                    # Convert to dicts for API
                    commit_dicts = [c.to_dict() for c in batch]

                    # Send to API
                    result = self.api_client.sync_commits(
                        project_id,
                        repo_id,
                        commit_dicts,
                        client_version="0.1.0",
                    )

                    inserted = result.get("inserted", 0)
                    skipped = result.get("skipped", 0)
                    errors = result.get("errors", 0)

                    progress.stop()

                    if errors > 0:
                        self.console.print(
                            f"  [yellow]Batch {batch_num}: {inserted} inserted, {skipped} skipped, {errors} errors[/yellow]"
                        )
                        all_success = False
                    else:
                        self.console.print(
                            f"  [green]✓ Batch {batch_num}: {inserted} inserted, {skipped} skipped[/green]"
                        )

                except APIError as e:
                    progress.stop()
                    self.console.print(f"  [red]✗ Batch {batch_num} failed: {e}[/red]")
                    all_success = False

        return all_success

    def sync_all(self) -> bool:
        """
        Sync all projects and repositories.

        Returns:
            True if all syncs successful
        """
        self.console.print("[bold]GitLeague Client[/bold] - Synchronizing repositories...")

        all_success = True
        for project in self.config.projects:
            try:
                success = self.sync_project(project)
                if not success:
                    all_success = False
            except Exception as e:
                self.console.print(f"[red]Error syncing project {project.name}: {e}[/red]")
                all_success = False

        # Final summary
        if all_success:
            self.console.print("\n[green bold]✓ All repositories synchronized successfully![/green bold]")
        else:
            self.console.print("\n[yellow bold]⚠ Some repositories had errors. See above for details.[/yellow bold]")

        return all_success

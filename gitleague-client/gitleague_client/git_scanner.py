"""Git repository scanning and commit extraction."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from git import Repo, GitCommandError
from git.objects.commit import Commit as GitCommit

from gitleague_client.exceptions import GitScanError


@dataclass
class CommitData:
    """Extracted commit data."""

    sha: str
    author_name: str
    author_email: str
    committer_name: str
    committer_email: str
    commit_date: datetime
    message_title: str
    message_body: Optional[str]
    additions: int
    deletions: int
    files_changed: int
    is_merge: bool
    parent_count: int

    def to_dict(self) -> dict:
        """Convert to dictionary for API submission."""
        return {
            "sha": self.sha,
            "author_name": self.author_name,
            "author_email": self.author_email,
            "committer_name": self.committer_name,
            "committer_email": self.committer_email,
            "commit_date": self.commit_date.isoformat(),
            "message_title": self.message_title,
            "message_body": self.message_body,
            "additions": self.additions,
            "deletions": self.deletions,
            "files_changed": self.files_changed,
            "is_merge": self.is_merge,
            "parent_count": self.parent_count,
        }


class GitScanner:
    """Scan Git repositories and extract commit metadata."""

    def __init__(self, repo_path: str, branch: str = "main"):
        """
        Initialize Git scanner.

        Args:
            repo_path: Path to local Git repository
            branch: Git branch to scan (default: main)

        Raises:
            GitScanError: If repository not found or invalid
        """
        self.repo_path = repo_path
        self.branch = branch

        try:
            self.repo = Repo(repo_path)
        except Exception as e:
            raise GitScanError(f"Failed to open repository at {repo_path}: {e}")

    def validate_branch(self) -> bool:
        """
        Check if the configured branch exists.

        Returns:
            True if branch exists, False otherwise
        """
        try:
            self.repo.remotes.origin.fetch()
        except Exception:
            pass  # Fetch might fail for local-only repos

        try:
            self.repo.heads[self.branch]
            return True
        except IndexError:
            return False

    def get_latest_commit_sha(self) -> Optional[str]:
        """
        Get the latest commit SHA on the configured branch.

        Returns:
            SHA of latest commit, or None if no commits

        Raises:
            GitScanError: If branch doesn't exist or error occurs
        """
        try:
            return self.repo.heads[self.branch].commit.hexsha
        except IndexError:
            raise GitScanError(f"Branch '{self.branch}' not found")
        except Exception as e:
            raise GitScanError(f"Failed to get latest commit: {e}")

    def get_commits_since_sha(
        self, last_sha: Optional[str] = None, max_commits: int = 1000
    ) -> List[CommitData]:
        """
        Get commits since a specific SHA.

        Args:
            last_sha: Start point (exclusive). If None, get all commits
            max_commits: Maximum commits to return

        Returns:
            List of CommitData objects

        Raises:
            GitScanError: If error occurs during scanning
        """
        try:
            # Get commits on the branch
            if last_sha:
                # Get commits after last_sha
                rev_range = f"{last_sha}..{self.branch}"
                commits = list(self.repo.iter_commits(rev_range))
            else:
                # Get all commits on the branch
                commits = list(self.repo.iter_commits(self.branch))

            # Limit to max_commits (newest first, so reverse)
            commits = list(reversed(commits))[-max_commits:]

            commits_data = []
            for commit in commits:
                try:
                    commit_data = self._extract_commit_data(commit)
                    commits_data.append(commit_data)
                except Exception as e:
                    raise GitScanError(f"Failed to extract commit {commit.hexsha}: {e}")

            return commits_data

        except GitScanError:
            raise
        except Exception as e:
            raise GitScanError(f"Failed to scan commits: {e}")

    def _extract_commit_data(self, git_commit: GitCommit) -> CommitData:
        """
        Extract metadata from a GitPython Commit object.

        Args:
            git_commit: GitPython commit object

        Returns:
            CommitData with extracted information
        """
        # Parse message (first line is title, rest is body)
        message = git_commit.message.strip()
        lines = message.split("\n", 1)
        message_title = lines[0][:500]  # Limit to 500 chars
        message_body = lines[1] if len(lines) > 1 else None

        # Get stats
        try:
            stats = git_commit.stats.total
            additions = stats.get("insertions", 0)
            deletions = stats.get("deletions", 0)
            files_changed = stats.get("files", 0)
        except Exception:
            # Fallback if stats fail
            additions = 0
            deletions = 0
            files_changed = 0

        # Check if merge commit
        is_merge = len(git_commit.parents) > 1

        return CommitData(
            sha=git_commit.hexsha,
            author_name=git_commit.author.name or "Unknown",
            author_email=git_commit.author.email or "unknown@unknown.local",
            committer_name=git_commit.committer.name or "Unknown",
            committer_email=git_commit.committer.email or "unknown@unknown.local",
            commit_date=datetime.fromtimestamp(git_commit.committed_date),
            message_title=message_title,
            message_body=message_body,
            additions=additions,
            deletions=deletions,
            files_changed=files_changed,
            is_merge=is_merge,
            parent_count=len(git_commit.parents),
        )

"""Git utilities for extracting commit metadata."""

import os
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import git
from git import Repo as GitRepo

from app.core.config import settings


def extract_commit_metadata(commit: git.Commit) -> Dict:
    """
    Extract metadata from a GitPython commit object.

    Args:
        commit: GitPython Commit object

    Returns:
        Dictionary with commit metadata
    """
    # Get stats (additions, deletions, files_changed)
    stats = commit.stats.total

    # Split message into title and body
    message_lines = commit.message.split("\n", 1)
    message_title = message_lines[0][:500]  # Cap at 500 chars
    message_body = message_lines[1] if len(message_lines) > 1 else None

    return {
        "sha": commit.hexsha,
        "author_name": commit.author.name,
        "author_email": commit.author.email.lower(),  # Normalize email
        "committer_name": commit.committer.name,
        "committer_email": commit.committer.email.lower(),  # Normalize email
        "commit_date": datetime.fromtimestamp(commit.committed_date),
        "message_title": message_title,
        "message_body": message_body,
        "additions": stats.get("insertions", 0),
        "deletions": stats.get("deletions", 0),
        "files_changed": stats.get("files", 0),
        "is_merge": len(commit.parents) > 1,
        "parent_count": len(commit.parents),
    }


def clone_or_fetch_repo(
    remote_url: str,
    bare_path: str,
    credentials_encrypted: Optional[str] = None,
) -> GitRepo:
    """
    Clone a repository if it doesn't exist, or fetch updates if it does.

    Args:
        remote_url: Git remote URL
        bare_path: Path to store bare repository
        credentials_encrypted: Optional encrypted credentials

    Returns:
        GitRepo object

    Raises:
        git.GitCommandError: If clone/fetch fails
    """
    from app.core.security import decrypt_credentials
    import json

    env = os.environ.copy()

    # Handle credentials
    if credentials_encrypted:
        credentials = json.loads(decrypt_credentials(credentials_encrypted))

        # For HTTPS with token
        if "token" in credentials and "://" in remote_url:
            protocol, rest = remote_url.split("://", 1)
            remote_url = f"{protocol}://{credentials['token']}@{rest}"

        # For SSH with private key
        elif "private_key" in credentials:
            # Create temporary key file
            temp_dir = tempfile.mkdtemp()
            key_file = os.path.join(temp_dir, "id_rsa")
            with open(key_file, "w") as f:
                f.write(credentials["private_key"])
            os.chmod(key_file, 0o600)
            env["GIT_SSH_COMMAND"] = f"ssh -i {key_file} -o StrictHostKeyChecking=no"

    # Clone or fetch
    if not os.path.exists(bare_path):
        # Clone as bare repository
        repo = GitRepo.clone_from(remote_url, bare_path, bare=True, env=env)
    else:
        # Open existing repo and fetch
        repo = GitRepo(bare_path)
        repo.remote("origin").fetch(env=env)

    return repo


def get_commits_since_sha(
    repo: GitRepo,
    branch: str,
    last_sha: Optional[str] = None,
) -> List[git.Commit]:
    """
    Get commits since a specific SHA on a branch.

    Args:
        repo: GitRepo object
        branch: Branch name
        last_sha: SHA to start from (exclusive), or None for all commits

    Returns:
        List of Commit objects (newest first)
    """
    if last_sha:
        # Get commits between last_sha and branch tip
        revision_range = f"{last_sha}..{branch}"
    else:
        # Get all commits on branch
        revision_range = branch

    commits = list(repo.iter_commits(revision_range))
    return commits


def get_latest_commit_sha(repo: GitRepo, branch: str) -> str:
    """
    Get the latest commit SHA on a branch.

    Args:
        repo: GitRepo object
        branch: Branch name

    Returns:
        Commit SHA (hexsha)
    """
    return repo.commit(branch).hexsha


def get_repo_path(repo_id: str) -> str:
    """
    Get the file system path for a repository's bare clone.

    Args:
        repo_id: Repository ID

    Returns:
        Absolute path to bare repository
    """
    repos_dir = settings.REPOS_STORAGE_PATH
    os.makedirs(repos_dir, exist_ok=True)
    return os.path.join(repos_dir, f"{repo_id}.git")


def validate_branch_exists(repo: GitRepo, branch: str) -> Tuple[bool, Optional[List[str]]]:
    """
    Check if a branch exists in the repository.

    Args:
        repo: GitRepo object
        branch: Branch name to check

    Returns:
        Tuple of (exists, available_branches)
    """
    try:
        # Get all branch names
        branches = [ref.name for ref in repo.branches]

        # For remote refs, also check remote branches
        if hasattr(repo, "remote"):
            remote_branches = [ref.name.replace("origin/", "") for ref in repo.remote().refs]
            branches.extend(remote_branches)

        branches = list(set(branches))  # Remove duplicates

        return branch in branches, branches
    except Exception:
        return False, None

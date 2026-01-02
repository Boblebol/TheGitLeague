"""NBA-style scoring utilities for Git commits."""

import json
from dataclasses import dataclass
from typing import Dict

from app.models.commit import Commit


@dataclass
class ScoringCoefficients:
    """Scoring coefficients for NBA metrics calculation."""

    additions_weight: float = 1.0
    deletions_weight: float = 0.6
    commit_base: int = 10
    multi_file_bonus: int = 5
    fix_bonus: int = 15
    wip_penalty: int = -10
    max_additions_cap: int = 1000
    max_deletions_cap: int = 1000

    @classmethod
    def from_dict(cls, data: Dict) -> "ScoringCoefficients":
        """
        Create ScoringCoefficients from dictionary.

        Args:
            data: Dictionary with coefficient values

        Returns:
            ScoringCoefficients instance
        """
        return cls(
            additions_weight=float(data.get("additions_weight", 1.0)),
            deletions_weight=float(data.get("deletions_weight", 0.6)),
            commit_base=int(data.get("commit_base", 10)),
            multi_file_bonus=int(data.get("multi_file_bonus", 5)),
            fix_bonus=int(data.get("fix_bonus", 15)),
            wip_penalty=int(data.get("wip_penalty", -10)),
            max_additions_cap=int(data.get("max_additions_cap", 1000)),
            max_deletions_cap=int(data.get("max_deletions_cap", 1000)),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ScoringCoefficients":
        """
        Create ScoringCoefficients from JSON string.

        Args:
            json_str: JSON string with coefficient values

        Returns:
            ScoringCoefficients instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "additions_weight": self.additions_weight,
            "deletions_weight": self.deletions_weight,
            "commit_base": self.commit_base,
            "multi_file_bonus": self.multi_file_bonus,
            "fix_bonus": self.fix_bonus,
            "wip_penalty": self.wip_penalty,
            "max_additions_cap": self.max_additions_cap,
            "max_deletions_cap": self.max_deletions_cap,
        }


def calculate_pts(commit: Commit, coeffs: ScoringCoefficients) -> int:
    """
    Calculate Points (PTS) for a commit.

    Points = Base + capped additions * weight

    Example:
      commit.additions = 1500
      capped = min(1500, 1000) = 1000
      pts = 10 + (1000 * 1.0) = 1010

    Args:
        commit: Commit object
        coeffs: Scoring coefficients

    Returns:
        Points score
    """
    base = coeffs.commit_base
    capped_additions = min(commit.additions, coeffs.max_additions_cap)
    return int(base + (capped_additions * coeffs.additions_weight))


def calculate_reb(commit: Commit, coeffs: ScoringCoefficients) -> int:
    """
    Calculate Rebounds (REB) for a commit.

    Rebounds = Capped deletions * weight (cleanup work)

    Example:
      commit.deletions = 500
      reb = 500 * 0.6 = 300

    Args:
        commit: Commit object
        coeffs: Scoring coefficients

    Returns:
        Rebounds score
    """
    capped_deletions = min(commit.deletions, coeffs.max_deletions_cap)
    return int(capped_deletions * coeffs.deletions_weight)


def calculate_ast(commit: Commit, coeffs: ScoringCoefficients) -> int:
    """
    Calculate Assists (AST) for a commit.

    Assists = Multi-file bonus (collaboration proxy)

    Example:
      commit.files_changed = 5 → ast = 5
      commit.files_changed = 2 → ast = 0

    Args:
        commit: Commit object
        coeffs: Scoring coefficients

    Returns:
        Assists score
    """
    if commit.files_changed > 3:
        return coeffs.multi_file_bonus
    return 0


def calculate_blk(commit: Commit, coeffs: ScoringCoefficients) -> int:
    """
    Calculate Blocks (BLK) for a commit.

    Blocks = Fix/bug commits (defensive work)

    Detects: "fix", "bug", "hotfix", "revert" in message

    Args:
        commit: Commit object
        coeffs: Scoring coefficients

    Returns:
        Blocks score
    """
    message = commit.message_title.lower()
    fix_keywords = ['fix', 'bug', 'hotfix', 'revert']

    if any(word in message for word in fix_keywords):
        return coeffs.fix_bonus
    return 0


def calculate_tov(commit: Commit, coeffs: ScoringCoefficients) -> int:
    """
    Calculate Turnovers (TOV) for a commit.

    Turnovers = WIP/debug commits (negative)

    Detects: "wip", "tmp", "debug", "test" in message

    Args:
        commit: Commit object
        coeffs: Scoring coefficients

    Returns:
        Turnovers score (negative)
    """
    message = commit.message_title.lower()
    wip_keywords = ['wip', 'tmp', 'debug', 'test']

    if any(word in message for word in wip_keywords):
        return coeffs.wip_penalty
    return 0


def calculate_impact_score(pts: int, reb: int, ast: int, blk: int, tov: int) -> float:
    """
    Calculate composite impact score.

    Formula: PTS*1.0 + REB*0.6 + AST*0.8 + BLK*1.2 + TOV*0.7

    Args:
        pts: Points
        reb: Rebounds
        ast: Assists
        blk: Blocks
        tov: Turnovers

    Returns:
        Impact score (float)
    """
    return (
        pts * 1.0 +
        reb * 0.6 +
        ast * 0.8 +
        blk * 1.2 +
        tov * 0.7
    )


def calculate_all_metrics(commit: Commit, coeffs: ScoringCoefficients) -> Dict[str, int | float]:
    """
    Calculate all NBA metrics for a commit.

    Args:
        commit: Commit object
        coeffs: Scoring coefficients

    Returns:
        Dictionary with all metrics
    """
    pts = calculate_pts(commit, coeffs)
    reb = calculate_reb(commit, coeffs)
    ast = calculate_ast(commit, coeffs)
    blk = calculate_blk(commit, coeffs)
    tov = calculate_tov(commit, coeffs)
    impact = calculate_impact_score(pts, reb, ast, blk, tov)

    return {
        "pts": pts,
        "reb": reb,
        "ast": ast,
        "blk": blk,
        "tov": tov,
        "impact_score": impact,
    }

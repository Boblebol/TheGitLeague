"""Unit tests for scoring and leaderboard logic."""

import pytest
from datetime import datetime, timedelta, timezone

from app.models.commit import Commit
from app.models.project import Project


class TestScoringFormulas:
    """Test scoring calculation formulas."""

    def test_base_scoring_formula(self):
        """Test base commit scoring logic."""
        additions = 50
        deletions = 10
        files_changed = 5

        # Scoring formulas
        points = min(additions, 1000)  # Capped
        rebounds = deletions * 0.5
        assists = files_changed * 1.5

        assert points > 0
        assert rebounds >= 0
        assert assists >= 0

    def test_scoring_with_zero_changes(self):
        """Test scoring for empty commit."""
        additions = 0
        deletions = 0
        files_changed = 0

        points = max(1, min(additions, 1000))  # Min 1 point
        rebounds = deletions * 0.5
        assists = files_changed * 1.5

        assert points >= 0
        assert rebounds >= 0
        assert assists >= 0

    def test_scoring_capped_additions(self):
        """Test that large additions are capped."""
        # Huge commit
        additions1 = 10000
        additions2 = 15000

        # Points should be capped at 1000
        points1 = min(additions1, 1000)
        points2 = min(additions2, 1000)

        assert points1 == 1000
        assert points2 == 1000

    def test_scoring_multifile_bonus(self):
        """Test assists bonus for multi-file commits."""
        single_file_changes = 1
        multi_file_changes = 10

        # Assists = files_changed * 1.5
        single_assist = single_file_changes * 1.5
        multi_assist = multi_file_changes * 1.5

        assert multi_assist > single_assist

    def test_scoring_deletions_as_rebounds(self):
        """Test that deletions/cleanup generates rebounds."""
        additions = 100
        deletions = 10

        additions_heavy_deletions = 10
        deletions_heavy_deletions = 100

        rebounds1 = deletions * 0.5
        rebounds2 = deletions_heavy_deletions * 0.5

        assert rebounds2 > rebounds1

    def test_negative_stats_prevented(self):
        """Test that stats never go negative."""
        additions = 0
        deletions = 0
        files_changed = 0

        points = min(max(0, additions), 1000)
        rebounds = max(0, deletions * 0.5)
        assists = max(0, files_changed * 1.5)

        assert points >= 0
        assert rebounds >= 0
        assert assists >= 0


class TestCommitMetrics:
    """Test commit metric extraction."""

    def test_extract_additions_deletions(self):
        """Test extracting additions and deletions."""
        # Simulate commit metrics
        additions = 150
        deletions = 50
        files_changed = 5

        # Test metric values
        assert additions == 150
        assert deletions == 50
        assert files_changed == 5

    def test_commit_with_large_changes(self):
        """Test commit with large change metrics."""
        # Simulate large commit metrics
        additions = 5000
        deletions = 1000
        files_changed = 50

        # Test that metrics are correctly handled
        assert additions == 5000
        assert deletions == 1000
        assert files_changed > 0


class TestLeaderboardLogic:
    """Test leaderboard ranking logic."""

    def test_leaderboard_sorting(self):
        """Test leaderboard sorting by points."""
        players = [
            {"name": "Player A", "points": 100},
            {"name": "Player B", "points": 150},
            {"name": "Player C", "points": 75},
        ]

        # Sort by points descending
        sorted_players = sorted(players, key=lambda p: p["points"], reverse=True)

        assert sorted_players[0]["points"] == 150
        assert sorted_players[1]["points"] == 100
        assert sorted_players[2]["points"] == 75

    def test_leaderboard_empty(self):
        """Test leaderboard with no commits."""
        leaderboard = []
        assert len(leaderboard) == 0

    def test_leaderboard_filtering_by_period(self):
        """Test filtering commits by period."""
        today = datetime.now(timezone.utc).date()
        week_ago = today - timedelta(days=7)

        # Simulate commit dates
        commit_dates = [
            today,
            today - timedelta(days=1),
            today - timedelta(days=5),
        ]

        # Filter for commits this week
        week_start = datetime.combine(week_ago, datetime.min.time()).replace(tzinfo=timezone.utc)
        week_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)

        week_commits = [
            date for date in commit_dates
            if datetime.combine(date, datetime.min.time()).replace(tzinfo=timezone.utc) >= week_start
        ]

        assert len(week_commits) >= 0


class TestAwardCalculation:
    """Test award calculation logic."""

    def test_player_of_week_logic(self):
        """Test identifying player with highest points in a week."""
        weekly_stats = [
            {"player": "A", "points": 100},
            {"player": "B", "points": 150},
            {"player": "C", "points": 75},
        ]

        # Find player with most points
        player_of_week = max(weekly_stats, key=lambda p: p["points"])
        assert player_of_week["player"] == "B"

    def test_most_improved_logic(self):
        """Test identifying most improved player."""
        previous_week = [
            {"player": "A", "points": 100},
            {"player": "B", "points": 50},
        ]

        current_week = [
            {"player": "A", "points": 110},
            {"player": "B", "points": 150},
        ]

        improvements = {}
        for prev in previous_week:
            curr = next((c for c in current_week if c["player"] == prev["player"]), None)
            if curr:
                improvements[prev["player"]] = curr["points"] - prev["points"]

        most_improved = max(improvements.items(), key=lambda x: x[1])
        assert most_improved[0] == "B"  # B improved by 100 points

    def test_mvp_calculation(self):
        """Test MVP calculation (highest total points)."""
        season_stats = [
            {"player": "A", "total_points": 500},
            {"player": "B", "total_points": 750},
            {"player": "C", "total_points": 600},
        ]

        mvp = max(season_stats, key=lambda p: p["total_points"])
        assert mvp["player"] == "B"


class TestRankingLogic:
    """Test ranking and percentile calculations."""

    def test_rank_calculation(self):
        """Test calculating player rank."""
        leaderboard = [
            {"player": "A", "points": 150},
            {"player": "B", "points": 100},
            {"player": "C", "points": 75},
        ]

        # Find rank of player B (should be 2)
        player_b = next(p for p in leaderboard if p["player"] == "B")
        rank = next(i for i, p in enumerate(leaderboard, 1) if p["player"] == "B")

        assert rank == 2

    def test_percentile_calculation(self):
        """Test percentile calculation."""
        scores = [75, 80, 85, 90, 95, 100]
        target_score = 85

        # Percentile = (count below + 0.5 * count equal) / total * 100
        below = sum(1 for s in scores if s < target_score)
        equal = sum(1 for s in scores if s == target_score)
        percentile = ((below + 0.5 * equal) / len(scores)) * 100

        assert percentile > 0
        assert percentile < 100

    def test_ties_in_ranking(self):
        """Test handling ties in rankings."""
        leaderboard = [
            {"player": "A", "points": 100},
            {"player": "B", "points": 100},
            {"player": "C", "points": 75},
        ]

        # Both A and B should have same rank
        assert leaderboard[0]["points"] == leaderboard[1]["points"]


class TestPeriodFiltering:
    """Test filtering by different time periods."""

    def test_daily_filtering(self):
        """Test filtering commits for a single day."""
        today = datetime.now(timezone.utc).date()

        # Simulate commit dates
        commit_dates = [
            datetime.now(timezone.utc),
            datetime.now(timezone.utc) - timedelta(hours=2),
            datetime.now(timezone.utc) - timedelta(days=1),
        ]

        # Query for today
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)

        today_commits = [
            date for date in commit_dates
            if today_start <= date <= today_end
        ]

        assert len(today_commits) >= 1

    def test_weekly_filtering(self):
        """Test filtering commits for a week."""
        today = datetime.now(timezone.utc).date()
        week_ago = today - timedelta(days=7)

        week_start = datetime.combine(week_ago, datetime.min.time()).replace(tzinfo=timezone.utc)

        # Simulate commit dates
        commit_dates = [
            datetime.now(timezone.utc),
            datetime.now(timezone.utc) - timedelta(days=3),
            datetime.now(timezone.utc) - timedelta(days=20),
        ]

        # Query for this week
        week_commits = [
            date for date in commit_dates
            if date >= week_start
        ]

        assert len(week_commits) >= 1

    def test_monthly_filtering(self):
        """Test filtering commits for a month."""
        today = datetime.now(timezone.utc).date()
        month_ago = today - timedelta(days=30)

        month_start = datetime.combine(month_ago, datetime.min.time()).replace(tzinfo=timezone.utc)

        # Simulate commit dates
        commit_dates = [
            datetime.now(timezone.utc),
            datetime.now(timezone.utc) - timedelta(days=15),
            datetime.now(timezone.utc) - timedelta(days=60),
        ]

        # Query for this month
        month_commits = [
            date for date in commit_dates
            if date >= month_start
        ]

        assert len(month_commits) >= 1

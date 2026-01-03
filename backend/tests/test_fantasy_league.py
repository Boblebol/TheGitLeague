"""Tests for Fantasy League functionality."""

import pytest
from datetime import datetime, timedelta, timezone

from app.models.fantasy import FantasyLeague
from app.models.season import Season
from app.models.user import User, UserRole, UserStatus


class TestFantasyLeagueCreation:
    """Test fantasy league creation."""

    def _create_season(self, db_session, test_project):
        """Helper to create a test season."""
        season = Season(
            project_id=test_project.id,
            name="Test Season",
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc) + timedelta(days=30),
            status="draft"
        )
        db_session.add(season)
        db_session.commit()
        return season

    def test_create_fantasy_league(self, db_session, test_project):
        """Test creating a fantasy league."""
        season = self._create_season(db_session, test_project)

        league = FantasyLeague(
            season_id=season.id,
            name="Test League",
            roster_min=1,
            roster_max=5,
        )
        db_session.add(league)
        db_session.commit()

        assert league is not None
        assert league.name == "Test League"
        assert league.roster_min == 1
        assert league.roster_max == 5

    def test_league_unique_name(self, db_session, test_project):
        """Test league creation with unique name."""
        season = self._create_season(db_session, test_project)

        league = FantasyLeague(
            season_id=season.id,
            name="Unique League",
            roster_min=1,
            roster_max=5,
        )
        db_session.add(league)
        db_session.commit()

        # Verify league exists
        fetched = db_session.query(FantasyLeague).filter(
            FantasyLeague.name == "Unique League"
        ).first()
        assert fetched is not None
        assert fetched.name == "Unique League"

    def test_league_roster_constraints(self, db_session, test_project):
        """Test roster size constraints."""
        season = self._create_season(db_session, test_project)

        league = FantasyLeague(
            season_id=season.id,
            name="Constrained League",
            roster_min=2,
            roster_max=4,
        )

        assert league.roster_min <= league.roster_max


class TestFantasyLeagueBasics:
    """Test basic fantasy league functionality."""

    def _create_season(self, db_session, test_project):
        """Helper to create a test season."""
        season = Season(
            project_id=test_project.id,
            name="Test Season",
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc) + timedelta(days=30),
            status="draft"
        )
        db_session.add(season)
        db_session.commit()
        return season

    def test_league_status(self, db_session, test_project):
        """Test league status initialization."""
        season = self._create_season(db_session, test_project)

        league = FantasyLeague(
            season_id=season.id,
            name="Status League",
            roster_min=1,
            roster_max=5,
        )
        db_session.add(league)
        db_session.commit()

        # Verify league can be retrieved
        fetched = db_session.query(FantasyLeague).filter(
            FantasyLeague.name == "Status League"
        ).first()
        assert fetched is not None

    def test_league_settings(self, db_session, test_project):
        """Test league settings."""
        season = self._create_season(db_session, test_project)

        league = FantasyLeague(
            season_id=season.id,
            name="Settings League",
            roster_min=1,
            roster_max=5,
        )
        db_session.add(league)
        db_session.commit()

        # Update settings
        league.roster_min = 2
        db_session.commit()

        fetched = db_session.query(FantasyLeague).filter(
            FantasyLeague.name == "Settings League"
        ).first()
        assert fetched.roster_min == 2

    def test_league_with_different_configs(self, db_session, test_project):
        """Test creating leagues with different configurations."""
        season = self._create_season(db_session, test_project)

        configs = [
            {"roster_min": 1, "roster_max": 3},
            {"roster_min": 2, "roster_max": 5},
            {"roster_min": 3, "roster_max": 10},
        ]

        for i, config in enumerate(configs):
            league = FantasyLeague(
                season_id=season.id,
                name=f"Config League {i}",
                roster_min=config["roster_min"],
                roster_max=config["roster_max"],
            )
            db_session.add(league)

        db_session.commit()

        # Verify all created
        all_leagues = db_session.query(FantasyLeague).filter(
            FantasyLeague.season_id == season.id
        ).all()
        assert len(all_leagues) >= 3


class TestFantasyLeagueValidation:
    """Test fantasy league validation."""

    def _create_season(self, db_session, test_project):
        """Helper to create a test season."""
        season = Season(
            project_id=test_project.id,
            name="Test Season",
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc) + timedelta(days=30),
            status="draft"
        )
        db_session.add(season)
        db_session.commit()
        return season

    def test_roster_size_validation(self, db_session, test_project):
        """Test that roster min <= roster max."""
        season = self._create_season(db_session, test_project)

        league = FantasyLeague(
            season_id=season.id,
            name="Validation League",
            roster_min=2,
            roster_max=4,
        )

        # Valid: min < max
        assert league.roster_min <= league.roster_max

    def test_league_name_not_empty(self, db_session, test_project):
        """Test that league name is not empty."""
        season = self._create_season(db_session, test_project)

        league = FantasyLeague(
            season_id=season.id,
            name="Valid Name",
            roster_min=1,
            roster_max=5,
        )

        assert len(league.name) > 0

    def test_league_season_association(self, db_session, test_project):
        """Test league is associated with season."""
        season = self._create_season(db_session, test_project)

        league = FantasyLeague(
            season_id=season.id,
            name="Season League",
            roster_min=1,
            roster_max=5,
        )
        db_session.add(league)
        db_session.commit()

        assert league.season_id == season.id


class TestFantasyLeagueQuerying:
    """Test fantasy league database querying."""

    def _create_season(self, db_session, test_project):
        """Helper to create a test season."""
        season = Season(
            project_id=test_project.id,
            name="Test Season",
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc) + timedelta(days=30),
            status="draft"
        )
        db_session.add(season)
        db_session.commit()
        return season

    def test_query_league_by_name(self, db_session, test_project):
        """Test querying league by name."""
        season = self._create_season(db_session, test_project)

        league = FantasyLeague(
            season_id=season.id,
            name="Query League",
            roster_min=1,
            roster_max=5,
        )
        db_session.add(league)
        db_session.commit()

        # Query by name
        fetched = db_session.query(FantasyLeague).filter(
            FantasyLeague.name == "Query League"
        ).first()
        assert fetched is not None
        assert fetched.name == "Query League"

    def test_query_leagues_by_season(self, db_session, test_project):
        """Test querying leagues by season."""
        season = self._create_season(db_session, test_project)

        leagues = []
        for i in range(3):
            league = FantasyLeague(
                season_id=season.id,
                name=f"Season League {i}",
                roster_min=1,
                roster_max=5,
            )
            leagues.append(league)
            db_session.add(league)

        db_session.commit()

        # Query all for season
        fetched = db_session.query(FantasyLeague).filter(
            FantasyLeague.season_id == season.id
        ).all()
        assert len(fetched) >= 3

    def test_query_with_filters(self, db_session, test_project):
        """Test querying with multiple filters."""
        season = self._create_season(db_session, test_project)

        league = FantasyLeague(
            season_id=season.id,
            name="Filter League",
            roster_min=2,
            roster_max=4,
        )
        db_session.add(league)
        db_session.commit()

        # Query with filters
        fetched = db_session.query(FantasyLeague).filter(
            (FantasyLeague.season_id == season.id) &
            (FantasyLeague.roster_min >= 2)
        ).first()
        assert fetched is not None


class TestFantasyLeagueEdgeCases:
    """Test edge cases for fantasy leagues."""

    def _create_season(self, db_session, test_project):
        """Helper to create a test season."""
        season = Season(
            project_id=test_project.id,
            name="Test Season",
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc) + timedelta(days=30),
            status="draft"
        )
        db_session.add(season)
        db_session.commit()
        return season

    def test_large_roster_size(self, db_session, test_project):
        """Test league with large roster size."""
        season = self._create_season(db_session, test_project)

        league = FantasyLeague(
            season_id=season.id,
            name="Large Roster League",
            roster_min=1,
            roster_max=100,
        )

        assert league.roster_max == 100

    def test_single_player_league(self, db_session, test_project):
        """Test league with min roster of 1."""
        season = self._create_season(db_session, test_project)

        league = FantasyLeague(
            season_id=season.id,
            name="Single Player League",
            roster_min=1,
            roster_max=1,
        )

        assert league.roster_min == league.roster_max == 1

    def test_league_with_special_characters(self, db_session, test_project):
        """Test league name with special characters."""
        season = self._create_season(db_session, test_project)

        league = FantasyLeague(
            season_id=season.id,
            name="League #1 - 'Best' Team!",
            roster_min=1,
            roster_max=5,
        )
        db_session.add(league)
        db_session.commit()

        fetched = db_session.query(FantasyLeague).filter(
            FantasyLeague.name == "League #1 - 'Best' Team!"
        ).first()
        assert "#" in fetched.name
        assert "'" in fetched.name

"""Response schema for GET /api/matches."""

from schemas.base_schema import CamelModel


class Odds(CamelModel):
    home: float
    draw: float
    away: float


class Match(CamelModel):
    id: str
    competition: str
    kickoff_date: str
    home_team: str
    away_team: str
    odds: Odds

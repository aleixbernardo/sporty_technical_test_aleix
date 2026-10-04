"""Response schema for POST /api/place-bet."""

from schemas.base_schema import CamelModel


class PlaceBetResponse(CamelModel):
    message: str
    match_id: str
    selection: str
    stake: float
    odds: float
    payout: float
    balance: float
    currency: str

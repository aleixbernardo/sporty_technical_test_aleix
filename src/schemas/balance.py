"""Response schema for GET /api/balance and POST /api/reset-balance."""

from schemas.base_schema import CamelModel


class Balance(CamelModel):
    balance: float
    currency: str

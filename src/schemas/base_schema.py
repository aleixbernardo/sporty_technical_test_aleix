"""Base pydantic model for API response schemas.

The API speaks camelCase (`matchId`, `kickoffDate`), so the base model maps
snake_case Python fields to camelCase JSON aliases. `populate_by_name` keeps the
models usable by either name.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

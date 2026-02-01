from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict


class BaseDTO(BaseModel):
    """DTO base para padronização"""

    class Config:
        from_attributes = True
        populate_by_name = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialização segura"""
        return self.model_dump()

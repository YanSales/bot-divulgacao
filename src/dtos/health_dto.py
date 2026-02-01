from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel


class HealthResponseDTO(BaseModel):
    status: str
    environment: str
    timestamp: datetime


class DetailedHealthResponseDTO(BaseModel):
    status: str
    database: Dict[str, Any]
    queue: Dict[str, Any]
    timestamp: datetime

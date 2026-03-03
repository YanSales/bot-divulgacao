from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CommentDTO:
    uuid: str
    post_uuid: str
    content: str
    status: str
    created_at: datetime
    created_by: Optional[str] = None
    platform: Optional[str] = "internal"
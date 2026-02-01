from datetime import datetime
from src.dtos.base import BaseDTO


class CommentDTO(BaseDTO):
    uuid: str
    post_uuid: str
    texto: str
    status: str
    criado_em: datetime

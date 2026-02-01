from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PostResponseDTO(BaseModel):
    uuid: str
    plataforma: str
    tipo_conteudo: str
    status: str
    horario_agendado: datetime
    criado_em: datetime

    class Config:
        orm_mode = True
        from_attributes = True

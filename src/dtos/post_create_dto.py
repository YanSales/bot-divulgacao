from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PostCreateDTO(BaseModel):
    plataforma: str
    tipo_conteudo: str
    horario_agendado: datetime

    titulo: Optional[str] = None
    descricao: Optional[str] = None
    hashtags: Optional[str] = None
    midia_url: Optional[str] = None

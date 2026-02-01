from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from src.dtos.base import BaseDTO


@dataclass
class PostDTO:
    uuid: str
    plataforma: str
    tipo_conteudo: str
    status: str
    horario_agendado: datetime
    criado_em: datetime
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    midia_url: Optional[str] = None

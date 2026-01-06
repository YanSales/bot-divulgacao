"""
Model para Posts Agendados
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid
import enum

from src.database import Base


class PostStatus(str, enum.Enum):
    """Status possíveis de um post"""
    PENDING = "pending"
    APPROVED = "approved"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Platform(str, enum.Enum):
    """Plataformas suportadas"""
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"


class ContentType(str, enum.Enum):
    """Tipos de conteúdo"""
    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"
    CAROUSEL = "carousel"
    STORY = "story"
    REEL = "reel"


class Post(Base):
    """Model para posts agendados"""
    __tablename__ = "posts_agendados"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Plataforma e tipo
    plataforma = Column(SQLEnum(Platform), nullable=False)
    tipo_conteudo = Column(SQLEnum(ContentType), nullable=False)
    
    # Conteúdo
    titulo = Column(String(500))
    descricao = Column(Text)
    hashtags = Column(Text)  # JSON array como string
    
    # Mídia
    midia_url = Column(Text)  # URL no Azure Blob ou path local
    midia_thumbnail = Column(Text)
    
    # Agendamento
    horario_agendado = Column(DateTime, nullable=False, index=True)
    
    # Status
    status = Column(
        SQLEnum(PostStatus), 
        default=PostStatus.PENDING, 
        nullable=False,
        index=True
    )
    tentativas = Column(Integer, default=0)
    erro_mensagem = Column(Text)
    
    # ID externo (da plataforma)
    post_id_externo = Column(String(100))
    
    # Timestamps
    criado_em = Column(DateTime, default=func.now(), nullable=False)
    atualizado_em = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Auditoria
    criado_por = Column(String(100))
    aprovado_por = Column(String(100))
    aprovado_em = Column(DateTime)
    publicado_em = Column(DateTime)
    
    def __repr__(self):
        return f"<Post {self.uuid} - {self.plataforma.value} - {self.status.value}>"
    
    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "plataforma": self.plataforma.value,
            "tipo_conteudo": self.tipo_conteudo.value,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "hashtags": self.hashtags,
            "midia_url": self.midia_url,
            "midia_thumbnail": self.midia_thumbnail,
            "horario_agendado": self.horario_agendado.isoformat() if self.horario_agendado else None,
            "status": self.status.value,
            "tentativas": self.tentativas,
            "erro_mensagem": self.erro_mensagem,
            "post_id_externo": self.post_id_externo,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
            "criado_por": self.criado_por,
            "aprovado_por": self.aprovado_por,
            "aprovado_em": self.aprovado_em.isoformat() if self.aprovado_em else None,
            "publicado_em": self.publicado_em.isoformat() if self.publicado_em else None,
        }
    
    @property
    def is_scheduled(self) -> bool:
        """Verifica se está agendado para o futuro"""
        return self.horario_agendado > datetime.now()
    
    @property
    def is_ready_to_publish(self) -> bool:
        """Verifica se está pronto para publicar"""
        return (
            self.status == PostStatus.APPROVED and
            self.horario_agendado <= datetime.now()
        )
    
    def mark_as_published(self, post_id_externo: str):
        """Marca como publicado"""
        self.status = PostStatus.PUBLISHED
        self.post_id_externo = post_id_externo
        self.publicado_em = datetime.now()
    
    def mark_as_failed(self, error_message: str):
        """Marca como falho"""
        self.status = PostStatus.FAILED
        self.erro_mensagem = error_message
        self.tentativas += 1
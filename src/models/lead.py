"""
Model para Leads
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from src.database import Base


class LeadStatus(str, enum.Enum):
    """Status do lead no funil"""
    NOVO = "novo"
    CONTATADO = "contatado"
    QUALIFICADO = "qualificado"
    CONVERTIDO = "convertido"
    PERDIDO = "perdido"


class LeadOrigin(str, enum.Enum):
    """Origem do lead"""
    LANDING_PAGE = "landing_page"
    INSTAGRAM_DM = "instagram_dm"
    INSTAGRAM_COMMENT = "instagram_comment"
    FACEBOOK_DM = "facebook_dm"
    FACEBOOK_COMMENT = "facebook_comment"
    TWITTER_DM = "twitter_dm"
    TWITTER_MENTION = "twitter_mention"
    WHATSAPP = "whatsapp"
    YOUTUBE_COMMENT = "youtube_comment"
    MANUAL = "manual"


class Lead(Base):
    """Model para leads capturados"""
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Origem
    origem = Column(SQLEnum(LeadOrigin), nullable=False, index=True)
    
    # Dados pessoais
    nome = Column(String(200))
    email = Column(String(200), index=True)
    telefone = Column(String(50))
    
    # Dados de redes sociais
    plataforma_social = Column(String(20))
    usuario_id_externo = Column(String(100), index=True)
    username = Column(String(100))
    
    # Qualificação
    score = Column(Integer, default=0, index=True)  # 0-100
    status = Column(
        SQLEnum(LeadStatus), 
        default=LeadStatus.NOVO, 
        nullable=False,
        index=True
    )
    
    # Categorização
    tags = Column(Text)  # JSON array como string
    dados_enriquecidos = Column(Text)  # JSON com dados adicionais
    
    # Interações
    primeira_interacao = Column(DateTime, index=True)
    ultima_interacao = Column(DateTime, index=True)
    numero_interacoes = Column(Integer, default=0)
    
    # Timestamps
    criado_em = Column(DateTime, default=func.now(), nullable=False)
    atualizado_em = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Lead {self.uuid} - {self.nome or self.username} - Score: {self.score}>"
    
    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "origem": self.origem.value,
            "nome": self.nome,
            "email": self.email,
            "telefone": self.telefone,
            "plataforma_social": self.plataforma_social,
            "usuario_id_externo": self.usuario_id_externo,
            "username": self.username,
            "score": self.score,
            "status": self.status.value,
            "tags": self.tags,
            "dados_enriquecidos": self.dados_enriquecidos,
            "primeira_interacao": self.primeira_interacao.isoformat() if self.primeira_interacao else None,
            "ultima_interacao": self.ultima_interacao.isoformat() if self.ultima_interacao else None,
            "numero_interacoes": self.numero_interacoes,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
        }
    
    @property
    def is_hot_lead(self) -> bool:
        """Verifica se é lead quente (score alto)"""
        return self.score >= 80
    
    @property
    def is_cold_lead(self) -> bool:
        """Verifica se é lead frio (score baixo)"""
        return self.score < 50
    
    def increment_score(self, points: int = 10):
        """Incrementa o score do lead"""
        self.score = min(100, self.score + points)
        self.ultima_interacao = datetime.now()
        self.numero_interacoes += 1
    
    def decrement_score(self, points: int = 5):
        """Decrementa o score do lead"""
        self.score = max(0, self.score - points)
    
    def mark_as_converted(self):
        """Marca lead como convertido"""
        self.status = LeadStatus.CONVERTIDO
        self.score = 100
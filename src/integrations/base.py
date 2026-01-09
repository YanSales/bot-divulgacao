"""
Interface base para adaptadores de redes sociais
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.utils.logger import get_logger

logger = get_logger(__name__)


class MediaType(str, Enum):
    """Tipos de mídia suportados"""
    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"
    CAROUSEL = "carousel"


@dataclass
class PostResult:
    """Resultado de uma publicação"""
    success: bool
    post_id: Optional[str] = None
    error_message: Optional[str] = None
    platform: Optional[str] = None
    url: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "post_id": self.post_id,
            "error_message": self.error_message,
            "platform": self.platform,
            "url": self.url,
        }


@dataclass
class Comment:
    """Representa um comentário"""
    id: str
    text: str
    username: str
    user_id: str
    timestamp: datetime
    post_id: str
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "username": self.username,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "post_id": self.post_id,
        }


@dataclass
class PostMetrics:
    """Métricas de um post"""
    post_id: str
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    reach: int = 0
    impressions: int = 0
    engagement_rate: float = 0.0
    collected_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "post_id": self.post_id,
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "saves": self.saves,
            "reach": self.reach,
            "impressions": self.impressions,
            "engagement_rate": self.engagement_rate,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
        }


class RateLimitExceeded(Exception):
    """Exceção quando rate limit é atingido"""
    pass


class PlatformAdapter(ABC):
    """
    Interface base para adaptadores de plataformas
    
    Todos os adaptadores devem implementar estes métodos
    """
    
    def __init__(self, credentials: Dict[str, str]):
        self.credentials = credentials
        self.platform_name = self.__class__.__name__.replace("Adapter", "").lower()
        self.logger = get_logger(f"{__name__}.{self.platform_name}")
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Autentica na plataforma
        
        Returns:
            True se autenticado, False caso contrário
        """
        pass
    
    @abstractmethod
    def publish_image(
        self, 
        image_path: str, 
        caption: str,
        **kwargs
    ) -> PostResult:
        """
        Publica uma imagem
        
        Args:
            image_path: Caminho da imagem
            caption: Legenda do post
            **kwargs: Parâmetros adicionais específicos da plataforma
            
        Returns:
            PostResult com resultado da publicação
        """
        pass
    
    @abstractmethod
    def publish_video(
        self, 
        video_path: str, 
        caption: str,
        **kwargs
    ) -> PostResult:
        """
        Publica um vídeo
        
        Args:
            video_path: Caminho do vídeo
            caption: Legenda do post
            **kwargs: Parâmetros adicionais específicos da plataforma
            
        Returns:
            PostResult com resultado da publicação
        """
        pass
    
    @abstractmethod
    def publish_text(self, text: str, **kwargs) -> PostResult:
        """
        Publica apenas texto
        
        Args:
            text: Conteúdo do texto
            **kwargs: Parâmetros adicionais específicos da plataforma
            
        Returns:
            PostResult com resultado da publicação
        """
        pass
    
    @abstractmethod
    def get_comments(self, post_id: str, limit: int = 100) -> List[Comment]:
        """
        Obtém comentários de um post
        
        Args:
            post_id: ID do post
            limit: Número máximo de comentários
            
        Returns:
            Lista de comentários
        """
        pass
    
    @abstractmethod
    def reply_to_comment(
        self, 
        comment_id: str, 
        reply_text: str
    ) -> bool:
        """
        Responde a um comentário
        
        Args:
            comment_id: ID do comentário
            reply_text: Texto da resposta
            
        Returns:
            True se sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    def get_post_metrics(self, post_id: str) -> PostMetrics:
        """
        Obtém métricas de um post
        
        Args:
            post_id: ID do post
            
        Returns:
            PostMetrics com as métricas
        """
        pass
    
    @abstractmethod
    def delete_post(self, post_id: str) -> bool:
        """
        Deleta um post
        
        Args:
            post_id: ID do post
            
        Returns:
            True se sucesso, False caso contrário
        """
        pass
    
    def check_rate_limit(self) -> Dict[str, Any]:
        """
        Verifica status do rate limit
        
        Returns:
            Dict com informações do rate limit
        """
        return {
            "platform": self.platform_name,
            "status": "ok",
            "remaining": None,
            "reset_at": None,
        }
    
    def validate_media(
        self, 
        file_path: str, 
        media_type: MediaType
    ) -> tuple[bool, Optional[str]]:
        """
        Valida arquivo de mídia
        
        Args:
            file_path: Caminho do arquivo
            media_type: Tipo de mídia
            
        Returns:
            Tupla (válido, mensagem_erro)
        """
        import os
        from pathlib import Path
        
        if not os.path.exists(file_path):
            return False, "Arquivo não encontrado"
        
        file_size = os.path.getsize(file_path)
        file_ext = Path(file_path).suffix.lower()
        
        if media_type == MediaType.IMAGE:
            # Validações para imagem
            valid_exts = ['.jpg', '.jpeg', '.png', '.gif']
            max_size = 8 * 1024 * 1024  # 8MB
            
            if file_ext not in valid_exts:
                return False, f"Extensão inválida. Use: {', '.join(valid_exts)}"
            
            if file_size > max_size:
                return False, f"Arquivo muito grande. Máximo: 8MB"
        
        elif media_type == MediaType.VIDEO:
            # Validações para vídeo
            valid_exts = ['.mp4', '.mov', '.avi']
            max_size = 100 * 1024 * 1024  # 100MB
            
            if file_ext not in valid_exts:
                return False, f"Extensão inválida. Use: {', '.join(valid_exts)}"
            
            if file_size > max_size:
                return False, f"Arquivo muito grande. Máximo: 100MB"
        
        return True, None
    
    def log_action(self, action: str, success: bool, details: Optional[Dict] = None):
        """Log de ações na plataforma"""
        log_data = {
            "platform": self.platform_name,
            "action": action,
            "success": success,
            **(details or {})
        }
        
        if success:
            self.logger.info(f"{action} completed", **log_data)
        else:
            self.logger.error(f"{action} failed", **log_data)
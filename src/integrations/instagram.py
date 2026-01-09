"""
Adaptador para Instagram usando Graph API
"""
import requests
import time
from typing import List, Optional, Dict
from datetime import datetime

from src.integrations.base import (
    PlatformAdapter, PostResult, Comment, PostMetrics,
    MediaType, RateLimitExceeded
)
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class InstagramAdapter(PlatformAdapter):
    """Adaptador para Instagram Graph API"""
    
    BASE_URL = "https://graph.facebook.com/v24.0"
    
    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        if credentials is None:
            credentials = {
                "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
                "user_id": settings.INSTAGRAM_USER_ID,
            }
        super().__init__(credentials)
        self.access_token = credentials.get("access_token")
        self.user_id = credentials.get("user_id")
        self.api_calls_count = 0
        self.last_reset = time.time()
    
    def authenticate(self) -> bool:
        """Verifica se o token é válido"""
        try:
            url = f"{self.BASE_URL}/me"
            params = {"access_token": self.access_token}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("Autenticação Instagram bem-sucedida")
                return True
            else:
                self.logger.error(
                    "Falha na autenticação Instagram",
                    status_code=response.status_code,
                    error=response.text
                )
                return False
        except Exception as e:
            self.logger.error("Erro ao autenticar Instagram", error=str(e))
            return False
    
    def _check_rate_limit(self):
        """Verifica e controla rate limit (200 chamadas/hora)"""
        current_time = time.time()
        
        # Reset contador a cada hora
        if current_time - self.last_reset > 3600:
            self.api_calls_count = 0
            self.last_reset = current_time
        
        # Verificar limite
        if self.api_calls_count >= 180:  # Deixar margem de segurança
            raise RateLimitExceeded("Rate limit do Instagram atingido")
        
        self.api_calls_count += 1
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> requests.Response:
        """Faz requisição à API com controle de rate limit"""
        self._check_rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        if data is None:
            data = {}
        
        data["access_token"] = self.access_token
        
        if method.upper() == "GET":
            response = requests.get(url, params=data, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, data=data, files=files, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, params=data, timeout=30)
        else:
            raise ValueError(f"Método HTTP inválido: {method}")
        
        return response
    
    def publish_image(
        self, 
        image_path: str, 
        caption: str,
        **kwargs
    ) -> PostResult:
        """
        Publica uma imagem no Instagram
        
        Processo:
        1. Cria container de mídia
        2. Aguarda processamento
        3. Publica container
        """
        try:
            # Validar imagem
            valid, error = self.validate_media(image_path, MediaType.IMAGE)
            if not valid:
                return PostResult(
                    success=False,
                    error_message=error,
                    platform="instagram"
                )
            
            # Passo 1: Upload da imagem para um servidor (precisa estar acessível via URL)
            # Para MVP, assumimos que a imagem já está no Azure Blob
            image_url = kwargs.get("image_url", image_path)
            
            # Passo 2: Criar container
            self.logger.info(f"Criando container para imagem: {image_url}")
            
            container_data = {
                "image_url": image_url,
                "caption": caption,
            }
            
            response = self._make_request(
                "POST",
                f"{self.user_id}/media",
                data=container_data
            )
            
            if response.status_code != 200:
                return PostResult(
                    success=False,
                    error_message=f"Erro ao criar container: {response.text}",
                    platform="instagram"
                )
            
            creation_id = response.json().get("id")
            self.logger.info(f"Container criado: {creation_id}")
            
            # Passo 3: Publicar container
            time.sleep(2)  # Aguardar processamento
            
            publish_data = {
                "creation_id": creation_id,
            }
            
            response = self._make_request(
                "POST",
                f"{self.user_id}/media_publish",
                data=publish_data
            )
            
            if response.status_code != 200:
                return PostResult(
                    success=False,
                    error_message=f"Erro ao publicar: {response.text}",
                    platform="instagram"
                )
            
            post_id = response.json().get("id")
            
            self.log_action("publish_image", True, {"post_id": post_id})
            
            return PostResult(
                success=True,
                post_id=post_id,
                platform="instagram",
                url=f"https://www.instagram.com/p/{post_id}/"
            )
            
        except RateLimitExceeded as e:
            self.logger.warning("Rate limit atingido", error=str(e))
            return PostResult(
                success=False,
                error_message=str(e),
                platform="instagram"
            )
        except Exception as e:
            self.logger.error("Erro ao publicar imagem", error=str(e))
            return PostResult(
                success=False,
                error_message=str(e),
                platform="instagram"
            )
    
    def publish_video(
        self, 
        video_path: str, 
        caption: str,
        **kwargs
    ) -> PostResult:
        """Publica um vídeo no Instagram"""
        try:
            valid, error = self.validate_media(video_path, MediaType.VIDEO)
            if not valid:
                return PostResult(
                    success=False,
                    error_message=error,
                    platform="instagram"
                )
            
            video_url = kwargs.get("video_url", video_path)
            
            # Criar container de vídeo
            container_data = {
                "media_type": "VIDEO",
                "video_url": video_url,
                "caption": caption,
            }
            
            response = self._make_request(
                "POST",
                f"{self.user_id}/media",
                data=container_data
            )
            
            if response.status_code != 200:
                return PostResult(
                    success=False,
                    error_message=f"Erro ao criar container: {response.text}",
                    platform="instagram"
                )
            
            creation_id = response.json().get("id")
            
            # Verificar status do processamento
            max_attempts = 30
            for attempt in range(max_attempts):
                time.sleep(10)  # Aguardar 10 segundos entre verificações
                
                response = self._make_request(
                    "GET",
                    creation_id,
                    data={"fields": "status_code"}
                )
                
                status_code = response.json().get("status_code")
                
                if status_code == "FINISHED":
                    break
                elif status_code == "ERROR":
                    return PostResult(
                        success=False,
                        error_message="Erro no processamento do vídeo",
                        platform="instagram"
                    )
                
                if attempt == max_attempts - 1:
                    return PostResult(
                        success=False,
                        error_message="Timeout no processamento do vídeo",
                        platform="instagram"
                    )
            
            # Publicar vídeo
            publish_data = {"creation_id": creation_id}
            
            response = self._make_request(
                "POST",
                f"{self.user_id}/media_publish",
                data=publish_data
            )
            
            if response.status_code != 200:
                return PostResult(
                    success=False,
                    error_message=f"Erro ao publicar: {response.text}",
                    platform="instagram"
                )
            
            post_id = response.json().get("id")
            
            self.log_action("publish_video", True, {"post_id": post_id})
            
            return PostResult(
                success=True,
                post_id=post_id,
                platform="instagram"
            )
            
        except Exception as e:
            self.logger.error("Erro ao publicar vídeo", error=str(e))
            return PostResult(
                success=False,
                error_message=str(e),
                platform="instagram"
            )
    
    def publish_text(self, text: str, **kwargs) -> PostResult:
        """
        Instagram não suporta posts apenas de texto
        Retorna erro
        """
        return PostResult(
            success=False,
            error_message="Instagram não suporta posts de texto puro",
            platform="instagram"
        )
    
    def get_comments(self, post_id: str, limit: int = 100) -> List[Comment]:
        """Obtém comentários de um post"""
        try:
            response = self._make_request(
                "GET",
                f"{post_id}/comments",
                data={
                    "fields": "id,text,username,timestamp,from",
                    "limit": min(limit, 100)
                }
            )
            
            if response.status_code != 200:
                self.logger.error(
                    "Erro ao obter comentários",
                    post_id=post_id,
                    error=response.text
                )
                return []
            
            comments_data = response.json().get("data", [])
            
            comments = []
            for comment_data in comments_data:
                comment = Comment(
                    id=comment_data.get("id"),
                    text=comment_data.get("text", ""),
                    username=comment_data.get("username", ""),
                    user_id=comment_data.get("from", {}).get("id", ""),
                    timestamp=datetime.fromisoformat(
                        comment_data.get("timestamp", "").replace("Z", "+00:00")
                    ),
                    post_id=post_id
                )
                comments.append(comment)
            
            return comments
            
        except Exception as e:
            self.logger.error("Erro ao obter comentários", error=str(e))
            return []
    
    def reply_to_comment(self, comment_id: str, reply_text: str) -> bool:
        """Responde a um comentário"""
        try:
            response = self._make_request(
                "POST",
                f"{comment_id}/replies",
                data={"message": reply_text}
            )
            
            success = response.status_code == 200
            
            self.log_action(
                "reply_comment",
                success,
                {"comment_id": comment_id}
            )
            
            return success
            
        except Exception as e:
            self.logger.error("Erro ao responder comentário", error=str(e))
            return False
    
    def get_post_metrics(self, post_id: str) -> PostMetrics:
        """Obtém métricas de um post"""
        try:
            response = self._make_request(
                "GET",
                f"{post_id}/insights",
                data={
                    "metric": "engagement,impressions,reach,saved"
                }
            )
            
            if response.status_code != 200:
                self.logger.error(
                    "Erro ao obter métricas",
                    post_id=post_id,
                    error=response.text
                )
                return PostMetrics(post_id=post_id)
            
            insights_data = response.json().get("data", [])
            
            metrics = PostMetrics(
                post_id=post_id,
                collected_at=datetime.now()
            )
            
            for insight in insights_data:
                metric_name = insight.get("name")
                value = insight.get("values", [{}])[0].get("value", 0)
                
                if metric_name == "engagement":
                    metrics.likes = value
                elif metric_name == "impressions":
                    metrics.impressions = value
                elif metric_name == "reach":
                    metrics.reach = value
                elif metric_name == "saved":
                    metrics.saves = value
            
            # Calcular engagement rate
            if metrics.reach > 0:
                metrics.engagement_rate = (metrics.likes / metrics.reach) * 100
            
            return metrics
            
        except Exception as e:
            self.logger.error("Erro ao obter métricas", error=str(e))
            return PostMetrics(post_id=post_id)
    
    def delete_post(self, post_id: str) -> bool:
        """Deleta um post"""
        try:
            response = self._make_request("DELETE", post_id)
            
            success = response.status_code == 200
            
            self.log_action("delete_post", success, {"post_id": post_id})
            
            return success
            
        except Exception as e:
            self.logger.error("Erro ao deletar post", error=str(e))
            return False
    
    def check_rate_limit(self) -> Dict:
        """Verifica status do rate limit"""
        return {
            "platform": "instagram",
            "status": "ok" if self.api_calls_count < 180 else "warning",
            "remaining": max(0, 200 - self.api_calls_count),
            "total": 200,
            "reset_at": datetime.fromtimestamp(self.last_reset + 3600).isoformat(),
        }
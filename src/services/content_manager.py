"""
Gerenciador de conteúdo para upload e publicação
"""
import os
import shutil
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import hashlib

from src.config import settings, UPLOADS_DIR
from src.utils.logger import get_logger
from src.integrations.factory import AdapterFactory
from src.integrations.base import PostResult, MediaType
from PIL import Image

logger = get_logger(__name__)


class ContentManager:
    """Gerencia upload, armazenamento e publicação de conteúdo"""
    
    def __init__(self):
        self.uploads_dir = UPLOADS_DIR
        self.uploads_dir.mkdir(exist_ok=True, parents=True)
        
        # Criar subpastas por tipo
        (self.uploads_dir / "images").mkdir(exist_ok=True)
        (self.uploads_dir / "videos").mkdir(exist_ok=True)
        (self.uploads_dir / "temp").mkdir(exist_ok=True)
    
    def save_upload(
        self, 
        file_path: str, 
        media_type: MediaType,
        optimize: bool = True
    ) -> Optional[str]:
        """
        Salva arquivo no storage local
        
        Args:
            file_path: Caminho do arquivo original
            media_type: Tipo de mídia
            optimize: Se deve otimizar arquivo
            
        Returns:
            Caminho do arquivo salvo ou None
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"Arquivo não encontrado: {file_path}")
                return None
            
            # Gerar nome único baseado em hash
            file_hash = self._generate_file_hash(file_path)
            file_ext = Path(file_path).suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            filename = f"{timestamp}_{file_hash}{file_ext}"
            
            # Determinar pasta de destino
            if media_type == MediaType.IMAGE:
                dest_dir = self.uploads_dir / "images"
            elif media_type == MediaType.VIDEO:
                dest_dir = self.uploads_dir / "videos"
            else:
                dest_dir = self.uploads_dir
            
            dest_path = dest_dir / filename
            
            # Otimizar imagens
            if media_type == MediaType.IMAGE and optimize:
                self._optimize_image(file_path, str(dest_path))
            else:
                shutil.copy2(file_path, dest_path)
            
            logger.info(f"Arquivo salvo: {dest_path}")
            return str(dest_path)
            
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo: {str(e)}")
            return None
    
    def _generate_file_hash(self, file_path: str) -> str:
        """Gera hash MD5 do arquivo"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()[:8]
    
    def _optimize_image(
        self, 
        input_path: str, 
        output_path: str,
        max_size: tuple = (1920, 1920),
        quality: int = 85
    ):
        """
        Otimiza imagem para web
        
        Args:
            input_path: Caminho da imagem original
            output_path: Caminho para salvar
            max_size: Tamanho máximo (largura, altura)
            quality: Qualidade JPEG (0-100)
        """
        try:
            with Image.open(input_path) as img:
                # Converter RGBA para RGB se necessário
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Redimensionar se necessário
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Salvar otimizada
                img.save(output_path, "JPEG", quality=quality, optimize=True)
                
                logger.info(
                    f"Imagem otimizada",
                    original_size=os.path.getsize(input_path),
                    optimized_size=os.path.getsize(output_path)
                )
        except Exception as e:
            logger.error(f"Erro ao otimizar imagem: {str(e)}")
            # Se falhar, copiar original
            shutil.copy2(input_path, output_path)
    
    def get_public_url(self, file_path: str) -> str:
        """
        Obtém URL pública do arquivo
        
        Para MVP, retorna caminho local
        Em produção, usar Azure Blob Storage
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            URL pública do arquivo
        """
        if settings.use_azure_storage:
            # TODO: Implementar upload para Azure Blob
            return self._upload_to_azure(file_path)
        else:
            # Para desenvolvimento, retornar caminho local
            # Em produção, isso deve ser servido por um servidor web
            return file_path
    
    def _upload_to_azure(self, file_path: str) -> str:
        """
        Upload para Azure Blob Storage
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            URL pública do blob
        """
        try:
            from azure.storage.blob import BlobServiceClient
            
            blob_service = BlobServiceClient.from_connection_string(
                settings.AZURE_STORAGE_CONNECTION_STRING
            )
            
            filename = Path(file_path).name
            blob_client = blob_service.get_blob_client(
                container=settings.AZURE_STORAGE_CONTAINER,
                blob=filename
            )
            
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            
            blob_url = blob_client.url
            logger.info(f"Arquivo enviado para Azure: {blob_url}")
            
            return blob_url
            
        except Exception as e:
            logger.error(f"Erro ao enviar para Azure: {str(e)}")
            return file_path
    
    def publish_content(
        self,
        platform: str,
        media_type: MediaType,
        file_path: Optional[str] = None,
        caption: str = "",
        **kwargs
    ) -> PostResult:
        """
        Publica conteúdo em uma plataforma
        
        Args:
            platform: Nome da plataforma
            media_type: Tipo de mídia
            file_path: Caminho do arquivo (se houver)
            caption: Legenda/texto do post
            **kwargs: Parâmetros adicionais
            
        Returns:
            PostResult com resultado da publicação
        """
        try:
            # Criar adaptador da plataforma
            adapter = AdapterFactory.create(platform)
            
            if adapter is None:
                return PostResult(
                    success=False,
                    error_message=f"Plataforma não disponível: {platform}",
                    platform=platform
                )
            
            # Obter URL pública se houver arquivo
            if file_path:
                public_url = self.get_public_url(file_path)
                kwargs["image_url"] = public_url
                kwargs["video_url"] = public_url
            
            # Publicar conforme tipo
            if media_type == MediaType.IMAGE and file_path:
                result = adapter.publish_image(file_path, caption, **kwargs)
            elif media_type == MediaType.VIDEO and file_path:
                result = adapter.publish_video(file_path, caption, **kwargs)
            elif media_type == MediaType.TEXT:
                result = adapter.publish_text(caption, **kwargs)
            else:
                result = PostResult(
                    success=False,
                    error_message=f"Tipo de mídia não suportado: {media_type}",
                    platform=platform
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao publicar conteúdo: {str(e)}")
            return PostResult(
                success=False,
                error_message=str(e),
                platform=platform
            )
    
    def delete_file(self, file_path: str) -> bool:
        """
        Deleta arquivo do storage
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            True se deletado com sucesso
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Arquivo deletado: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo: {str(e)}")
            return False
    
    def cleanup_temp(self):
        """Limpa arquivos temporários antigos (>24h)"""
        try:
            temp_dir = self.uploads_dir / "temp"
            now = datetime.now().timestamp()
            
            for file_path in temp_dir.iterdir():
                if file_path.is_file():
                    # Verificar se arquivo tem mais de 24 horas
                    file_age = now - file_path.stat().st_mtime
                    if file_age > 86400:  # 24 horas em segundos
                        file_path.unlink()
                        logger.info(f"Arquivo temporário removido: {file_path}")
        except Exception as e:
            logger.error(f"Erro ao limpar arquivos temporários: {str(e)}")
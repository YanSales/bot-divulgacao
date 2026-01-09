"""
Factory para criar adaptadores de plataformas
"""
from typing import Optional, Dict
from src.integrations.base import PlatformAdapter
from src.integrations.instagram import InstagramAdapter
from src.integrations.facebook import FacebookAdapter
from src.config import settings, ENABLED_PLATFORMS
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AdapterFactory:
    """Factory para criar adaptadores de plataformas"""
    
    _adapters = {
        "instagram": InstagramAdapter,
        "facebook": FacebookAdapter,
        # Adicionar outros adaptadores aqui
    }
    
    @classmethod
    def create(
        cls, 
        platform: str, 
        credentials: Optional[Dict[str, str]] = None
    ) -> Optional[PlatformAdapter]:
        """
        Cria um adaptador para a plataforma especificada
        
        Args:
            platform: Nome da plataforma (instagram, facebook, etc)
            credentials: Credenciais opcionais (usa .env se não fornecido)
            
        Returns:
            Adaptador da plataforma ou None se não suportada
        """
        platform_lower = platform.lower()
        
        # Verificar se plataforma está habilitada
        if not ENABLED_PLATFORMS.get(platform_lower, False):
            logger.warning(
                f"Plataforma {platform} não está habilitada ou sem credenciais"
            )
            return None
        
        # Obter classe do adaptador
        adapter_class = cls._adapters.get(platform_lower)
        
        if adapter_class is None:
            logger.error(f"Adaptador não implementado para: {platform}")
            return None
        
        try:
            # Criar instância do adaptador
            adapter = adapter_class(credentials)
            
            # Tentar autenticar
            if not adapter.authenticate():
                logger.error(f"Falha na autenticação: {platform}")
                return None
            
            logger.info(f"Adaptador criado com sucesso: {platform}")
            return adapter
            
        except Exception as e:
            logger.error(
                f"Erro ao criar adaptador {platform}",
                error=str(e)
            )
            return None
    
    @classmethod
    def create_all(cls) -> Dict[str, PlatformAdapter]:
        """
        Cria adaptadores para todas as plataformas habilitadas
        
        Returns:
            Dict com adaptadores criados {platform: adapter}
        """
        adapters = {}
        
        for platform, enabled in ENABLED_PLATFORMS.items():
            if enabled:
                adapter = cls.create(platform)
                if adapter:
                    adapters[platform] = adapter
        
        logger.info(
            f"Criados {len(adapters)} adaptadores",
            platforms=list(adapters.keys())
        )
        
        return adapters
    
    @classmethod
    def get_supported_platforms(cls) -> list:
        """Retorna lista de plataformas suportadas"""
        return list(cls._adapters.keys())


# Exemplo de uso
if __name__ == "__main__":
    # Criar adaptador Instagram
    instagram = AdapterFactory.create("instagram")
    if instagram:
        print("✅ Instagram conectado!")
    
    # Criar adaptador Facebook
    facebook = AdapterFactory.create("facebook")
    if facebook:
        print("✅ Facebook conectado!")
    
    # Criar todos os adaptadores
    all_adapters = AdapterFactory.create_all()
    print(f"\n📱 Plataformas conectadas: {list(all_adapters.keys())}")
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.content_manager import ContentManager
from src.integrations.base import MediaType

# Criar gerenciador
manager = ContentManager()

# Teste 1: Publicar texto no Facebook
print("📝 Testando publicação de texto...")
result = manager.publish_content(
    platform="facebook",
    media_type=MediaType.TEXT,
    caption="Teste do bot de divulgação! 🤖"
)

print(f"Resultado: {'✅ Sucesso!' if result.success else '❌ Falha'}")
if result.post_id:
    print(f"Post ID: {result.post_id}")
if result.error_message:
    print(f"Erro: {result.error_message}")
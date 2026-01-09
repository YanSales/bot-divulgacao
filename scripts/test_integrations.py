"""
Script para testar integrações com redes sociais
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.integrations.factory import AdapterFactory
from src.config import ENABLED_PLATFORMS
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_authentication():
    """Testa autenticação em todas as plataformas"""
    print("\n" + "="*60)
    print("🔐 Testando Autenticação das Plataformas")
    print("="*60 + "\n")
    
    results = {}
    
    for platform, enabled in ENABLED_PLATFORMS.items():
        print(f"📱 {platform.upper()}...")
        
        if not enabled:
            print(f"   ⚠️  Desabilitado (sem credenciais no .env)")
            results[platform] = "disabled"
            continue
        
        try:
            adapter = AdapterFactory.create(platform)
            
            if adapter:
                print(f"   ✅ Conectado com sucesso!")
                results[platform] = "success"
                
                # Testar rate limit
                rate_info = adapter.check_rate_limit()
                if rate_info.get("remaining"):
                    print(f"   📊 Rate Limit: {rate_info['remaining']}/{rate_info.get('total', 'N/A')} restantes")
            else:
                print(f"   ❌ Falha na conexão")
                results[platform] = "failed"
                
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
            results[platform] = "error"
        
        print()
    
    return results


def test_post_capabilities():
    """Testa capacidades de publicação"""
    print("\n" + "="*60)
    print("📝 Testando Capacidades de Publicação")
    print("="*60 + "\n")
    
    for platform, enabled in ENABLED_PLATFORMS.items():
        if not enabled:
            continue
        
        print(f"📱 {platform.upper()}:")
        
        adapter = AdapterFactory.create(platform)
        if not adapter:
            print(f"   ❌ Não conectado\n")
            continue
        
        # Verificar métodos disponíveis
        capabilities = []
        
        if hasattr(adapter, 'publish_image'):
            capabilities.append("Imagens")
        if hasattr(adapter, 'publish_video'):
            capabilities.append("Vídeos")
        if hasattr(adapter, 'publish_text'):
            capabilities.append("Texto")
        if hasattr(adapter, 'get_comments'):
            capabilities.append("Ler comentários")
        if hasattr(adapter, 'reply_to_comment'):
            capabilities.append("Responder comentários")
        if hasattr(adapter, 'get_post_metrics'):
            capabilities.append("Métricas")
        
        print(f"   ✅ Suporta: {', '.join(capabilities)}\n")


def generate_report(results):
    """Gera relatório final"""
    print("\n" + "="*60)
    print("📊 RELATÓRIO FINAL")
    print("="*60 + "\n")
    
    success_count = sum(1 for r in results.values() if r == "success")
    failed_count = sum(1 for r in results.values() if r == "failed")
    disabled_count = sum(1 for r in results.values() if r == "disabled")
    error_count = sum(1 for r in results.values() if r == "error")
    
    print(f"✅ Conectadas: {success_count}")
    print(f"❌ Falhas: {failed_count}")
    print(f"⚠️  Desabilitadas: {disabled_count}")
    print(f"🔥 Erros: {error_count}")
    
    print("\n📋 Status por Plataforma:")
    for platform, status in results.items():
        emoji = {
            "success": "✅",
            "failed": "❌",
            "disabled": "⚠️",
            "error": "🔥"
        }.get(status, "❓")
        
        print(f"   {emoji} {platform.upper()}: {status}")
    
    print("\n" + "="*60)
    
    if failed_count > 0 or error_count > 0:
        print("\n⚠️  Dicas para resolver problemas:")
        print("   1. Verifique as credenciais no arquivo .env")
        print("   2. Certifique-se que os tokens não expiraram")
        print("   3. Verifique se as permissões estão corretas")
        print("   4. Consulte a documentação em docs/api_reference.md")


def main():
    """Função principal"""
    print("\n🤖 Bot de Divulgação - Teste de Integrações\n")
    
    try:
        # Testar autenticação
        results = test_authentication()
        
        # Testar capacidades
        test_post_capabilities()
        
        # Gerar relatório
        generate_report(results)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste cancelado pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
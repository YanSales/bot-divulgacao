"""
Script para preparar ambiente de testes
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import init_db, DatabaseHealthCheck
from src.config import settings, ENABLED_PLATFORMS
from src.utils.logger import get_logger

logger = get_logger(__name__)


def check_environment():
    """Verifica variáveis de ambiente"""
    print("\n" + "="*60)
    print("🔧 Verificando Variáveis de Ambiente")
    print("="*60 + "\n")
    
    required = {
        "SECRET_KEY": settings.SECRET_KEY,
        "API_KEY": settings.API_KEY,
        "DATABASE_URL": settings.DATABASE_URL,
    }
    
    optional = {
        "INSTAGRAM_ACCESS_TOKEN": settings.INSTAGRAM_ACCESS_TOKEN,
        "FACEBOOK_USER_ACCESS_TOKEN": settings.FACEBOOK_USER_ACCESS_TOKEN,
        "REDIS_URL": settings.REDIS_URL,
    }
    
    all_ok = True
    
    print("📋 Variáveis Obrigatórias:")
    for name, value in required.items():
        if value:
            masked = value[:8] + "..." if len(value) > 8 else value
            print(f"   ✅ {name}: {masked}")
        else:
            print(f"   ❌ {name}: NÃO CONFIGURADO")
            all_ok = False
    
    print("\n📋 Variáveis Opcionais:")
    for name, value in optional.items():
        if value:
            masked = value[:8] + "..." if len(value) > 8 else value
            print(f"   ✅ {name}: {masked}")
        else:
            print(f"   ⚠️  {name}: não configurado")
    
    print("\n📱 Plataformas Habilitadas:")
    for platform, enabled in ENABLED_PLATFORMS.items():
        emoji = "✅" if enabled else "❌"
        print(f"   {emoji} {platform.upper()}")
    
    return all_ok


def check_database():
    """Verifica banco de dados"""
    print("\n" + "="*60)
    print("🗄️  Verificando Banco de Dados")
    print("="*60 + "\n")
    
    try:
        # Tentar inicializar
        init_db()
        print("✅ Banco de dados inicializado")
        
        # Health check
        health = DatabaseHealthCheck.get_status()
        
        if health["status"] == "healthy":
            print("✅ Banco de dados saudável")
            print(f"   Total de posts: {health['stats']['total_posts']}")
            print(f"   Total de leads: {health['stats']['total_leads']}")
            return True
        else:
            print(f"❌ Banco de dados com problemas: {health.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {str(e)}")
        return False


def check_directories():
    """Verifica estrutura de diretórios"""
    print("\n" + "="*60)
    print("📁 Verificando Diretórios")
    print("="*60 + "\n")
    
    from src.config import UPLOADS_DIR, LOGS_DIR, TEMP_DIR
    
    dirs = {
        "Uploads": UPLOADS_DIR,
        "Logs": LOGS_DIR,
        "Temp": TEMP_DIR,
    }
    
    all_ok = True
    
    for name, path in dirs.items():
        if path.exists():
            print(f"   ✅ {name}: {path}")
        else:
            print(f"   ⚠️  {name}: criando...")
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"      ✅ Criado: {path}")
            except Exception as e:
                print(f"      ❌ Erro: {e}")
                all_ok = False
    
    return all_ok


def seed_test_data():
    """Adiciona dados de teste"""
    print("\n" + "="*60)
    print("🌱 Adicionando Dados de Teste")
    print("="*60 + "\n")
    
    try:
        from src.database import get_db_context
        from sqlalchemy import text
        
        with get_db_context() as db:
            # Verificar se já tem FAQs
            result = db.execute(text("SELECT COUNT(*) FROM faq_respostas")).fetchone()
            
            if result[0] > 0:
                print(f"✅ FAQ já possui {result[0]} respostas cadastradas")
            else:
                print("⚠️  FAQ vazio, adicionando respostas padrão...")
                
                faqs = [
                    ("preco", '["preço", "valor", "quanto"]', 'Qual o preço?', 
                     'Os preços variam conforme o modelo. Acesse nosso site ou me envie uma mensagem! 📱'),
                    ("estoque", '["disponível", "estoque", "tem"]', 'Tem disponível?',
                     'Verifico a disponibilidade para você! Me envie o modelo de interesse. 📦'),
                    ("entrega", '["entrega", "frete", "prazo"]', 'Qual o prazo?',
                     'O prazo varia por região. Me passa seu CEP? 🚚'),
                    ("obrigado", '["obrigado", "valeu", "thanks"]', 'Obrigado!',
                     'Eu que agradeço! 😊'),
                ]
                
                for categoria, palavras, pergunta, resposta in faqs:
                    db.execute(
                        text("""
                            INSERT INTO faq_respostas 
                            (categoria, palavras_chave, pergunta_exemplo, resposta, ativo)
                            VALUES (:cat, :words, :question, :answer, 1)
                        """),
                        {
                            "cat": categoria,
                            "words": palavras,
                            "question": pergunta,
                            "answer": resposta
                        }
                    )
                
                db.commit()
                print("✅ FAQs adicionados com sucesso")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao adicionar dados: {str(e)}")
        return False


def check_imports():
    """Verifica se todos os módulos podem ser importados"""
    print("\n" + "="*60)
    print("📦 Verificando Importações")
    print("="*60 + "\n")
    
    modules = {
        "Config": "from src.config import settings",
        "Database": "from src.database import init_db",
        "Models": "from src.models.post import Post",
        "Queue Manager": "from src.services.queue_manager import QueueManager",
        "Comment Manager": "from src.services.comment_manager import CommentManager",
        "Content Manager": "from src.services.content_manager import ContentManager",
        "Integrations": "from src.integrations.factory import AdapterFactory",
        "API": "from src.api.main import app",
        "Scheduler": "from src.scheduler.jobs import BotScheduler",
    }
    
    all_ok = True
    
    for name, import_str in modules.items():
        try:
            exec(import_str)
            print(f"   ✅ {name}")
        except Exception as e:
            print(f"   ❌ {name}: {str(e)}")
            all_ok = False
    
    return all_ok


def main():
    """Função principal"""
    print("\n" + "🤖 Bot de Divulgação - Setup de Teste\n")
    
    results = {
        "Importações": False,
        "Ambiente": False,
        "Diretórios": False,
        "Banco de Dados": False,
        "Dados de Teste": False,
    }
    
    try:
        # 1. Verificar importações
        results["Importações"] = check_imports()
        
        # 2. Verificar ambiente
        results["Ambiente"] = check_environment()
        
        # 3. Verificar diretórios
        results["Diretórios"] = check_directories()
        
        # 4. Verificar banco
        results["Banco de Dados"] = check_database()
        
        # 5. Adicionar dados de teste
        results["Dados de Teste"] = seed_test_data()
        
    except Exception as e:
        print(f"\n❌ Erro durante setup: {str(e)}")
        return 1
    
    # Relatório final
    print("\n" + "="*60)
    print("📊 RELATÓRIO FINAL")
    print("="*60 + "\n")
    
    for check, passed in results.items():
        emoji = "✅" if passed else "❌"
        print(f"{emoji} {check}: {'OK' if passed else 'FALHOU'}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n📈 Resultado: {passed}/{total} verificações passaram")
    
    if passed == total:
        print("\n🎉 Ambiente pronto para testes!")
        print("\nPróximos passos:")
        print("1. python scripts/test_phase2.py")
        print("2. python src/api/main.py")
        print("3. python src/scheduler/jobs.py")
        return 0
    else:
        print("\n⚠️  Alguns problemas foram encontrados.")
        print("Corrija os erros acima antes de continuar.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
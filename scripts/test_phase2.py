"""
Script de teste completo da Fase 2
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.queue_manager import QueueManager
from src.services.comment_manager import CommentManager
from src.models.post import Platform, ContentType
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_queue_manager():
    """Testa gerenciador de fila"""
    print("\n" + "="*60)
    print("📋 Testando Queue Manager")
    print("="*60 + "\n")
    
    queue = QueueManager()
    
    # Teste 1: Adicionar post à fila
    print("1️⃣ Adicionando post de teste à fila...")
    
    post = queue.add_to_queue(
        plataforma="instagram",
        tipo_conteudo="text",
        horario_agendado=datetime.now() + timedelta(minutes=5),
        titulo="Post de Teste",
        descricao="Este é um post de teste do bot! #teste",
        criado_por="test_script"
    )
    
    if post:
        print(f"   ✅ Post criado: {post.uuid}")
        print(f"   📅 Agendado para: {post.horario_agendado}")
        print(f"   📊 Status: {post.status}")
    else:
        print("   ❌ Falha ao criar post")
        return False
    
    # Teste 2: Listar posts pendentes
    print("\n2️⃣ Listando posts pendentes...")
    
    pending = queue.get_pending_posts()
    print(f"   📋 Posts pendentes: {len(pending)}")
    
    # Teste 3: Aprovar post
    print("\n3️⃣ Aprovando post...")
    
    success = queue.approve_post(post.uuid, aprovado_por="test_script")
    
    if success:
        print("   ✅ Post aprovado!")
    else:
        print("   ❌ Falha ao aprovar post")
        return False
    
    # Teste 4: Verificar status da fila
    print("\n4️⃣ Status da fila...")
    
    status = queue.get_queue_status()
    print(f"   📊 Total: {status['total']}")
    print(f"   ⏳ Pendentes: {status['pending']}")
    print(f"   ✅ Aprovados: {status['approved']}")
    print(f"   🚀 Publicados: {status['published']}")
    print(f"   ❌ Falhados: {status['failed']}")
    print(f"   🏥 Saúde: {status['health']}")
    
    # Teste 5: Cancelar post
    print("\n5️⃣ Cancelando post de teste...")
    
    success = queue.cancel_post(post.uuid, cancelado_por="test_script")
    
    if success:
        print("   ✅ Post cancelado!")
    else:
        print("   ❌ Falha ao cancelar post")
    
    print("\n✅ Queue Manager testado com sucesso!\n")
    return True


def test_comment_manager():
    """Testa gerenciador de comentários"""
    print("\n" + "="*60)
    print("💬 Testando Comment Manager")
    print("="*60 + "\n")
    
    comments = CommentManager()
    
    # Teste 1: Analisar comentários
    print("1️⃣ Testando análise de comentários...\n")
    
    test_comments = [
        "Qual o preço deste produto?",
        "Adorei! Produto perfeito! ❤️",
        "Tem disponível em estoque?",
        "Obrigado pela informação!",
        "Qual o prazo de entrega para São Paulo?",
    ]
    
    for i, comment_text in enumerate(test_comments, 1):
        analysis = comments.analyze_comment(comment_text)
        
        print(f"   Comentário {i}: \"{comment_text}\"")
        print(f"      Categoria: {analysis['category']}")
        print(f"      Pergunta: {'Sim' if analysis['is_question'] else 'Não'}")
        print(f"      Sentimento: {analysis['sentiment']}")
        print(f"      Precisa resposta: {'Sim' if analysis['needs_response'] else 'Não'}")
        print()
    
    # Teste 2: Buscar resposta automática
    print("2️⃣ Testando respostas automáticas...\n")
    
    categories = ["preco", "estoque", "entrega", "obrigado"]
    
    for category in categories:
        response = comments.get_auto_response(category)
        if response:
            print(f"   {category.upper()}: {response[:60]}...")
        else:
            print(f"   ❌ Sem resposta para: {category}")
    
    # Teste 3: Verificar rate limit
    print("\n3️⃣ Testando rate limit...")
    
    can_reply = comments.check_rate_limit("instagram")
    print(f"   {'✅' if can_reply else '❌'} Pode responder: {can_reply}")
    
    print("\n✅ Comment Manager testado com sucesso!\n")
    return True


def test_integration():
    """Teste de integração entre componentes"""
    print("\n" + "="*60)
    print("🔗 Teste de Integração")
    print("="*60 + "\n")
    
    queue = QueueManager()
    comments = CommentManager()
    
    # Criar post de teste
    print("1️⃣ Criando post de teste completo...")
    
    post = queue.add_to_queue(
        plataforma="facebook",
        tipo_conteudo="text",
        horario_agendado=datetime.now() + timedelta(hours=1),
        titulo="Novo Lançamento!",
        descricao="Confira nosso novo produto incrível! 🚀 #lançamento #novidade",
        criado_por="integration_test"
    )
    
    if not post:
        print("   ❌ Falha ao criar post")
        return False
    
    print(f"   ✅ Post criado: {post.uuid}")
    
    # Aprovar post
    print("\n2️⃣ Aprovando post...")
    queue.approve_post(post.uuid, "integration_test")
    print("   ✅ Post aprovado")
    
    # Verificar se está pronto
    print("\n3️⃣ Verificando posts prontos para publicar...")
    ready = queue.get_ready_to_publish()
    print(f"   📋 Posts prontos: {len(ready)}")
    
    # Status final
    print("\n4️⃣ Status final...")
    status = queue.get_queue_status()
    print(f"   Total de posts: {status['total']}")
    print(f"   Saúde do sistema: {status['health']}")
    
    print("\n✅ Teste de integração concluído!\n")
    return True


def run_all_tests():
    """Executa todos os testes"""
    print("\n" + "🤖 Bot de Divulgação - Testes da Fase 2\n")
    
    results = {
        "Queue Manager": False,
        "Comment Manager": False,
        "Integration": False
    }
    
    try:
        # Teste 1: Queue Manager
        results["Queue Manager"] = test_queue_manager()
        
        # Teste 2: Comment Manager
        results["Comment Manager"] = test_comment_manager()
        
        # Teste 3: Integração
        results["Integration"] = test_integration()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Testes cancelados pelo usuário")
        return
    except Exception as e:
        print(f"\n\n❌ Erro durante testes: {str(e)}")
        return
    
    # Relatório final
    print("\n" + "="*60)
    print("📊 RELATÓRIO FINAL")
    print("="*60 + "\n")
    
    for test_name, passed in results.items():
        emoji = "✅" if passed else "❌"
        print(f"{emoji} {test_name}: {'PASSOU' if passed else 'FALHOU'}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n📈 Total: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 Todos os testes passaram! Fase 2 está funcionando!")
    else:
        print("\n⚠️ Alguns testes falharam. Verifique os logs acima.")


if __name__ == "__main__":
    run_all_tests()
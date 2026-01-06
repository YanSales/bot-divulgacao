"""
Script para inicializar o banco de dados
Cria tabelas e insere dados iniciais
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import init_db, get_db_context, Base, engine
from src.models.post import Post
from src.models.lead import Lead
from src.utils.logger import get_logger
from sqlalchemy import text

logger = get_logger(__name__)


def create_tables():
    """Cria todas as tabelas"""
    logger.info("Criando tabelas...")
    init_db()
    logger.info("✅ Tabelas criadas com sucesso!")


def insert_initial_data():
    """Insere dados iniciais no banco"""
    logger.info("Inserindo dados iniciais...")
    
    with get_db_context() as db:
        # Verificar se já tem dados
        if db.query(Post).first() is not None:
            logger.info("Banco já possui dados. Pulando inserção inicial.")
            return
        
        # Inserir configurações iniciais
        configs_sql = """
        CREATE TABLE IF NOT EXISTS configuracoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave VARCHAR(100) UNIQUE NOT NULL,
            valor TEXT NOT NULL,
            tipo VARCHAR(20) DEFAULT 'string',
            descricao TEXT,
            atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        INSERT OR IGNORE INTO configuracoes (chave, valor, tipo, descricao) VALUES
        ('horarios_publicacao', '["07:30", "12:30", "17:30"]', 'json', 'Horários diários de publicação'),
        ('analise_horarios_ativa', 'true', 'boolean', 'Análise automática de melhores horários'),
        ('modo_operacao', 'semi-automatic', 'string', 'Modo de operação do bot'),
        ('limite_comentarios_hora', '30', 'int', 'Máximo de comentários por hora'),
        ('limite_mensagens_dia', '100', 'int', 'Máximo de mensagens por dia'),
        ('plataformas_ativas', '{"instagram": true, "facebook": true, "twitter": true, "youtube": true, "whatsapp": true}', 'json', 'Plataformas habilitadas');
        """
        
        # Tabela de métricas
        metricas_sql = """
        CREATE TABLE IF NOT EXISTS metricas_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_uuid VARCHAR(36) NOT NULL,
            plataforma VARCHAR(20) NOT NULL,
            data_coleta DATETIME NOT NULL,
            curtidas INTEGER DEFAULT 0,
            comentarios INTEGER DEFAULT 0,
            compartilhamentos INTEGER DEFAULT 0,
            salvamentos INTEGER DEFAULT 0,
            alcance INTEGER DEFAULT 0,
            impressoes INTEGER DEFAULT 0,
            cliques_link INTEGER DEFAULT 0,
            taxa_engajamento FLOAT,
            FOREIGN KEY (post_uuid) REFERENCES posts_agendados(uuid)
        );
        
        CREATE INDEX IF NOT EXISTS idx_metricas_post_data ON metricas_posts(post_uuid, data_coleta);
        """
        
        # Tabela de interações
        interacoes_sql = """
        CREATE TABLE IF NOT EXISTS interacoes_usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plataforma VARCHAR(20) NOT NULL,
            usuario_id_externo VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            tipo_interacao VARCHAR(50) NOT NULL,
            post_uuid VARCHAR(36),
            conteudo TEXT,
            timestamp DATETIME NOT NULL,
            respondido BOOLEAN DEFAULT FALSE,
            resposta_automatica TEXT,
            respondido_em DATETIME,
            sentimento VARCHAR(20),
            prioridade INTEGER DEFAULT 0,
            FOREIGN KEY (post_uuid) REFERENCES posts_agendados(uuid)
        );
        
        CREATE INDEX IF NOT EXISTS idx_interacao_usuario ON interacoes_usuarios(usuario_id_externo, plataforma);
        CREATE INDEX IF NOT EXISTS idx_interacao_respondido ON interacoes_usuarios(respondido, prioridade);
        """
        
        # Tabela de mensagens automáticas
        mensagens_sql = """
        CREATE TABLE IF NOT EXISTS mensagens_automaticas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_uuid VARCHAR(36),
            plataforma VARCHAR(20) NOT NULL,
            destinatario VARCHAR(200) NOT NULL,
            template_usado VARCHAR(100),
            mensagem TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            agendada_para DATETIME,
            enviada_em DATETIME,
            erro_mensagem TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_uuid) REFERENCES leads(uuid)
        );
        
        CREATE INDEX IF NOT EXISTS idx_msg_status ON mensagens_automaticas(status, agendada_para);
        """
        
        # Tabela de FAQ
        faq_sql = """
        CREATE TABLE IF NOT EXISTS faq_respostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria VARCHAR(100) NOT NULL,
            palavras_chave TEXT NOT NULL,
            pergunta_exemplo TEXT,
            resposta TEXT NOT NULL,
            ativo BOOLEAN DEFAULT TRUE,
            vezes_usado INTEGER DEFAULT 0,
            taxa_satisfacao FLOAT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
            atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        INSERT INTO faq_respostas (categoria, palavras_chave, pergunta_exemplo, resposta) VALUES
        ('preco', '["preço", "valor", "quanto custa", "quanto é", "preço"]', 'Qual o preço?', 
         'Olá! Os preços variam conforme o modelo. Acesse nosso catálogo completo ou envie uma mensagem para falar com um consultor! 📱'),
        ('estoque', '["disponível", "tem em estoque", "disponibilidade", "quando chega", "tem"]', 'Tem disponível?',
         'Verificamos a disponibilidade em tempo real! Me envie uma mensagem direta com o modelo de seu interesse que verifico para você. 📦'),
        ('entrega', '["entrega", "frete", "prazo", "demora", "envio", "correios"]', 'Qual o prazo de entrega?',
         'Trabalhamos com entregas para todo Brasil! O prazo varia de acordo com sua região. Me passa seu CEP que calculo para você? 🚚'),
        ('garantia', '["garantia", "defeito", "problema", "troca", "assistência"]', 'Tem garantia?',
         'Sim! Todos nossos produtos têm garantia do fabricante. Te envio os detalhes por mensagem? 🛡️'),
        ('pagamento', '["pagamento", "parcela", "cartão", "pix", "boleto"]', 'Formas de pagamento?',
         'Aceitamos Pix, cartão de crédito em até 12x sem juros e boleto! Qual forma prefere? 💳'),
        ('obrigado', '["obrigado", "valeu", "thanks", "obrigada"]', 'Obrigado!',
         'Eu que agradeço! Estamos sempre à disposição. 😊');
        """
        
        # Tabela de logs
        logs_sql = """
        CREATE TABLE IF NOT EXISTS logs_sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nivel VARCHAR(20) NOT NULL,
            modulo VARCHAR(100),
            mensagem TEXT NOT NULL,
            detalhes TEXT,
            usuario VARCHAR(100),
            ip_address VARCHAR(50),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_logs_nivel ON logs_sistema(nivel, timestamp);
        """
        
        # Executar SQLs
        for sql_script in [configs_sql, metricas_sql, interacoes_sql, mensagens_sql, faq_sql, logs_sql]:
            for statement in sql_script.split(';'):
                if statement.strip():
                    db.execute(text(statement))
        
        db.commit()
        logger.info("✅ Dados iniciais inseridos com sucesso!")


def show_tables():
    """Mostra todas as tabelas criadas"""
    logger.info("Tabelas no banco de dados:")
    
    with get_db_context() as db:
        # SQLite
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result]
        
        for i, table in enumerate(tables, 1):
            logger.info(f"  {i}. {table}")


def main():
    """Função principal"""
    logger.info("=" * 60)
    logger.info("Inicializando Banco de Dados do Bot de Divulgação")
    logger.info("=" * 60)
    
    try:
        # Criar tabelas
        create_tables()
        
        # Inserir dados iniciais
        insert_initial_data()
        
        # Mostrar tabelas criadas
        show_tables()
        
        logger.info("=" * 60)
        logger.info("✅ Banco de dados inicializado com sucesso!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
"""
Script para criar a tabela comments

"""
import sys
from pathlib import Path
from sqlalchemy import text

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_db_context
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_comments_table():
    logger.info("Criando tabela comments (se não existir)...")

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid VARCHAR(36) UNIQUE NOT NULL,
        post_uuid VARCHAR(36) NOT NULL,
        texto TEXT NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
        criado_em DATETIME NOT NULL,
        criado_por VARCHAR(100) NOT NULL,
        publicado_em DATETIME,
        erro_publicacao TEXT,
        FOREIGN KEY (post_uuid) REFERENCES posts_agendados(uuid)
    );
    """

    indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_comments_uuid ON comments(uuid);",
        "CREATE INDEX IF NOT EXISTS idx_comments_post_uuid ON comments(post_uuid);",
        "CREATE INDEX IF NOT EXISTS idx_comments_status ON comments(status);",
    ]

    with get_db_context() as db:
        db.execute(text(create_table_sql))

        for idx_sql in indexes_sql:
            db.execute(text(idx_sql))

        db.commit()

    logger.info("✅ Tabela comments criada/verificada com sucesso!")


def show_tables():
    logger.info("Tabelas atuais no banco:")

    with get_db_context() as db:
        result = db.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        for row in result.fetchall():
            logger.info(f" - {row[0]}")


def main():
    logger.info("=" * 60)
    logger.info("Inicialização da tabela COMMENTS")
    logger.info("=" * 60)

    try:
        create_comments_table()
        show_tables()

        logger.info("=" * 60)
        logger.info("✅ Script finalizado com sucesso")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("❌ Erro ao criar tabela comments", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()

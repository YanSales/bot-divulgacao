"""
Scheduler para tarefas automatizadas
"""
import time
from datetime import datetime, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import and_, text

from src.services.queue_manager import QueueManager
from src.services.comment_manager import CommentManager
from src.services.content_manager import ContentManager
from src.database import get_db_context
from src.models.post import Post
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BotScheduler:
    def __init__(self):
        self.scheduler = BlockingScheduler()
        self.queue_manager = QueueManager()
        self.comment_manager = CommentManager()
        self.content_manager = ContentManager()
        logger.info("Scheduler inicializado")

    # ================= POSTS =================
    def check_and_publish_posts(self):
        logger.info("Verificando posts prontos para publicar...")

        try:
            posts = self.queue_manager.get_ready_to_publish()

            if not posts:
                logger.info("Nenhum post pronto para publicar")
                return

            logger.info(f"Encontrados {len(posts)} posts prontos")

            for post in posts:
                try:
                    logger.info(
                        f"Publicando post {post.uuid}",
                        plataforma=post.plataforma
                    )

                    # 🔥 CORREÇÃO CRÍTICA:
                    # publish_post recebe UUID (str), NÃO DTO
                    success = self.queue_manager.publish_post(post.uuid)

                    if success:
                        logger.info(f"✅ Post {post.uuid} publicado com sucesso!")
                    else:
                        logger.error(f"❌ Falha ao publicar post {post.uuid}")

                    time.sleep(5)

                except Exception as e:
                    logger.error(
                        f"Erro ao publicar post {post.uuid}",
                        error=str(e)
                    )

        except Exception as e:
            logger.error("Erro ao verificar posts", error=str(e))

    def retry_failed_posts(self):
        logger.info("Retentando posts falhados...")
        try:
            count = self.queue_manager.retry_failed_posts(max_retries=3)
            logger.info(f"Retentados {count} posts")
        except Exception as e:
            logger.error("Erro ao retentar posts", error=str(e))

    # ================= COMENTÁRIOS =================
    def process_comments(self):
        logger.info("Processando comentários...")

        try:
            with get_db_context() as db:
                recent_posts = db.query(Post).filter(
                    and_(
                        Post.status == "PUBLISHED",
                        Post.publicado_em >= datetime.now() - timedelta(days=1)
                    )
                ).all()

            if not recent_posts:
                logger.info("Nenhum post recente para processar")
                return

            for post in recent_posts:
                if not post.post_id_externo:
                    continue

                try:
                    self.comment_manager.process_comments(
                        platform=post.plataforma,
                        post_id=post.post_id_externo,
                        post_uuid=post.uuid,
                        auto_reply=True
                    )
                    time.sleep(3)

                except Exception as e:
                    logger.error(
                        f"Erro ao processar comentários do post {post.uuid}",
                        error=str(e)
                    )

        except Exception as e:
            logger.error("Erro ao processar comentários", error=str(e))

    # ================= MÉTRICAS =================
    def collect_metrics(self):
        logger.info("Coletando métricas...")

        try:
            from src.integrations.factory import AdapterFactory

            with get_db_context() as db:
                recent_posts = db.query(Post).filter(
                    and_(
                        Post.status == "PUBLISHED",
                        Post.publicado_em >= datetime.now() - timedelta(days=2)
                    )
                ).all()

            for post in recent_posts:
                if not post.post_id_externo:
                    continue

                try:
                    adapter = AdapterFactory.create(post.plataforma)
                    if not adapter:
                        continue

                    metrics = adapter.get_post_metrics(post.post_id_externo)

                    with get_db_context() as db:
                        db.execute(
                            text("""
                                INSERT INTO metricas_posts (
                                    post_uuid, plataforma, data_coleta,
                                    curtidas, comentarios, compartilhamentos,
                                    salvamentos, alcance, impressoes,
                                    taxa_engajamento
                                ) VALUES (
                                    :post_uuid, :plataforma, :data_coleta,
                                    :curtidas, :comentarios, :compartilhamentos,
                                    :salvamentos, :alcance, :impressoes,
                                    :taxa_engajamento
                                )
                            """),
                            {
                                "post_uuid": post.uuid,
                                "plataforma": post.plataforma,
                                "data_coleta": datetime.now(),
                                "curtidas": metrics.likes,
                                "comentarios": metrics.comments,
                                "compartilhamentos": metrics.shares,
                                "salvamentos": metrics.saves,
                                "alcance": metrics.reach,
                                "impressoes": metrics.impressions,
                                "taxa_engajamento": metrics.engagement_rate
                            }
                        )
                        db.commit()

                    time.sleep(2)

                except Exception as e:
                    logger.error(
                        f"Erro ao coletar métricas do post {post.uuid}",
                        error=str(e)
                    )

        except Exception as e:
            logger.error("Erro ao coletar métricas", error=str(e))

    # ================= MANUTENÇÃO =================
    def cleanup_temp_files(self):
        logger.info("Limpando arquivos temporários...")
        try:
            self.content_manager.cleanup_temp()
            logger.info("Limpeza concluída")
        except Exception as e:
            logger.error("Erro na limpeza", error=str(e))

    def health_check(self):
        try:
            queue_status = self.queue_manager.get_queue_status()
            logger.info("Health check", **queue_status)
        except Exception as e:
            logger.error("Erro no health check", error=str(e))

    # ================= SETUP =================
    def setup_jobs(self):
        self.scheduler.add_job(self.check_and_publish_posts, "interval", minutes=5)
        self.scheduler.add_job(self.process_comments, "interval", minutes=10)
        self.scheduler.add_job(self.retry_failed_posts, "interval", hours=1)
        self.scheduler.add_job(self.cleanup_temp_files, CronTrigger(hour=3, minute=0))
        self.scheduler.add_job(self.collect_metrics, "interval", hours=6)
        self.scheduler.add_job(self.health_check, "interval", minutes=15)

    def start(self):
        logger.info("🤖 Bot de Divulgação - Scheduler")
        logger.info(f"Ambiente: {settings.ENVIRONMENT}")
        logger.info(f"Modo: {settings.OPERATION_MODE}")

        self.setup_jobs()
        self.scheduler.start()


def main():
    BotScheduler().start()


if __name__ == "__main__":
    main()

"""
Gerenciador de fila de publicações
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy import and_

from src.database import get_db_context
from src.models.post import Post, PostStatus, Platform
from src.services.content_manager import ContentManager
from src.integrations.base import MediaType
from src.utils.logger import get_logger, audit_logger
from src.dtos.post_dto import PostDTO

logger = get_logger(__name__)


class QueueManager:
    """Gerencia fila de posts agendados"""

    def __init__(self):
        self.content_manager = ContentManager()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _to_dto(self, post: Post) -> PostDTO:
        return PostDTO(
            uuid=post.uuid,
            plataforma=post.plataforma.value,
            tipo_conteudo=post.tipo_conteudo,
            status=post.status.value,
            horario_agendado=post.horario_agendado,
            criado_em=post.criado_em,
            titulo=post.titulo,
            descricao=post.descricao,
            midia_url=post.midia_url
        )

    # ------------------------------------------------------------------
    # Queue
    # ------------------------------------------------------------------
    def add_to_queue(
        self,
        plataforma: str,
        tipo_conteudo: str,
        horario_agendado: datetime,
        titulo: Optional[str] = None,
        descricao: Optional[str] = None,
        hashtags: Optional[str] = None,
        midia_url: Optional[str] = None,
        criado_por: str = "system"
    ) -> Optional[PostDTO]:

        try:
            with get_db_context() as db:
                post = Post(
                    plataforma=Platform(plataforma.lower()),
                    tipo_conteudo=tipo_conteudo,
                    titulo=titulo,
                    descricao=descricao,
                    hashtags=hashtags,
                    midia_url=midia_url,
                    horario_agendado=horario_agendado,
                    status=PostStatus.PENDING,
                    criado_por=criado_por
                )

                db.add(post)
                db.commit()
                db.refresh(post)

                logger.info(
                    "Post adicionado à fila",
                    post_uuid=post.uuid,
                    plataforma=plataforma,
                    horario=horario_agendado.isoformat()
                )

                audit_logger.log(
                    action="ADD_TO_QUEUE",
                    user=criado_por,
                    details={
                        "post_uuid": post.uuid,
                        "plataforma": plataforma,
                        "horario_agendado": horario_agendado.isoformat()
                    }
                )

                return self._to_dto(post)

        except Exception as e:
            logger.error("Erro ao adicionar post à fila", error=str(e))
            return None

    def get_pending_posts(
        self,
        plataforma: Optional[str] = None,
        limit: int = 100
    ) -> List[PostDTO]:

        try:
            with get_db_context() as db:
                query = db.query(Post).filter(Post.status == PostStatus.PENDING)

                if plataforma:
                    query = query.filter(Post.plataforma == Platform(plataforma.lower()))

                posts = query.order_by(Post.horario_agendado).limit(limit).all()
                return [self._to_dto(p) for p in posts]

        except Exception as e:
            logger.error("Erro ao obter posts pendentes", error=str(e))
            return []

    def get_ready_to_publish(self) -> List[PostDTO]:
        try:
            with get_db_context() as db:
                now = datetime.now()

                posts = db.query(Post).filter(
                    and_(
                        Post.status == PostStatus.APPROVED,
                        Post.horario_agendado <= now
                    )
                ).order_by(Post.horario_agendado).all()

                return [self._to_dto(p) for p in posts]

        except Exception as e:
            logger.error("Erro ao obter posts prontos", error=str(e))
            return []

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def approve_post(self, post_uuid: str, aprovado_por: str) -> bool:
        try:
            with get_db_context() as db:
                post = db.query(Post).filter(Post.uuid == post_uuid).first()
                if not post:
                    return False

                post.status = PostStatus.APPROVED
                post.aprovado_por = aprovado_por
                post.aprovado_em = datetime.now()
                db.commit()

                audit_logger.log(
                    action="APPROVE_POST",
                    user=aprovado_por,
                    details={"post_uuid": post_uuid}
                )

                return True

        except Exception as e:
            logger.error("Erro ao aprovar post", error=str(e))
            return False

    def publish_post(self, post_uuid: str) -> bool:
        try:
            with get_db_context() as db:
                post = db.query(Post).filter(Post.uuid == post_uuid).first()
                if not post:
                    return False

                post.status = PostStatus.PUBLISHING
                db.commit()

                media_type = MediaType(post.tipo_conteudo)

                result = self.content_manager.publish_content(
                    platform=post.plataforma.value,
                    media_type=media_type,
                    file_path=post.midia_url,
                    caption=post.descricao or ""
                )

                if result.success:
                    post.mark_as_published(result.post_id)
                    db.commit()
                    return True

                post.mark_as_failed(result.error_message)
                db.commit()
                return False

        except Exception as e:
            logger.error("Erro ao publicar post", error=str(e))
            return False

    def cancel_post(self, post_uuid: str, cancelado_por: str) -> bool:
        try:
            with get_db_context() as db:
                post = db.query(Post).filter(Post.uuid == post_uuid).first()
                if not post or post.status == PostStatus.PUBLISHED:
                    return False

                post.status = PostStatus.CANCELLED
                db.commit()

                audit_logger.log(
                    action="CANCEL_POST",
                    user=cancelado_por,
                    details={"post_uuid": post_uuid}
                )

                return True

        except Exception as e:
            logger.error("Erro ao cancelar post", error=str(e))
            return False

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def get_queue_status(self) -> Dict:
        try:
            with get_db_context() as db:
                now = datetime.now()

                total = db.query(Post).count()
                failed = db.query(Post).filter(Post.status == PostStatus.FAILED).count()
                overdue = db.query(Post).filter(
                    and_(
                        Post.status == PostStatus.APPROVED,
                        Post.horario_agendado < now - timedelta(hours=1)
                    )
                ).count()

                return {
                    "total": total,
                    "pending": db.query(Post).filter(Post.status == PostStatus.PENDING).count(),
                    "approved": db.query(Post).filter(Post.status == PostStatus.APPROVED).count(),
                    "publishing": db.query(Post).filter(Post.status == PostStatus.PUBLISHING).count(),
                    "published": db.query(Post).filter(Post.status == PostStatus.PUBLISHED).count(),
                    "failed": failed,
                    "overdue": overdue,
                    "health": "ok" if failed < 5 and overdue < 3 else "warning"
                }

        except Exception as e:
            logger.error("Erro ao obter status da fila", error=str(e))
            return {"health": "error"}

"""
Gerenciador de comentários automáticos e CRUD interno de comentários
"""
from typing import List, Optional, Dict
from datetime import datetime
from uuid import uuid4
from sqlalchemy import text

from src.database import get_db_context
from src.integrations.factory import AdapterFactory
from src.utils.logger import get_logger
from src.config import settings
from src.dtos.comment_dto import CommentDTO

logger = get_logger(__name__)


class CommentManager:
    """Gerencia comentários internos e respostas automáticas"""

    def __init__(self):
        self.adapters = {}
        self.response_cache = {}
        self.rate_limit_counter = {}

    # ==========================================================
    # Helpers
    # ==========================================================

    def _to_dto(self, row) -> CommentDTO:
        return CommentDTO(
            uuid=row[0],
            post_uuid=row[1],
            content=row[2],
            status=row[3],
            created_at=row[4],
            created_by=row[5],
            platform="internal",
        )

    # ==========================================================
    # CRUD INTERNO
    # ==========================================================

    def create_comment(
        self,
        post_uuid: str,
        texto: str,
        criado_por: str,
    ) -> Optional[CommentDTO]:
        try:
            with get_db_context() as db:
                comment_uuid = str(uuid4())
                now = datetime.utcnow()

                db.execute(
                    text("""
                        INSERT INTO comments (
                            uuid,
                            post_uuid,
                            texto,
                            status,
                            criado_em,
                            criado_por
                        ) VALUES (
                            :uuid,
                            :post_uuid,
                            :texto,
                            'PENDING',
                            :criado_em,
                            :criado_por
                        )
                    """),
                    {
                        "uuid": comment_uuid,
                        "post_uuid": post_uuid,
                        "texto": texto,
                        "criado_em": now,
                        "criado_por": criado_por,
                    }
                )

                db.commit()

                return CommentDTO(
                    uuid=comment_uuid,
                    post_uuid=post_uuid,
                    content=texto,
                    status="PENDING",
                    created_at=now,
                    created_by=criado_por,
                    platform="internal",
                )

        except Exception as e:
            logger.exception("Erro ao criar comentário", error=str(e))
            return None

    # ==========================================================
    # LISTAGEM (Dashboard)
    # ==========================================================

    def get_pending_comments(self, limit: int = 20) -> List[CommentDTO]:
        try:
            with get_db_context() as db:
                result = db.execute(
                    text("""
                        SELECT
                            uuid,
                            post_uuid,
                            texto,
                            status,
                            criado_em,
                            criado_por
                        FROM comments
                        WHERE status = 'PENDING'
                        ORDER BY criado_em DESC
                        LIMIT :limit
                    """),
                    {"limit": limit}
                ).fetchall()

                return [self._to_dto(row) for row in result]

        except Exception as e:
            logger.error("Erro ao buscar comentários pendentes", error=str(e))
            return []

    # ==========================================================
    # ANÁLISE
    # ==========================================================

    def analyze_comment(self, comment_text: str) -> Dict:
        text_lower = comment_text.lower()

        categories = {
            "preco": ["preço", "valor", "quanto", "custa", "$", "r$"],
            "estoque": ["disponível", "estoque", "tem", "quando chega"],
            "entrega": ["entrega", "frete", "prazo", "demora", "envio"],
            "garantia": ["garantia", "defeito", "problema", "troca"],
            "pagamento": ["pagamento", "parcela", "cartão", "pix", "boleto"],
            "obrigado": ["obrigado", "valeu", "thanks", "obrigada"],
        }

        detected_category = None
        for category, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                detected_category = category
                break

        is_question = "?" in comment_text

        positive_words = ["adorei", "amei", "perfeito", "ótimo", "excelente", "top"]
        negative_words = ["ruim", "péssimo", "horrível", "decepcionado", "problema"]

        sentiment = "neutral"
        if any(word in text_lower for word in positive_words):
            sentiment = "positive"
        elif any(word in text_lower for word in negative_words):
            sentiment = "negative"

        return {
            "category": detected_category or "general",
            "is_question": is_question,
            "sentiment": sentiment,
            "needs_response": is_question or detected_category is not None,
        }

    # ==========================================================
    # RATE LIMIT
    # ==========================================================

    def check_rate_limit(self, platform: str) -> bool:
        now = datetime.now()
        hour_key = now.strftime("%Y-%m-%d-%H")
        key = f"{platform}:{hour_key}"

        self.rate_limit_counter.setdefault(key, 0)

        for old_key in list(self.rate_limit_counter.keys()):
            if old_key != key:
                del self.rate_limit_counter[old_key]

        if self.rate_limit_counter[key] >= settings.MAX_COMMENTS_PER_HOUR:
            logger.warning("Rate limit atingido", platform=platform)
            return False

        return True
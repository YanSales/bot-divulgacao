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

logger = get_logger(__name__)


class CommentManager:
    """Gerencia comentários internos e respostas automáticas"""

    def __init__(self):
        self.adapters = {}
        self.response_cache = {}
        self.rate_limit_counter = {}

    # ==========================================================
    # ADAPTER
    # ==========================================================

    def _get_adapter(self, platform: str):
        if platform not in self.adapters:
            self.adapters[platform] = AdapterFactory.create(platform)
        return self.adapters[platform]

    # ==========================================================
    # CRUD INTERNO DE COMMENTS (API)
    # ==========================================================

    def create_comment(
        self,
        post_uuid: str,
        texto: str,
        criado_por: str,
    ):
        """
        Cria um comentário interno vinculado a um post
        Usado pelo endpoint /comments
        """
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

                return type(
                    "Comment",
                    (),
                    {
                        "uuid": comment_uuid,
                        "post_uuid": post_uuid,
                        "texto": texto,
                        "status": "PENDING",
                        "criado_em": now,
                    },
                )

        except Exception as e:
            logger.exception("Erro ao criar comentário", error=str(e))
            return None

    # ==========================================================
    # ANÁLISE DE COMENTÁRIOS
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
    # AUTO RESPONSE
    # ==========================================================

    def get_auto_response(self, category: str) -> Optional[str]:
        try:
            with get_db_context() as db:
                result = db.execute(
                    text("""
                        SELECT resposta
                        FROM faq_respostas
                        WHERE categoria = :category
                        AND ativo = 1
                        ORDER BY vezes_usado ASC
                        LIMIT 1
                    """),
                    {"category": category},
                ).fetchone()

                if not result:
                    return None

                db.execute(
                    text("""
                        UPDATE faq_respostas
                        SET vezes_usado = vezes_usado + 1
                        WHERE categoria = :category
                    """),
                    {"category": category},
                )

                db.commit()
                return result[0]

        except Exception as e:
            logger.error("Erro ao buscar resposta automática", error=str(e))
            return None

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

    # ==========================================================
    # INTERAÇÕES
    # ==========================================================

    def is_already_replied(self, comment_id: str, platform: str) -> bool:
        try:
            with get_db_context() as db:
                result = db.execute(
                    text("""
                        SELECT COUNT(*)
                        FROM interacoes_usuarios
                        WHERE usuario_id_externo = :comment_id
                        AND plataforma = :platform
                        AND respondido = 1
                    """),
                    {"comment_id": comment_id, "platform": platform},
                ).fetchone()

                return result[0] > 0

        except Exception as e:
            logger.error("Erro ao verificar resposta", error=str(e))
            return False

    def save_interaction(
        self,
        platform: str,
        user_id: str,
        username: str,
        comment_text: str,
        comment_id: str,
        post_uuid: Optional[str] = None,
        auto_response: Optional[str] = None,
        sentiment: str = "neutral",
    ):
        try:
            with get_db_context() as db:
                db.execute(
                    text("""
                        INSERT INTO interacoes_usuarios (
                            plataforma,
                            usuario_id_externo,
                            username,
                            tipo_interacao,
                            post_uuid,
                            conteudo,
                            timestamp,
                            respondido,
                            resposta_automatica,
                            sentimento
                        ) VALUES (
                            :platform,
                            :user_id,
                            :username,
                            'comment',
                            :post_uuid,
                            :content,
                            :timestamp,
                            :respondido,
                            :response,
                            :sentiment
                        )
                    """),
                    {
                        "platform": platform,
                        "user_id": user_id,
                        "username": username,
                        "post_uuid": post_uuid,
                        "content": comment_text,
                        "timestamp": datetime.utcnow(),
                        "respondido": 1 if auto_response else 0,
                        "response": auto_response,
                        "sentiment": sentiment,
                    },
                )
                db.commit()

        except Exception as e:
            logger.error("Erro ao salvar interação", error=str(e))

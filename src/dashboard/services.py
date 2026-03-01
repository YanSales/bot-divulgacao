from typing import List
from sqlalchemy.orm import Session

from src.database import get_db_context
from src.models.post import Post
from src.dashboard.view_models import post_to_dict


def get_recent_posts(limit: int = 5) -> List[dict]:
    with get_db_context() as db:
        posts = (
            db.query(Post)
            .order_by(Post.criado_em.desc())
            .limit(limit)
            .all()
        )
        return [post_to_dict(p) for p in posts]


def get_posts(
    status: str | None = None,
    plataforma: str | None = None,
    limit: int = 50
) -> List[dict]:
    with get_db_context() as db:
        query = db.query(Post)

        if status:
            query = query.filter(Post.status == status)

        if plataforma:
            query = query.filter(Post.plataforma == plataforma)

        posts = (
            query
            .order_by(Post.horario_agendado.desc())
            .limit(limit)
            .all()
        )

        return [post_to_dict(p) for p in posts]

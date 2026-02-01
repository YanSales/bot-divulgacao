from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    Security,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.config import settings
from src.database import init_db, DatabaseHealthCheck
from src.services.queue_manager import QueueManager
from src.services.comment_manager import CommentManager
from src.utils.logger import get_logger
from src.models.post import Platform

# DTOs
from src.dtos.post_create_dto import PostCreateDTO
from src.dtos.post_response_dto import PostResponseDTO
from src.dtos.comment_create_dto import CommentCreateDTO
from src.dtos.comment_dto import CommentDTO
from src.dtos.health_dto import (
    HealthResponseDTO,
    DetailedHealthResponseDTO,
)

logger = get_logger(__name__)

# =========================================================
# AUTH
# =========================================================

security = HTTPBearer(auto_error=False)


def require_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key não fornecida",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Esquema inválido. Use Bearer",
        )

    if credentials.credentials != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key inválida",
        )

    return credentials.credentials


# =========================================================
# LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        logger.info("Banco inicializado")
    except Exception:
        logger.exception("Erro ao inicializar banco")
        raise
    yield


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Bot de Divulgação API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

queue_manager = QueueManager()
comment_manager = CommentManager()

# =========================================================
# HEALTH
# =========================================================

@app.get("/health", response_model=HealthResponseDTO)
async def health():
    return HealthResponseDTO(
        status="healthy",
        environment=settings.ENVIRONMENT,
        timestamp=datetime.utcnow(),
    )


@app.get(
    "/health/detailed",
    response_model=DetailedHealthResponseDTO,
)
async def detailed_health(api_key: str = Depends(require_api_key)):
    db_status = DatabaseHealthCheck.get_status()
    queue_status = queue_manager.get_queue_status()

    status_overall = (
        "healthy" if db_status.get("status") == "healthy" else "degraded"
    )

    return DetailedHealthResponseDTO(
        status=status_overall,
        database=db_status,
        queue=queue_status,
        timestamp=datetime.utcnow(),
    )


# =========================================================
# POSTS CRUD
# =========================================================

@app.post(
    "/api/v1/posts",
    response_model=PostResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(
    post: PostCreateDTO,
    api_key: str = Depends(require_api_key),
):
    try:
        try:
            Platform(post.plataforma.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Plataforma inválida: {post.plataforma}",
            )

        created = queue_manager.add_to_queue(
            plataforma=post.plataforma,
            tipo_conteudo=post.tipo_conteudo,
            horario_agendado=post.horario_agendado,
            titulo=post.titulo,
            descricao=post.descricao,
            hashtags=post.hashtags,
            midia_url=post.midia_url,
            criado_por=api_key,
        )

        if not created:
            raise HTTPException(
                status_code=500,
                detail="Falha ao criar post",
            )

        return PostResponseDTO.model_validate(created)

    except HTTPException:
        raise
    except Exception:
        logger.exception("Erro ao criar post")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao criar post",
        )


@app.get(
    "/api/v1/posts",
    response_model=List[PostResponseDTO],
)
async def list_pending_posts(
    api_key: str = Depends(require_api_key),
):
    posts = queue_manager.get_pending_posts()
    return [PostResponseDTO.from_orm(p) for p in posts]


@app.post(
    "/api/v1/posts/{post_uuid}/approve",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def approve_post(
    post_uuid: str,
    api_key: str = Depends(require_api_key),
):
    success = queue_manager.approve_post(post_uuid, api_key)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Post não encontrado",
        )


@app.delete(
    "/api/v1/posts/{post_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_post(
    post_uuid: str,
    api_key: str = Depends(require_api_key),
):
    success = queue_manager.cancel_post(post_uuid, api_key)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Post não encontrado ou já publicado",
        )


# =========================================================
# COMMENTS
# =========================================================

@app.post(
    "/api/v1/comments",
    response_model=CommentDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    comment: CommentCreateDTO,
    api_key: str = Depends(require_api_key),
):
    created = comment_manager.create_comment(
        post_uuid=comment.post_uuid,
        texto=comment.texto,
        criado_por=api_key,
    )

    if not created:
        raise HTTPException(
            status_code=500,
            detail="Falha ao criar comentário",
        )

    return CommentDTO(
        uuid=str(created.uuid),
        post_uuid=str(created.post_uuid),
        texto=created.texto,
        status=created.status,
        criado_em=created.criado_em,
    )


# =========================================================
# GLOBAL ERROR
# =========================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception("Erro não tratado")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erro interno do servidor",
            "error": str(exc) if settings.DEBUG else None,
        },
    )

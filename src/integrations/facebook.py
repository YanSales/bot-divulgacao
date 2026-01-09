"""
Adaptador para Facebook usando Graph API v24.0
Compatível com Nova Experiência de Páginas
"""

import requests
from typing import List, Optional, Dict
from datetime import datetime

from src.integrations.base import (
    PlatformAdapter,
    PostResult,
    Comment,
    PostMetrics,
    MediaType,
)
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FacebookAdapter(PlatformAdapter):
    BASE_URL = "https://graph.facebook.com/v24.0"

    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        if credentials is None:
            credentials = {
                "user_access_token": settings.FACEBOOK_USER_ACCESS_TOKEN,
                "page_id": settings.FACEBOOK_PAGE_ID,
            }

        super().__init__(credentials)

        self.user_access_token = credentials.get("user_access_token")
        self.page_id = credentials.get("page_id")
        self.page_access_token: Optional[str] = None

    # ------------------------------------------------------------------
    # AUTH
    # ------------------------------------------------------------------

    def authenticate(self) -> bool:
        if not self.user_access_token or not self.page_id:
            self.logger.error("User token ou Page ID não configurado")
            return False

        # 1️⃣ /me/accounts
        try:
            response = requests.get(
                f"{self.BASE_URL}/me/accounts",
                params={
                    "access_token": self.user_access_token,
                    "fields": "id,name,access_token",
                },
                timeout=15,
            )

            if response.status_code == 200:
                for page in response.json().get("data", []):
                    if page.get("id") == self.page_id:
                        self.page_access_token = page.get("access_token")
                        self.logger.info(
                            "Page access token obtido via /me/accounts",
                            page_name=page.get("name"),
                        )
                        return True
        except Exception as e:
            self.logger.warning("Falha /me/accounts", error=str(e))

        # 2️⃣ Fallback direto
        try:
            response = requests.get(
                f"{self.BASE_URL}/{self.page_id}",
                params={
                    "fields": "access_token,name",
                    "access_token": self.user_access_token,
                },
                timeout=15,
            )

            if response.status_code != 200:
                self.logger.error("Erro no fallback", error=response.text)
                return False

            self.page_access_token = response.json().get("access_token")

            if not self.page_access_token:
                self.logger.error("Fallback não retornou page token")
                return False

            self.logger.info("Page access token obtido via fallback direto")
            return True

        except Exception as e:
            self.logger.error("Erro na autenticação Facebook", error=str(e))
            return False

    # ------------------------------------------------------------------
    # PUBLISH
    # ------------------------------------------------------------------

    def publish_text(self, text: str, **kwargs) -> PostResult:
        if not self.page_access_token:
            return PostResult(False, "Não autenticado", "facebook")

        response = requests.post(
            f"{self.BASE_URL}/{self.page_id}/feed",
            data={
                "message": text,
                "access_token": self.page_access_token,
            },
            timeout=30,
        )

        if response.status_code == 200:
            return PostResult(True, response.json().get("id"), "facebook")

        return PostResult(False, response.text, "facebook")

    def publish_image(self, image_path: str, caption: str, **kwargs) -> PostResult:
        if not self.page_access_token:
            return PostResult(False, "Não autenticado", "facebook")

        valid, error = self.validate_media(image_path, MediaType.IMAGE)
        if not valid:
            return PostResult(False, error, "facebook")

        with open(image_path, "rb") as img:
            response = requests.post(
                f"{self.BASE_URL}/{self.page_id}/photos",
                files={"source": img},
                data={
                    "caption": caption,
                    "access_token": self.page_access_token,
                },
                timeout=60,
            )

        if response.status_code == 200:
            return PostResult(True, response.json().get("id"), "facebook")

        return PostResult(False, response.text, "facebook")

    def publish_video(self, video_path: str, caption: str, **kwargs) -> PostResult:
        """IMPLEMENTAÇÃO OBRIGATÓRIA"""
        if not self.page_access_token:
            return PostResult(False, "Não autenticado", "facebook")

        valid, error = self.validate_media(video_path, MediaType.VIDEO)
        if not valid:
            return PostResult(False, error, "facebook")

        with open(video_path, "rb") as video:
            response = requests.post(
                f"{self.BASE_URL}/{self.page_id}/videos",
                files={"source": video},
                data={
                    "description": caption,
                    "access_token": self.page_access_token,
                },
                timeout=300,
            )

        if response.status_code == 200:
            return PostResult(True, response.json().get("id"), "facebook")

        return PostResult(False, response.text, "facebook")

    # ------------------------------------------------------------------
    # METRICS
    # ------------------------------------------------------------------

    def get_post_metrics(self, post_id: str) -> PostMetrics:
        """IMPLEMENTAÇÃO OBRIGATÓRIA"""

        if not self.page_access_token:
            return PostMetrics(post_id=post_id)

        response = requests.get(
            f"{self.BASE_URL}/{post_id}",
            params={
                "fields": "likes.summary(true),comments.summary(true),shares",
                "access_token": self.page_access_token,
            },
            timeout=30,
        )

        if response.status_code != 200:
            return PostMetrics(post_id=post_id)

        data = response.json()

        return PostMetrics(
            post_id=post_id,
            likes=data.get("likes", {}).get("summary", {}).get("total_count", 0),
            comments=data.get("comments", {}).get("summary", {}).get("total_count", 0),
            shares=data.get("shares", {}).get("count", 0),
            collected_at=datetime.now(),
        )

    # ------------------------------------------------------------------
    # COMMENTS
    # ------------------------------------------------------------------

    def get_comments(self, post_id: str, limit: int = 100) -> List[Comment]:
        if not self.page_access_token:
            return []

        response = requests.get(
            f"{self.BASE_URL}/{post_id}/comments",
            params={
                "fields": "id,message,from,created_time",
                "limit": limit,
                "access_token": self.page_access_token,
            },
            timeout=30,
        )

        comments = []
        for item in response.json().get("data", []):
            comments.append(
                Comment(
                    id=item["id"],
                    text=item.get("message", ""),
                    username=item.get("from", {}).get("name", ""),
                    user_id=item.get("from", {}).get("id", ""),
                    post_id=post_id,
                    timestamp=datetime.fromisoformat(
                        item["created_time"].replace("Z", "+00:00")
                    ),
                )
            )
        return comments

    def reply_to_comment(self, comment_id: str, reply_text: str) -> bool:
        response = requests.post(
            f"{self.BASE_URL}/{comment_id}/comments",
            data={
                "message": reply_text,
                "access_token": self.page_access_token,
            },
            timeout=30,
        )
        return response.status_code == 200

    def delete_post(self, post_id: str) -> bool:
        response = requests.delete(
            f"{self.BASE_URL}/{post_id}",
            params={"access_token": self.page_access_token},
            timeout=30,
        )
        return response.status_code == 200

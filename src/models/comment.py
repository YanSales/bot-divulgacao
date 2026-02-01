import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from src.database import Base


class Comment(Base):
    __tablename__ = "comments"

    uuid = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_uuid = Column(String, ForeignKey("posts.uuid"), nullable=False)

    texto = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDING")

    criado_em = Column(DateTime, default=datetime.utcnow)
    criado_por = Column(String, nullable=False)

    post = relationship("Post", backref="comments")

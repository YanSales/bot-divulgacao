from pydantic import BaseModel


class CommentCreateDTO(BaseModel):
    post_uuid: str
    texto: str

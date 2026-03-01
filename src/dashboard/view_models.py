from src.models.post import Post


def post_to_dict(post: Post) -> dict:
    return {
        "id": post.id,
        "uuid": post.uuid,
        "titulo": post.titulo,
        "descricao": post.descricao,
        "plataforma": post.plataforma.value,
        "tipo_conteudo": post.tipo_conteudo.value,
        "status": post.status.value,
        "horario_agendado": post.horario_agendado,
        "criado_em": post.criado_em,
    }

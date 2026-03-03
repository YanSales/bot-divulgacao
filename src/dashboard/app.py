""" Dashboard principal do Bot de Divulgação """

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import settings, ENABLED_PLATFORMS
from src.services.queue_manager import QueueManager
from src.services.comment_manager import CommentManager
from src.dashboard.services import get_recent_posts, get_posts

# =============================
# Configuração da página
# =============================
st.set_page_config(
    page_title="Bot de Divulgação",
    page_icon="🤖",
    layout="wide",
)

# =============================
# Dark Mode Refinado
# =============================
st.markdown("""
<style>
body { background-color: #0f1117; color: #e6e6e6; }
.stApp { background-color: #0f1117; }
div[data-testid="stMetric"] {
    background-color: #1a1c24;
    padding: 16px;
    border-radius: 12px;
}
div[data-testid="stExpander"] {
    background-color: #1a1c24;
    border-radius: 12px;
}
.kanban-card {
    background-color: #1a1c24;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# =============================
# Serviços
# =============================
@st.cache_resource
def queue_manager():
    return QueueManager()

@st.cache_resource
def comment_manager():
    return CommentManager()

# =============================
# Sidebar
# =============================
def show_sidebar():
    with st.sidebar:
        st.markdown("# 🤖 Bot de Divulgação")
        st.markdown("---")

        st.markdown("### 🌎 Timezone")
        timezone = st.selectbox(
            "Fuso horário",
            ["America/Sao_Paulo", "UTC"],
            index=0
        )

        st.markdown("### ℹ️ Sistema")
        st.info(
            f"Ambiente: {settings.ENVIRONMENT}\n\n"
            f"Modo: {settings.OPERATION_MODE}"
        )

        st.markdown("### 📱 Plataformas")
        for p, enabled in ENABLED_PLATFORMS.items():
            st.write(f"{'✅' if enabled else '❌'} {p.capitalize()}")

        st.markdown("---")

        menu = st.radio(
            "Menu",
            ["Dashboard", "Posts", "Comentários", "Configurações"]
        )

    return menu, timezone

# =============================
# Dashboard
# =============================
def show_dashboard():
    st.title("📊 Dashboard")

    status = queue_manager().get_queue_status()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", status.get("total", 0))
    col2.metric("Pendentes", status.get("pending", 0))
    col3.metric("Aprovados", status.get("approved", 0))
    col4.metric("Publicados", status.get("published", 0))

    st.markdown("### 📝 Posts Recentes")
    posts = get_recent_posts()

    if not posts:
        st.info("Nenhum post encontrado")
        return

    for post in posts:
        with st.expander(f"{post['titulo'] or 'Sem título'}"):
            st.write(f"📱 Plataforma: {post['plataforma']}")
            st.write(f"🗂️ Status: {post['status']}")
            st.write(post["descricao"] or "")

# =============================
# Kanban
# =============================
def render_kanban(posts):
    st.markdown("## 📌 Visão Kanban")

    cols = st.columns(4)
    status_map = ["pending", "approved", "published", "failed"]

    for idx, status in enumerate(status_map):
        with cols[idx]:
            st.markdown(f"### {status.upper()}")
            for post in posts:
                if post["status"] == status:
                    st.markdown(
                        f"""
                        <div class="kanban-card">
                        <strong>{post['titulo'] or 'Sem título'}</strong><br>
                        {post['plataforma']}<br>
                        {post['horario_agendado'].strftime('%d/%m %H:%M')}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

# =============================
# Posts
# =============================
def show_posts(timezone):
    st.title("📝 Gerenciar Posts")

    tab_list, tab_create = st.tabs(["📋 Lista", "➕ Criar Post"])

    # =========================
    # LISTA
    # =========================
    with tab_list:

        posts = get_posts()
        render_kanban(posts)

        st.markdown("---")

        for post in posts:
            with st.container(border=True):

                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    st.markdown(f"### {post['titulo'] or 'Sem título'}")
                    st.caption((post["descricao"] or "")[:120])

                with col2:
                    st.write("📱", post["plataforma"])
                    st.write("🕒", post["horario_agendado"].strftime("%d/%m %H:%M"))

                with col3:
                    st.write("🗂️", post["status"])

                with col4:
                    if post["status"] == "pending":
                        if st.button("✅ Aprovar", key=f"ap_{post['uuid']}"):
                            queue_manager().approve_post(post["uuid"], "dashboard")
                            st.rerun()

                    if post["status"] in ["pending", "approved"]:
                        if st.button("❌ Cancelar", key=f"ca_{post['uuid']}"):
                            queue_manager().cancel_post(post["uuid"], "dashboard")
                            st.rerun()

                    if post["status"] in ["pending", "failed", "cancelled"]:
                        if st.button("🗑️ Excluir", key=f"de_{post['uuid']}"):
                            st.session_state["delete_confirm"] = post["uuid"]

        # Confirmação
        if "delete_confirm" in st.session_state:
            st.warning("⚠️ Confirmar exclusão do post selecionado")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("🗑️ Excluir definitivamente", type="primary"):
                    queue_manager().delete_post(
                        st.session_state["delete_confirm"],
                        "dashboard"
                    )
                    del st.session_state["delete_confirm"]
                    st.success("Post excluído com sucesso")
                    st.rerun()

            with col2:
                if st.button("Cancelar"):
                    del st.session_state["delete_confirm"]

    # =========================
    # CRIAR POST
    # =========================
    with tab_create:

        st.markdown("## ➕ Criar Novo Post")

        with st.form("create_post"):

            plataforma = st.selectbox(
                "Plataforma",
                [p.capitalize() for p, e in ENABLED_PLATFORMS.items() if e]
            )

            tipo = st.selectbox("Tipo de Conteúdo", ["text", "image", "video"])

            titulo = st.text_input("Título (opcional)")
            descricao = st.text_area("Descrição", height=150)

            st.markdown("### ⏰ Agendamento")

            col1, col2 = st.columns(2)

            with col1:
                data = st.date_input(
                    "Data",
                    min_value=datetime.now().date()
                )

            with col2:
                horario_input = st.time_input(
                    "Horário",
                    step=300
                )

            submit = st.form_submit_button("🚀 Criar Post")

            if submit:

                tz = ZoneInfo(timezone)
                horario = datetime.combine(data, horario_input)
                horario = horario.replace(tzinfo=tz)

                if horario <= datetime.now(tz):
                    st.error("Horário deve ser futuro")
                    return

                if not descricao.strip():
                    st.error("Descrição obrigatória")
                    return

                queue_manager().add_to_queue(
                    plataforma=plataforma.lower(),
                    tipo_conteudo=tipo,
                    horario_agendado=horario,
                    titulo=titulo or None,
                    descricao=descricao,
                    criado_por="dashboard"
                )

                st.success("Post criado com sucesso!")
                st.info("Status inicial: PENDING")
                st.rerun()

# =============================
# Comentários
# =============================
def show_comments():
    st.title("💬 Comentários")

    comments = comment_manager().get_pending_comments(limit=20)

    if not comments:
        st.success("Nenhum comentário pendente")
        return

    for c in comments:
        with st.expander(c["content"][:50]):
            st.write(c["content"])
            st.write(c["platform"])

# =============================
# Configurações
# =============================
def show_settings():
    st.title("⚙️ Configurações")
    st.json(settings.model_dump())

# =============================
# Main
# =============================
def main():
    page, timezone = show_sidebar()

    if page == "Dashboard":
        show_dashboard()
    elif page == "Posts":
        show_posts(timezone)
    elif page == "Comentários":
        show_comments()
    else:
        show_settings()

if __name__ == "__main__":
    main()
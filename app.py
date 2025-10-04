# app.py — TELA INICIAL COM LOGOS E BOTÕES DE NAVEGAÇÃO

import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="DGCE - Gestão de Compliance",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CABEÇALHO COM LOGOS E TÍTULO ---
col1, col2, col3 = st.columns([1, 3, 1])

with col1:
    # Logo SUDECAP (substitua pelo caminho real ou URL)
    st.image("https://via.placeholder.com/150x50?text=SUDECAP", width=150)

with col2:
    # Título centralizado
    st.markdown("""
    <div style="text-align: center; font-size: 28px; font-weight: bold; color: #0066cc;">
        DGCE<br>
        <span style="font-size: 18px; color: #009933;">DEPARTAMENTO DE GESTÃO DE COMPLIANCE E INTEGRIDADE DE EMPREENDIMENTOS</span>
    </div>
    """, unsafe_allow_html=True)

with col3:
    # Logo Prefeitura BH (substitua pelo caminho real ou URL)
    st.image("https://via.placeholder.com/150x50?text=BH+PREFEITURA", width=150)

# --- STATUS "EM CONSTRUÇÃO" ---
st.markdown("<div style='text-align: center; margin-top: -20px;'><img src='https://via.placeholder.com/30x30?text=🚧' alt='Em Construção'> EM CONSTRUÇÃO</div>", unsafe_allow_html=True)

st.markdown("---")

# --- BOTÕES DE NAVEGAÇÃO (LADO ESQUERDO) ---
st.markdown("### 📋 Navegação")

col_left, col_right = st.columns([1, 3])

with col_left:
    if st.button("⬅️ VOLTAR", key="voltar"):
        st.write("Voltar não faz nada aqui — pode ser implementado como redirecionamento futuro.")
    
    if st.button("📋 LISTA DE NOME", key="lista_nome"):
        st.info("Lista de nomes ainda não implementada.")

# --- BOTÕES DE ÁREAS (LADO DIREITO) ---
with col_right:
    st.markdown("### 🧭 Áreas")
    
    # Botões de navegação para páginas
    if st.button("📊 GEMOR — Gerência de Controle e Monitoramento de Riscos", key="gemor"):
        st.page_link("pages/1_GEMOR.py", label="", icon="")
    
    if st.button("✅ GECIE — Gerência de Conformidade e Integridade de Empreendimentos", key="gecie"):
        st.page_link("pages/2_GECIE.py", label="", icon="")
    
    if st.button("🔧 CONTROLES", key="controles"):
        st.page_link("pages/3_CONTROLES.py", label="", icon="")
    
    if st.button("🚀 AÇÕES", key="acoes"):
        st.page_link("pages/4_ACOES.py", label="", icon="")

# --- OPCIONAL: MENU LATERAL PARA NAVEGAÇÃO ADICIONAL ---
with st.sidebar:
    st.header("🧭 Navegação Rápida")
    st.page_link("app.py", label="🏠 Início", icon="🏠")
    st.page_link("pages/1_GEMOR.py", label="📊 GEMOR", icon="📈")
    st.page_link("pages/2_GECIE.py", label="✅ GECIE", icon="📉")
    st.page_link("pages/3_CONTROLES.py", label="🔧 Controles", icon="⚙️")
    st.page_link("pages/4_ACOES.py", label="🚀 Ações", icon="⚡")

# Hack para evitar erro de renderização
st.image("https://via.placeholder.com/1x1?text=0", width=1)

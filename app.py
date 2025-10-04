# app.py — Tela Inicial com Logo DGCE (CORRIGIDO)

import streamlit as st

st.set_page_config(
    page_title="DGCE - Gestão de Compliance",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CABEÇALHO COM LOGO ---
try:
    st.image("logo_dgce.png", use_column_width=True)
except:
    st.markdown("""
    <div style="text-align: center; padding: 10px;">
        <h1 style="color: #0066cc; margin: 0; font-size: 28px;">DGCE</h1>
        <p style="color: #009933; font-size: 16px; margin: 5px 0;">
            DEPARTAMENTO DE GESTÃO DE COMPLIANCE E INTEGRIDADE DE EMPREENDIMENTOS
        </p>
    </div>
    """, unsafe_allow_html=True)

# Status "EM CONSTRUÇÃO"
st.markdown("""
<div style="text-align: center; margin: -10px 0 20px 0;">
    <span style="display: inline-block; background-color: #2d3748; color: white; padding: 3px 10px; border-radius: 4px; font-size: 12px;">
        🚧 EM CONSTRUÇÃO
    </span>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# --- CONTEÚDO PRINCIPAL ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 Ações Rápidas")
    st.button("⬅️ VOLTAR", disabled=True)
    st.button("📋 LISTA DE NOME", disabled=True)

with col2:
    st.subheader("🧭 Áreas de Acesso")
    st.page_link("1_visao_geral.py", label="📊 Visão Geral (BI)", icon="📈")   # ✅ Sem "pages/"
    st.page_link("2_GMOR.py", label="🚧 GMOR", icon="🏗️")                   # ✅ Sem "pages/"
    st.page_link("3_GECIE.py", label="💰 GECIE", icon="📉")                  # ✅ Sem "pages/"
    st.page_link("4_CONTROLES.py", label="🔧 Controles", icon="⚙️")          # ✅ Sem "pages/"

# --- SIDEBAR ---
with st.sidebar:
    st.header("🧭 Navegação")
    st.markdown("🏠 **Início** (você está aqui)")
    st.markdown("---")
    st.page_link("1_visao_geral.py", label="📊 Visão Geral (BI)", icon="📈")   # ✅ Sem "pages/"
    st.page_link("2_GMOR.py", label="🚧 GMOR", icon="🏗️")                   # ✅ Sem "pages/"
    st.page_link("3_GECIE.py", label="💰 GECIE", icon="📉")                  # ✅ Sem "pages/"
    st.page_link("4_CONTROLES.py", label="🔧 Controles", icon="⚙️")          # ✅ Sem "pages/"

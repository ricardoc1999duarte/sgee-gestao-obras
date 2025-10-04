# app.py — TELA INICIAL COM CABEÇALHO E MENU MANUAL

import streamlit as st

st.set_page_config(
    page_title="DGCE - Gestão de Contratos",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CABEÇALHO ---
st.title("🏗️ DGCE - Diretoria de Gestão de Contratos e Engenharia")
st.markdown("---")

st.header("Bem-vindo ao Portal de Análise de Contratos")

st.markdown("""
<div style="background-color: #1e293b; padding: 15px; border-radius: 8px; color: #60a5fa;">
<strong>Navegue pela barra lateral à esquerda para acessar as diferentes áreas:</strong><br>
<ul>
<li><strong>Visão Geral</strong>: Painel completo com KPIs, gráficos e análise de todos os contratos.</li>
<li><strong>GMOR</strong>: Página dedicada à Gerência de Monitoramento de Obras.</li>
<li><strong>GECIE</strong>: Página dedicada à Gerência de Custos e Informações Estratégicas.</li>
</ul>
</div>
""", unsafe_allow_html=True)

# --- ADICIONA LINKS NO SIDEBAR MANUALMENTE ---
with st.sidebar:
    st.header("🧭 Navegação")
    st.page_link("app.py", label="🏠 Início", icon="🏠")
    st.page_link("pages/1_visao_geral.py", label="📊 Visão Geral", icon="📈")
    st.page_link("pages/2_GMOR.py", label="🚧 GMOR", icon="🏗️")
    st.page_link("pages/3_GECIE.py", label="💰 GECIE", icon="📉")

# Se quiser, pode adicionar um pequeno ícone ou contador
st.image("https://via.placeholder.com/1x1?text=0", width=1)  # hack para evitar erro de renderização

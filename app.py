# app.py
import streamlit as st

st.set_page_config(
    page_title="DGCE - Início",
    page_icon="🏗️",
    layout="centered"
)

st.title("DGCE - Diretoria de Gestão de Contratos e Engenharia")
st.write("---")

st.header("Bem-vindo ao Portal de Análise de Contratos")

st.info(
    """
    **Navegue pela barra lateral à esquerda para acessar as diferentes áreas:**

    - **Visão Geral:** Painel completo com KPIs, gráficos e análise de todos os contratos.
    - **GMOR:** Página dedicada à Gerência de Monitoramento de Obras.
    - **GECIE:** Página dedicada à Gerência de Custos e Informações Estratégicas.
    """
)

st.image(
    "https://www.rio.rj.gov.br/documents/81963/53332301/logo+prefeitura+2021.png/13437255-a530-9c6c-8043-e38f634b99c4?t=1615987334303",
    width=200
 )

# pages/1_visao_geral.py
import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# --- CONSTANTES E CONFIGURAÇÕES ---
FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
SETOR_COL = "Setor Responsavel"
RESP_COL = "Responsável"

st.set_page_config(page_title="Visão Geral - Contratos", layout="wide" )

# --- FUNÇÕES DE BACK-END ---
# (Cole aqui as funções: conectar_google_drive, baixar_arquivo_drive, carregar_dados, generate_instructions)
# O código delas não muda, então pode usar o da resposta anterior.
# É importante que elas estejam no topo deste arquivo.

@st.cache_resource
def conectar_google_drive():
    try:
        if "gcp_service_account" not in st.secrets: return None
        creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
        return build("drive", "v3", credentials=creds)
    except Exception: return None

@st.cache_data(ttl=3600)
def baixar_arquivo_drive(_service, file_id: str):
    if not _service: return None
    try:
        request = _service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done: _, done = downloader.next_chunk()
        buffer.seek(0)
        return buffer
    except Exception: return None

@st.cache_data(ttl=3600)
def carregar_dados(file_id):
    file_buffer = None
    try:
        file_buffer = open("SGEE+PO.xlsm", "rb")
    except FileNotFoundError:
        service = conectar_google_drive()
        if service: file_buffer = baixar_arquivo_drive(service, file_id)
    if file_buffer is None: return pd.DataFrame()
    try:
        df = pd.read_excel(file_buffer, sheet_name="SGEEePO", engine="openpyxl")
        date_cols = ["Data Fim Cnt Com Aditivos"]
        for col in date_cols:
            if col in df.columns: df[col] = pd.to_datetime(df[col], errors="coerce")
        num_cols = ["Total Contrato", "Total Medido Acumulado"]
        for col in num_cols:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        if "Data Fim Cnt Com Aditivos" in df.columns:
            df["Dias Restantes"] = (df["Data Fim Cnt Com Aditivos"] - pd.to_datetime("today")).dt.days
        if all(c in df.columns for c in ["Total Medido Acumulado", "Total Contrato"]):
            df["% executado"] = 0
            mask = df["Total Contrato"] > 0
            df.loc[mask, "% executado"] = (df.loc[mask, "Total Medido Acumulado"] / df.loc[mask, "Total Contrato"] * 100).fillna(0)
        return df.dropna(how="all")
    except Exception: return pd.DataFrame()

# --- LAYOUT DA APLICAÇÃO ---
st.title("Painel de Análise de Contratos")
df_calc = carregar_dados(FILE_ID)
if df_calc.empty:
    st.error("Não foi possível carregar os dados. Verifique o arquivo local ou as credenciais do Google Drive.")
    st.stop()

# --- SIDEBAR E FILTROS ---
with st.sidebar:
    st.header("⚙️ Filtros")
    setores_selecionados = []
    if SETOR_COL in df_calc.columns:
        setores_unicos = sorted(df_calc[SETOR_COL].dropna().unique())
        setores_selecionados = st.multiselect("Filtrar por Setor", setores_unicos, default=setores_unicos)
    
    responsaveis_selecionados = []
    if RESP_COL in df_calc.columns:
        responsaveis_unicos = sorted(df_calc[RESP_COL].dropna().unique())
        responsaveis_selecionados = st.multiselect("Filtrar por Responsável", responsaveis_unicos, default=responsaveis_unicos)

# Aplicando filtros
df_filtrado = df_calc.copy()
if setores_selecionados and SETOR_COL in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado[SETOR_COL].isin(setores_selecionados)]
if responsaveis_selecionados and RESP_COL in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado[RESP_COL].isin(responsaveis_selecionados)]

# --- PAINEL PRINCIPAL ---
st.header("📊 Indicadores Chave da Seleção")
# ... (Cole aqui a seção de KPIs da resposta anterior)

st.markdown("---")

# --- SEÇÃO DE GRÁFICOS (COM CORREÇÃO) ---
st.header("📈 Visualizações Gráficas")
if df_filtrado.empty:
    st.warning("Nenhum dado para exibir nos gráficos com os filtros atuais.")
else:
    col_graph1, col_graph2 = st.columns(2)
    with col_graph1:
        if "Valor Contrato" in df_filtrado.columns and SETOR_COL in df_filtrado.columns:
            st.subheader("Valor por Setor")
            # ... (código do gráfico de barras)
    with col_graph2:
        st.subheader("Execução vs. Prazos")
        # VERIFICAÇÃO PARA CORRIGIR O ERRO
        if all(c in df_filtrado.columns for c in ["% executado", "Dias Restantes"]) and not df_filtrado[["% executado", "Dias Restantes"]].isnull().all().all():
            fig_scatter = px.scatter(
                df_filtrado.dropna(subset=["% executado", "Dias Restantes"]),
                x="Dias Restantes", y="% executado",
                color=SETOR_COL if SETOR_COL in df_filtrado.columns else None,
                hover_data=["Nº Contrato", "Objeto", "Total Contrato"]
            )
            fig_scatter.add_vline(x=0, line_dash="dash", line_color="red")
            fig_scatter.add_hline(y=80, line_dash="dash", line_color="orange")
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Não há dados suficientes para gerar o gráfico de Execução vs. Prazos com os filtros atuais.")

st.markdown("---")
st.header("📋 Dados Detalhados da Seleção")
st.data_editor(df_filtrado, use_container_width=True, hide_index=True, num_rows="dynamic")

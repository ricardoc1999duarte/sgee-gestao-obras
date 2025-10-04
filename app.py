import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# --- CONSTANTES E CONFIGURAÇÕES GLOBAIS ---
FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
SETOR_COL = "Setor Responsavel"
RESP_COL = "Responsável"

st.set_page_config(page_title="SGEE+PO - Análise de Contratos", layout="wide", initial_sidebar_state="expanded" )

# --- FUNÇÕES DE BACK-END ---

@st.cache_resource
def conectar_google_drive():
    """Estabelece conexão com a API do Google Drive usando as credenciais do Streamlit."""
    try:
        # Verifica se a configuração do segredo do Streamlit existe
        if "gcp_service_account" not in st.secrets:
            st.error("Configuração 'gcp_service_account' não encontrada nos segredos do Streamlit.")
            return None
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPES
        )
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        st.error(f"❌ Erro de conexão com o Google Drive: {e}")
        return None

@st.cache_data(ttl=3600)
def baixar_arquivo_drive(_service, file_id: str):
    """Baixa um arquivo do Google Drive pelo seu ID e o retorna como um buffer em memória."""
    if not _service:
        return None
    try:
        request = _service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"❌ Erro ao baixar arquivo do Drive: {e}")
        return None

@st.cache_data(ttl=3600)
def carregar_dados(file_id):
    """Carrega os dados do Excel (local ou Drive) e faz o pré-processamento."""
    file_buffer = None
    try:
        file_buffer = open("SGEE+PO.xlsm", "rb")
        st.sidebar.info("Dados carregados do arquivo local 'SGEE+PO.xlsm'.")
    except FileNotFoundError:
        st.sidebar.warning("Arquivo local não encontrado. Tentando baixar do Google Drive...")
        service = conectar_google_drive()
        if service:
            file_buffer = baixar_arquivo_drive(service, file_id)
            if file_buffer:
                st.sidebar.success("Dados carregados com sucesso do Google Drive.")
        else:
            st.sidebar.error("Falha na conexão com o Drive. Não foi possível carregar os dados.")


    if file_buffer is None:
        st.error("❌ Falha crítica: Não foi possível carregar o ficheiro Excel de nenhuma fonte.")
        return pd.DataFrame()

    try:
        df = pd.read_excel(file_buffer, sheet_name="SGEEePO", engine="openpyxl")
        
        date_columns = ["Data Assin Cnt", "Data Inicio Cnt", "Data Fim Cnt Original", "Data Fim Cnt Com Aditivos", "Data Última Renovação"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        
        financial_columns = ["Total Contrato", "Valor Contrato", "Valor Aditivos", "Saldo Contratual", "Total Medido Acumulado"]
        for col in financial_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        if "% Aditivo" in df.columns:
            df["% Aditivo"] = pd.to_numeric(df["% Aditivo"], errors="coerce").fillna(0)
        
        if "Data Fim Cnt Com Aditivos" in df.columns:
            df["Dias Restantes"] = (df["Data Fim Cnt Com Aditivos"] - pd.to_datetime("today")).dt.days
        if "Total Medido Acumulado" in df.columns and "Total Contrato" in df.columns:
            df["% executado"] = (df["Total Contrato"] > 0).astype(int) * (df["Total Medido Acumulado"] / df["Total Contrato"] * 100).fillna(0)
        if "Saldo Contratual" in df.columns and "Total Contrato" in df.columns:
            df["% saldo"] = (df["Total Contrato"] > 0).astype(int) * (df["Saldo Contratual"] / df["Total Contrato"] * 100).fillna(0)

        return df.dropna(how="all")
    except Exception as e:
        st.error(f"❌ Falha ao processar a planilha: {e}")
        return pd.DataFrame()

def generate_instructions(df: pd.DataFrame) -> list[str]:
    """Gera uma lista de instruções e alertas com base em regras de negócio aplicadas ao DataFrame."""
    instructions = []
    if df.empty:
        return ["ℹ️ Nenhum dado para análise com os filtros selecionados."]
        
    df_copy = df.copy()

    # Regra 1: Índice Aditivo Global
    if all(c in df_copy.columns for c in ["Valor Contrato", "Valor Aditivos", "% Aditivo"]):
        df_filtered_aditivos = df_copy[df_copy["% Aditivo"] <= 50]
        total_valor_contrato = df_filtered_aditivos["Valor Contrato"].sum()
        total_valor_aditivos = df_filtered_aditivos["Valor Aditivos"].sum()
        indice_aditivo_global = (total_valor_aditivos / total_valor_contrato * 100) if total_valor_contrato != 0 else 0
        if indice_aditivo_global > 10:
            instructions.append(f"⚠️ **Alerta de Aditivos:** O Índice Aditivo Global ({indice_aditivo_global:.2f}%) está acima de 10%.")

    # Regra 2: Contratos Atrasados
    if "Dias Restantes" in df_copy.columns:
        contratos_atrasados = df_copy[df_copy["Dias Restantes"] < 0].shape[0]
        if contratos_atrasados > 0:
            instructions.append(f"⏰ **Atrasos Identificados:** Existem {contratos_atrasados} contratos com prazo expirado.")

    # Regra 3: Baixo % Executado
    if "% executado" in df_copy.columns:
        contratos_baixo_execucao = df_copy[(df_copy["% executado"] > 0) & (df_copy["% executado"] < 20)].shape[0]
        if contratos_baixo_execucao > 0:
            instructions.append(f"📉 **Baixa Execução:** {contratos_baixo_execucao} contratos apresentam execução financeira entre 1% e 20%.")

    # Regra 4: Contratos na Zona de Risco (Atrasado e Baixa Execução)
    if all(c in df_copy.columns for c in ["Dias Restantes", "% executado"]):
        contratos_risco = df_copy[(df_copy["Dias Restantes"] < 0) & (df_copy["% executado"] < 80)].shape[0]
        if contratos_risco > 0:
            instructions.append(f"🚨 **Zona de Risco:** {contratos_risco} contratos estão atrasados e com execução abaixo de 80%. Ação imediata recomendada.")

    # Regra 5: Setor com Maior Valor
    if all(c in df_copy.columns for c in ["Valor Contrato", SETOR_COL]):
        setor_maior_valor = df_copy.groupby(SETOR_COL)["Valor Contrato"].sum().idxmax()
        instructions.append(f"💰 **Principal Setor:** O setor '{setor_maior_valor}' concentra o maior volume de valor em contratos na seleção atual.")

    if not instructions:
        instructions.append("✅ Nenhum alerta crítico identificado. Os indicadores parecem estar dentro dos parâmetros.")

    return instructions

# --- LAYOUT DA APLICAÇÃO ---

# Título
st.title("🏗️ SGEE+PO - Painel de Análise de Contratos")

# Carregamento dos dados
df_calc = carregar_dados(FILE_ID)

if df_calc.empty:
    st.stop()

# --- SIDEBAR E FILTROS ---
with st.sidebar:
    st.header("⚙️ Filtros e Ações")
    
    if SETOR_COL in df_calc.columns:
        setores_unicos = sorted(df_calc[SETOR_COL].dropna().unique())
        setores_selecionados = st.multiselect("Filtrar por Setor", setores_unicos, default=setores_unicos)
    else:
        setores_selecionados = []

    if RESP_COL in df_calc.columns:
        responsaveis_unicos = sorted(df_calc[RESP_COL].dropna().unique())
        responsaveis_selecionados = st.multiselect("Filtrar por Responsável", responsaveis_unicos, default=responsaveis_unicos)
    else:
        responsaveis_selecionados = []

    st.markdown("---")
    
    if st.button("🔄 Recarregar Dados do Arquivo"):
        st.cache_data.clear()
        st.rerun()

# Aplicando filtros
df_filtrado = df_calc.copy()
if setores_selecionados and SETOR_COL in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado[SETOR_COL].isin(setores_selecionados)]
if responsaveis_selecionados and RESP_COL in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado[RESP_COL].isin(responsaveis_selecionados)]

# --- PAINEL PRINCIPAL ---

# Seção de Instruções
st.header("💡 Análise e Instruções")
with st.container(border=True):
    generated_instructions = generate_instructions(df_filtrado)
    for instruction in generated_instructions:
        st.markdown(instruction)

st.markdown("---")

# KPIs
st.header("📊 Indicadores Chave da Seleção")
col1, col2, col3 = st.columns(3)
col1.metric("Contratos na Seleção", len(df_filtrado))
if SETOR_COL in df_filtrado.columns:
    col2.metric("Setores na Seleção", df_filtrado[SETOR_COL].nunique())
if RESP_COL in df_filtrado.columns:
    col3.metric("Responsáveis na Seleção", df_filtrado[RESP_COL].nunique())

# KPIs Financeiros, de Prazo e Execução em colunas
st.markdown("---")
col_fin1, col_fin2, col_fin3 = st.columns(3)
col_prazo1, col_prazo2, col_exec1 = st.columns(3)

# Cálculos Financeiros
total_valor_contrato = 0
total_valor_aditivos = 0
indice_aditivo_global = 0
if not df_filtrado.empty and all(c in df_filtrado.columns for c in ["% Aditivo", "Valor Contrato", "Valor Aditivos"]):
    df_filtered_aditivos = df_filtrado[df_filtrado["% Aditivo"] <= 50]
    total_valor_contrato = df_filtered_aditivos["Valor Contrato"].sum()
    total_valor_aditivos = df_filtered_aditivos["Valor Aditivos"].sum()
    if total_valor_contrato > 0:
        indice_aditivo_global = (total_valor_aditivos / total_valor_contrato * 100)
col_fin1.metric("Somatório Valor Contrato", f"R$ {total_valor_contrato:,.2f}")
col_fin2.metric("Somatório dos Aditivos", f"R$ {total_valor_aditivos:,.2f}")
col_fin3.metric("Índice Aditivo Global", f"{indice_aditivo_global:.2f}%")

# Cálculos de Prazo e Execução
if "Dias Restantes" in df_filtrado.columns:
    contratos_atrasados = df_filtrado[df_filtrado["Dias Restantes"] < 0].shape[0]
    col_prazo1.metric("Média de Dias Restantes", f"{df_filtrado['Dias Restantes'].mean():.0f} dias")
    col_prazo2.metric("Total de Contratos Atrasados", contratos_atrasados)
if "% executado" in df_filtrado.columns:
    col_exec1.metric("Média % Executado", f"{df_filtrado['% executado'].mean():.2f}%")

st.markdown("---")

# --- SEÇÃO DE GRÁFICOS ---
st.header("📈 Visualizações Gráficas")

if df_filtrado.empty:
    st.warning("Nenhum dado para exibir nos gráficos com os filtros atuais.")
else:
    col_graph1, col_graph2 = st.columns(2)
    with col_graph1:
        if "Valor Contrato" in df_filtrado.columns and SETOR_COL in df_filtrado.columns:
            st.subheader("Valor por Setor")
            df_setor = df_filtrado.groupby(SETOR_COL)["Valor Contrato"].sum().sort_values(ascending=False)
            fig_bar = px.bar(df_setor, y="Valor Contrato", text_auto='.2s')
            fig_bar.update_layout(showlegend=False, yaxis_title="Valor Total (R$)", xaxis_title="Setor")
            st.plotly_chart(fig_bar, use_container_width=True)
    
    with col_graph2:
        if "% executado" in df_filtrado.columns and "Dias Restantes" in df_filtrado.columns:
            st.subheader("Execução vs. Prazos")
            fig_scatter = px.scatter(
                df_filtrado, x="Dias Restantes", y="% executado",
                color=SETOR_COL, hover_data=["Nº Contrato", "Objeto", "Total Contrato"]
            )
            fig_scatter.add_vline(x=0, line_dash="dash", line_color="red")
            fig_scatter.add_hline(y=80, line_dash="dash", line_color="orange")
            st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# Dados Detalhados
st.header("📋 Dados Detalhados da Seleção")
st.data_editor(df_filtrado, use_container_width=True, hide_index=True, num_rows="dynamic")

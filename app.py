
import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io


# --- FUNÇÕES DE BACK-END ---

@st.cache_resource
def conectar_google_drive():
    try:
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPES
        )
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        st.error(f"❌ Erro de conexão com o Google Drive: {e}")
        return None

@st.cache_data(ttl=3600)
def baixar_arquivo_drive(file_id: str):
    service = conectar_google_drive()
    if not service:
        return None

    try:
        request = service.files().get_media(fileId=file_id)
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

def generate_instructions(df: pd.DataFrame) -> list[str]:
    instructions = []
    df_copy = df.copy() # Trabalhar com uma cópia para evitar SettingWithCopyWarning

    # Regra 1: Índice Aditivo Global
    if 
        df_filtered_aditivos = df_copy[df_copy["% Aditivo"] <= 50]
        total_valor_contrato = df_filtered_aditivos["Valor Contrato"].sum() if "Valor Contrato" in df_filtered_aditivos.columns else 0
        total_valor_aditivos = df_filtered_aditivos["Valor Aditivos"].sum() if "Valor Aditivos" in df_filtered_aditivos.columns else 0
        indice_aditivo_global = (total_valor_aditivos / total_valor_contrato * 100) if total_valor_contrato != 0 else 0
        if indice_aditivo_global > 10:
            instructions.append(f"⚠️ **Alerta de Aditivos:** O Índice Aditivo Global ({indice_aditivo_global:.2f}%) está acima de 10%. Isso pode indicar um alto volume de aditivos. Considere rever os processos de planeamento inicial ou a gestão de mudanças nos contratos.")

    # Regra 2: Contratos Atrasados
    if "Data Fim Cnt Com Aditivos" in df_copy.columns:
        df_copy["Dias Restantes"] = (df_copy["Data Fim Cnt Com Aditivos"] - pd.to_datetime("today")).dt.days
        contratos_atrasados = df_copy[df_copy["Dias Restantes"] < 0].shape[0]
        if contratos_atrasados > 0:
            instructions.append(f"⏰ **Atrasos Identificados:** Existem {contratos_atrasados} contratos com dias restantes negativos. Priorize a revisão e o acompanhamento destes contratos para mitigar atrasos maiores e possíveis penalidades.")

    # Regra 3: Baixo % Executado
    if "Total Medido Acumulado" in df_copy.columns and "Total Contrato" in df_copy.columns:
        df_copy["% executado"] = (df_copy["Total Medido Acumulado"] / df_copy["Total Contrato"] * 100).fillna(0)
        contratos_baixo_execucao = df_copy[df_copy["% executado"] < 20].shape[0]
        if contratos_baixo_execucao > 0:
            instructions.append(f"📉 **Baixa Execução Financeira:** {contratos_baixo_execucao} contratos apresentam menos de 20% de execução financeira. Investigue as causas e acelere o progresso para evitar subutilização de recursos ou atrasos no projeto.")

    if not instructions:
        instructions.append("✅ Nenhuma instrução específica gerada com base nas regras atuais. Os indicadores parecem estar dentro dos parâmetros definidos.")

    return instructions

# --- CONFIGURAÇÕES GLOBAIS ---
FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

st.set_page_config(
    page_title="SGEE+PO - Reconstrução",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CARREGAMENTO DOS DADOS ---
st.title("🏗️ SGEE+PO - Reconstrução do Painel")
st.info("Passo 1: Carregando dados e exibindo KPIs. Ignore a aparência por enquanto.")

file_buffer = None
try:
    file_buffer = open("SGEE+PO.xlsm", "rb")
    st.info("✅ Ficheiro Excel carregado localmente.")
except FileNotFoundError:
    st.info("Ficheiro Excel local não encontrado. A tentar carregar do Google Drive...")
    file_buffer = baixar_arquivo_drive(FILE_ID)

if not file_buffer:
    st.error("❌ Não foi possível carregar o ficheiro Excel, nem localmente nem do Google Drive.")
    st.stop()

try:
    df_calc = pd.read_excel(file_buffer, sheet_name="SGEEePO", engine="openpyxl")
    # Converter colunas de data para o tipo datetime
    date_columns = ["Data Assin Cnt", "Data Inicio Cnt", "Data Fim Cnt Original", "Data Fim Cnt Com Aditivos", "Data Última Renovação"]
    for col in date_columns:
        if col in df_calc.columns:
            df_calc[col] = pd.to_datetime(df_calc[col], errors="coerce")
    
    # Converter colunas financeiras para o tipo numérico
    financial_columns = ["Total Contrato", "Valor Contrato", "Valor Aditivos", "Saldo Contratual", "Total Medido Acumulado"]
    for col in financial_columns:
        if col in df_calc.columns:
            df_calc[col] = pd.to_numeric(df_calc[col], errors="coerce").fillna(0)

    df_calc = df_calc.dropna(how="all")
    # Converter a coluna 
    if 
        df_calc["% Aditivo"] = pd.to_numeric(df_calc["% Aditivo"], errors="coerce").fillna(0)

    if df_calc.empty:
        st.error("⚠️ A planilha foi carregada, mas está vazia.")
        st.stop()
    st.success("✅ Dados carregados com sucesso!")
except Exception as e:
    st.error(f"❌ Falha ao processar a planilha: {e}")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurações")
    
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

    st.markdown("---")
    st.header("📸 Diagnóstico")
    st.caption("A funcionalidade de gerar imagem da tela foi temporariamente desativada devido a problemas técnicos. Por favor, use as ferramentas de captura de tela do seu sistema operacional.")

    st.markdown("---")
    st.header("💡 Gerador de Instruções")
    if st.button("Gerar Instruções"): 
        generated_instructions = generate_instructions(df_calc)
        for instruction in generated_instructions:
            st.info(instruction)
    st.caption("Gera instruções e insights acionáveis com base nos dados e KPIs.")

# --- KPIs ---
st.header("📊 Indicadores Chave")
col1, col2, col3 = st.columns(3)

col1.metric("Total de Registros", len(df_calc))

setor_col = "Setor Responsavel"
if setor_col in df_calc.columns:
    col2.metric("Setores Únicos", df_calc[setor_col].nunique())
else:
    col2.warning(f"Coluna \'{setor_col}\' não encontrada.")

resp_col = "Responsável"
if resp_col in df_calc.columns:
    col3.metric("Responsáveis Únicos", df_calc[resp_col].nunique())
else:
    col3.warning(f"Coluna \'{resp_col}\' não encontrada.")

st.markdown("---")

# --- CÁLCULOS DE KPIS ADICIONAIS ---

st.header("📊 KPIs Financeiros")

# Filtrar dados para cálculos de aditivos (excluir % Aditivo > 50)
df_filtered_aditivos = df_calc[df_calc["% Aditivo"] <= 50] if 

# Somatório Valor Contrato
total_valor_contrato = df_filtered_aditivos["Valor Contrato"].sum() if "Valor Contrato" in df_filtered_aditivos.columns else 0

# Somatório dos Aditivos
total_valor_aditivos = df_filtered_aditivos["Valor Aditivos"].sum() if "Valor Aditivos" in df_filtered_aditivos.columns else 0

# Índice do Aditivo Global em %
indice_aditivo_global = (total_valor_aditivos / total_valor_contrato * 100) if total_valor_contrato != 0 else 0

col4, col5, col6 = st.columns(3)
col4.metric("Somatório Valor Contrato (c/ filtro)", f"R$ {total_valor_contrato:,.2f}")
col5.metric("Somatório dos Aditivos (c/ filtro)", f"R$ {total_valor_aditivos:,.2f}")
col6.metric("Índice Aditivo Global (c/ filtro)", f"{indice_aditivo_global:,.2f}%")

st.markdown("---")

# --- DADOS DETALHADOS ---
st.header("📋 Dados Detalhados")
st.data_editor(df_calc, use_container_width=True, hide_index=True, num_rows="dynamic")

# --- CÁLCULOS DE DATAS ---

if "Data Fim Cnt Com Aditivos" in df_calc.columns:
    df_calc["Dias Restantes"] = (df_calc["Data Fim Cnt Com Aditivos"] - pd.to_datetime("today")).dt.days
    df_calc["Atrasos"] = df_calc["Dias Restantes"].apply(lambda x: x if x < 0 else 0)
    st.header("📅 Indicadores de Prazo")
    col_dr, col_at = st.columns(2)
    col_dr.metric("Média de Dias Restantes", f"{df_calc["Dias Restantes"].mean():.0f} dias")
    col_at.metric("Total de Contratos Atrasados", df_calc[df_calc["Atrasos"] < 0].shape[0])
    st.markdown("---")

# --- CÁLCULOS FINANCEIROS ADICIONAIS ---

if "Total Medido Acumulado" in df_calc.columns and "Total Contrato" in df_calc.columns:
    df_calc["% executado"] = (df_calc["Total Medido Acumulado"] / df_calc["Total Contrato"] * 100).fillna(0)
    st.header("💰 Indicadores de Execução Financeira")
    st.metric("Média % Executado", f"{df_calc["% executado"].mean():.2f}%")

if "Saldo Contratual" in df_calc.columns and "Total Contrato" in df_calc.columns:
    df_calc["% saldo"] = (df_calc["Saldo Contratual"] / df_calc["Total Contrato"] * 100).fillna(0)
    st.metric("Média % Saldo", f"{df_calc["% saldo"].mean():.2f}%")

st.markdown("---")


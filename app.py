import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from streamlit_js_eval import streamlit_js_eval

# --- CONFIGURAÇÕES GLOBAIS ---
FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

st.set_page_config(
    page_title="SGEE+PO - Reconstrução",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurações")
    # st.info(f"ID do Arquivo: `{FILE_ID[-10:]}`") # Comentado, pois estamos a usar um ficheiro local
    
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

    st.markdown("---")
    st.header("📸 Diagnóstico")
    
    if st.button("Gerar Imagem da Tela"):
        streamlit_js_eval(js_expressions='''
            // Função para capturar e baixar a tela
            function captureAndDownload() {
                const element = document.querySelector("[data-testid='stAppViewContainer']");
                if (!element) {
                    alert('Elemento do painel não encontrado.');
                    return;
                }

                html2canvas(element, {
                    scale: 1.5,
                    useCORS: true,
                    backgroundColor: '#ffffff'
                }).then(canvas => {
                    const link = document.createElement('a');
                    link.download = 'diagnostico_painel.png';
                    link.href = canvas.toDataURL('image/png');
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }).catch(err => {
                    console.error('Erro ao gerar imagem:', err);
                    alert('Falha ao gerar imagem. Verifique o console do navegador.');
                });
            }

            // Verifica se html2canvas já está disponível
            if (typeof html2canvas !== 'undefined') {
                captureAndDownload();
            } else {
                // Carrega html2canvas dinamicamente
                const script = document.createElement('script');
                script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
                script.onload = () => {
                    if (typeof html2canvas !== 'undefined') {
                        captureAndDownload();
                    } else {
                        alert('Falha ao carregar html2canvas.');
                    }
                };
                script.onerror = () => {
                    alert('Não foi possível carregar a biblioteca html2canvas.');
                };
                document.head.appendChild(script);
            }
        ''')
    st.caption("Gera uma imagem PNG da tela atual para análise.")

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
            df_calc[col] = pd.to_datetime(df_calc[col], errors='coerce')
    
    # Converter colunas financeiras para o tipo numérico
    financial_columns = ["Total Contrato", "Valor Contrato", "Valor Aditivos", "Saldo Contratual", "Total Medido Acumulado"]
    for col in financial_columns:
        if col in df_calc.columns:
            df_calc[col] = pd.to_numeric(df_calc[col], errors='coerce').fillna(0)

    df_calc = df_calc.dropna(how='all')
    # Converter a coluna '% Aditivo' para numérica, se existir
    if '% Aditivo' in df_calc.columns:
        df_calc['% Aditivo'] = pd.to_numeric(df_calc['% Aditivo'], errors='coerce').fillna(0)

    if df_calc.empty:
        st.error("⚠️ A planilha foi carregada, mas está vazia.")
        st.stop()
    st.success("✅ Dados carregados com sucesso!")
except Exception as e:
    st.error(f"❌ Falha ao processar a planilha: {e}")
    st.stop()

# --- KPIs ---
st.header("📊 Indicadores Chave")
col1, col2, col3 = st.columns(3)

col1.metric("Total de Registros", len(df_calc))

setor_col = "Setor Responsavel"
if setor_col in df_calc.columns:
    col2.metric("Setores Únicos", df_calc[setor_col].nunique())
else:
    col2.warning(f"Coluna '{setor_col}' não encontrada.")

resp_col = "Responsável"
if resp_col in df_calc.columns:
    col3.metric("Responsáveis Únicos", df_calc[resp_col].nunique())
else:
    col3.warning(f"Coluna '{resp_col}' não encontrada.")

st.markdown("---")

# --- CÁLCULOS DE KPIS ADICIONAIS ---

st.header("📊 KPIs Financeiros")

# Filtrar dados para cálculos de aditivos (excluir % Aditivo > 50)
df_filtered_aditivos = df_calc[df_calc['% Aditivo'] <= 50] if '% Aditivo' in df_calc.columns else df_calc

# Somatório Valor Contrato
total_valor_contrato = df_filtered_aditivos['Valor Contrato'].sum() if 'Valor Contrato' in df_filtered_aditivos.columns else 0

# Somatório dos Aditivos
total_valor_aditivos = df_filtered_aditivos['Valor Aditivos'].sum() if 'Valor Aditivos' in df_filtered_aditivos.columns else 0

# Índice do Aditivo Global em %
indice_aditivo_global = (total_valor_aditivos / total_valor_contrato * 100) if total_valor_contrato != 0 else 0

col4, col5, col6 = st.columns(3)
col4.metric("Somatório Valor Contrato (c/ filtro)", f"R$ {total_valor_contrato:,.2f}")
col5.metric("Somatório dos Aditivos (c/ filtro)", f"R$ {total_valor_aditivos:,.2f}")
col6.metric("Índice Aditivo Global (c/ filtro)", f"{indice_aditivo_global:,.2f}%")

st.markdown("---")

# --- DADOS DETALHADOS ---
st.header("📋 Dados Detalhados")
st.dataframe(df_calc, use_container_width=True)

# --- CÁLCULOS DE DATAS ---

if 'Data Fim Cnt Com Aditivos' in df_calc.columns:
    df_calc['Dias Restantes'] = (df_calc['Data Fim Cnt Com Aditivos'] - pd.to_datetime('today')).dt.days
    df_calc['Atrasos'] = df_calc['Dias Restantes'].apply(lambda x: x if x < 0 else 0)
    st.header("📅 Indicadores de Prazo")
    col_dr, col_at = st.columns(2)
    col_dr.metric("Média de Dias Restantes", f"{df_calc['Dias Restantes'].mean():.0f} dias")
    col_at.metric("Total de Contratos Atrasados", df_calc[df_calc['Atrasos'] < 0].shape[0])
    st.markdown("---")

# --- CÁLCULOS FINANCEIROS ADICIONAIS ---

if 'Total Medido Acumulado' in df_calc.columns and 'Total Contrato' in df_calc.columns:
    df_calc['% executado'] = (df_calc['Total Medido Acumulado'] / df_calc['Total Contrato'] * 100).fillna(0)
    st.header("💰 Indicadores de Execução Financeira")
    st.metric("Média % Executado", f"{df_calc['% executado'].mean():.2f}%")

if 'Saldo Contratual' in df_calc.columns and 'Total Contrato' in df_calc.columns:
    df_calc['% saldo'] = (df_calc['Saldo Contratual'] / df_calc['Total Contrato'] * 100).fillna(0)
    st.metric("Média % Saldo", f"{df_calc['% saldo'].mean():.2f}%")

st.markdown("---")

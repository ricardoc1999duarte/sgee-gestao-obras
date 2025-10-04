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
    st.info(f"ID do Arquivo: `{FILE_ID[-10:]}`")
    
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

    st.markdown("---")
    st.header("📸 Diagnóstico")
    
    if st.button("Gerar Imagem da Tela"):
        streamlit_js_eval(js_expressions="""
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
        """)
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

file_buffer = baixar_arquivo_drive(FILE_ID)
if not file_buffer:
    st.stop()

try:
    df_calc = pd.read_excel(file_buffer, sheet_name="SGEEePO", engine="openpyxl")
    df_calc = df_calc.dropna(how='all')
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

# --- DADOS DETALHADOS ---
st.header("📋 Dados Detalhados")
st.dataframe(df_calc, use_container_width=True)

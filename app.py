import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from streamlit_js_eval import streamlit_js_eval # Importado de volta

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="SGEE+PO - Diagnóstico",
    layout="wide"
 )

# --- BOTÃO DE CAPTURA NA SIDEBAR ---
with st.sidebar:
    st.header("Diagnóstico")
    if st.button("📸 Gerar Imagem da Tela"):
        streamlit_js_eval(js_expressions="""
            const html2canvasScript = document.createElement('script');
            html2canvasScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
            document.head.appendChild(html2canvasScript );

            html2canvasScript.onload = () => {
                const element = window.parent.document.querySelector('[data-testid="stAppViewContainer"]');
                html2canvas(element, { scale: 1.5, useCORS: true }).then(canvas => {
                    const image = canvas.toDataURL('image/png');
                    const a = document.createElement('a');
                    a.href = image;
                    a.download = 'diagnostico_painel.png';
                    a.click();
                });
            };
        """)
    st.caption("Gera uma imagem (PNG) de toda a tela para análise.")


# --- CORPO PRINCIPAL DO DIAGNÓSTICO ---
st.title("🚧 SGEE+PO - Módulo de Diagnóstico de Dados 🚧")
st.warning("Estamos em modo de segurança. O objetivo é apenas carregar e exibir os dados brutos para identificar o problema.")

# --- CARREGAMENTO E EXIBIÇÃO ---
FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
st.info(f"Tentando carregar dados do arquivo ID: ...{FILE_ID[-10:]}")

# Funções de conexão e download (colocadas aqui para simplificar o escopo)
@st.cache_resource
def conectar_google_drive():
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=['https://www.googleapis.com/auth/drive.readonly']
         )
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        st.error(f"Erro de conexão com o Google Drive: {e}")
        return None

@st.cache_data(ttl=3600)
def baixar_arquivo_drive(_service, file_id):
    try:
        request = _service.files().get_media(fileId=file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        done = False
        while not done: status, done = downloader.next_chunk()
        file_stream.seek(0)
        return file_stream
    except Exception as e:
        st.error(f"Erro ao baixar arquivo do Drive: {e}")
        return None

try:
    # PASSO 1: Conectar
    service = conectar_google_drive()
    if service is None:
        st.stop()
    st.success("✅ PASSO 1/4: Conexão com Google Drive bem-sucedida.")

    # PASSO 2: Baixar
    file_stream = baixar_arquivo_drive(service, FILE_ID)
    if file_stream is None:
        st.stop()
    st.success("✅ PASSO 2/4: Download do arquivo do Drive bem-sucedido.")

    # PASSO 3: Ler o Excel para um DataFrame
    df_bruto = pd.read_excel(file_stream, sheet_name='SGEEePO', engine='openpyxl')
    if df_bruto.empty:
        st.error("O arquivo Excel foi lido, mas está vazio.")
        st.stop()
    st.success("✅ PASSO 3/4: Leitura do arquivo Excel bem-sucedida.")
    
    # PASSO CRÍTICO: Imprimir os nomes das colunas exatamente como o Pandas os leu
    st.markdown("### Colunas Originais Encontradas no Arquivo:")
    st.code(list(df_bruto.columns))

    # PASSO 4: Exibir DataFrame Bruto
    st.success("✅ PASSO 4/4: Exibindo os dados brutos abaixo.")
    st.markdown("---")
    st.header("Tabela de Dados Brutos")
    st.dataframe(df_bruto)

except Exception as e:
    st.error(f"❌ FALHA CRÍTICA DURANTE A EXECUÇÃO:")
    st.exception(e) # Isso vai imprimir o erro completo na tela para nós.


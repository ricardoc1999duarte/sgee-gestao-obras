import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="SGEE+PO - Diagnóstico",
    layout="wide"
 )

st.title("🚧 SGEE+PO - Módulo de Diagnóstico de Dados 🚧")
st.warning("Estamos em modo de segurança. O objetivo é apenas carregar e exibir os dados brutos.")

# --- 2. FUNÇÕES DE BACK-END (sem alterações) ---
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

# --- 3. CARREGAMENTO E EXIBIÇÃO ---
FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
st.info(f"Tentando carregar dados do arquivo ID: ...{FILE_ID[-10:]}")

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
    
    st.markdown("### Colunas Originais Encontradas no Arquivo:")
    st.write(list(df_bruto.columns))

    # PASSO 4: Exibir DataFrame Bruto
    st.success("✅ PASSO 4/4: Exibindo os dados brutos abaixo.")
    st.markdown("---")
    st.header("Tabela de Dados Brutos")
    st.dataframe(df_bruto)

except Exception as e:
    st.error(f"❌ FALHA CRÍTICA DURANTE A EXECUÇÃO:")
    st.exception(e) # Isso vai imprimir o erro completo na tela para nós.


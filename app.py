import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from streamlit_js_eval import streamlit_js_eval

# --- 1. CONFIGURAÇÕES GLOBAIS ---
FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

st.set_page_config(
    page_title="SGEE+PO - Painel de Gestão de Obras",
    layout="wide",
    initial_sidebar_state="expanded"
 )

# --- 2. SIDEBAR ---
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
        streamlit_js_eval(js_expressions=\'\'\'
            const script = document.createElement(\'script\');
            script.src = \'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js\';
            document.head.appendChild(script );
            script.onload = () => {
                const container = window.parent.document.querySelector(\'[data-testid="stAppViewContainer"]\');
                if (!container) {
                    alert(\'Elemento do painel não encontrado.\');
                    return;
                }
                html2canvas(container, { scale: 1.5, useCORS: true }).then(canvas => {
                    const link = document.createElement(\'a\');
                    link.download = \'diagnostico_painel.png\';
                    link.href = canvas.toDataURL(\'image/png\');
                    link.click();
                });
            };
        \'\'\')
    st.caption("Captura uma imagem PNG da tela atual para análise.")

# --- 3. FUNÇÕES DE BACK-END ---
@st.cache_resource
def conectar_google_drive():
    """Conecta ao Google Drive usando credenciais de conta de serviço."""
    try:
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPES
        )
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        st.error(f"❌ Falha ao conectar ao Google Drive: {e}")
        return None

@st.cache_data(ttl=3600)
def baixar_arquivo_drive(file_id: str):
    """Baixa um arquivo do Google Drive e retorna um buffer em memória."""
    service = conectar_google_drive()
    if not service: return None
    try:
        request = service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done: _, done = downloader.next_chunk()
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"❌ Erro ao baixar arquivo do Drive: {e}"); return None

# --- 4. CARREGAMENTO E FILTROS ---
st.title("🏗️ SGEE+PO - Painel de Gestão de Obras")

file_buffer = baixar_arquivo_drive(FILE_ID)
if not file_buffer:
    st.stop()

try:
    df_original = pd.read_excel(file_buffer, sheet_name="SGEEePO", engine="openpyxl")
    df_original = df_original.dropna(how=\'all\')
    if df_original.empty:
        st.error("⚠️ A planilha foi carregada, mas está vazia."); st.stop()
except Exception as e:
    st.error(f"❌ Falha ao processar a planilha: {e}"); st.stop()

# Filtros na sidebar
st.sidebar.markdown("---")
st.sidebar.header("🔍 Filtros Dinâmicos")

setor_col = "Setor Responsavel"
resp_col = "Responsável"

setores = ["Todos"] + sorted(df_original[setor_col].dropna().unique().tolist())
responsaveis = ["Todos"] + sorted(df_original[resp_col].dropna().unique().tolist())

setor_selecionado = st.sidebar.selectbox("Setor", setores)
responsavel_selecionado = st.sidebar.selectbox("Responsável", responsaveis)

df_filtrado = df_original.copy()
if setor_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado[setor_col] == setor_selecionado]
if responsavel_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado[resp_col] == responsavel_selecionado]

# --- 5. EXIBIÇÃO DE KPIs ---
st.header("📊 Indicadores Chave")
col1, col2, col3 = st.columns(3)
col1.metric("Total de Registros", len(df_filtrado))
col2.metric("Setores Únicos", df_filtrado[setor_col].nunique())
col3.metric("Responsáveis Únicos", df_filtrado[resp_col].nunique())

st.markdown("---")

# --- 6. ANÁLISES GRÁFICAS ---
st.header("📈 Análises Gráficas")
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("Contratos por Setor")
    if not df_filtrado[setor_col].dropna().empty:
        setor_counts = df_filtrado[setor_col].value_counts()
        fig_setor = px.pie(values=setor_counts.values, names=setor_counts.index, hole=0.4)
        fig_setor.update_layout(template="plotly_white", showlegend=True)
        st.plotly_chart(fig_setor, use_container_width=True)
    else:
        st.warning("Nenhum dado de setor para exibir.")

with col_g2:
    st.subheader("Top 10 Responsáveis")
    if not df_filtrado[resp_col].dropna().empty:
        resp_counts = df_filtrado[resp_col].value_counts().nlargest(10)
        fig_resp = px.bar(y=resp_counts.index, x=resp_counts.values, orientation=\'h\', labels={\'y\': \'\', \'x\': \'Nº de Contratos\'}) # Corrigido aqui
        fig_resp.update_layout(template="plotly_white", yaxis={\'categoryorder\':\'total ascending\'}) # Corrigido aqui
        st.plotly_chart(fig_resp, use_container_width=True)
    else:
        st.warning("Nenhum dado de responsável para exibir.")

st.markdown("---")

# --- 7. EXIBIÇÃO DA TABELA ---
st.header("📋 Dados Detalhados")
st.dataframe(df_filtrado, use_container_width=True)

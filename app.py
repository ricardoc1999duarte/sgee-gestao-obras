import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from streamlit_js_eval import streamlit_js_eval # Importado para o botão de captura

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="SGEE+PO - Reconstrução",
    layout="wide"
 )

# --- 2. SIDEBAR COM O ESSENCIAL ---
with st.sidebar:
    st.header("Configurações")
    FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
    st.info(f"ID do Arquivo: ...{FILE_ID[-10:]}")
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear(); st.cache_resource.clear(); st.rerun()

    st.markdown("--- ")
    st.header("Diagnóstico")
    
    # BOTÃO DE CAPTURA DE TELA (RESTAURADO E FUNCIONAL)
    if st.button("📸 Gerar Imagem da Tela"):
        streamlit_js_eval(js_expressions="""
            const html2canvasScript = document.createElement("script");
            html2canvasScript.src = "https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js";
            document.head.appendChild(html2canvasScript );

            html2canvasScript.onload = () => {
                const element = window.parent.document.querySelector("[data-testid=\"stAppViewContainer\"]");
                html2canvas(element, { scale: 1.5, useCORS: true }).then(canvas => {
                    const image = canvas.toDataURL("image/png");
                    const a = document.createElement("a");
                    a.href = image;
                    a.download = "diagnostico_painel.png";
                    a.click();
                });
            };
        """)
    st.caption("Gera uma imagem (PNG) de toda a tela para análise.")

# --- 3. FUNÇÕES DE BACK-END ---
@st.cache_resource
def conectar_google_drive():
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/drive.readonly"]
         )
        return build("drive", "v3", credentials=credentials)
    except Exception as e:
        st.error(f"Erro de conexão com o Google Drive: {e}"); return None

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
        st.error(f"Erro ao baixar arquivo do Drive: {e}"); return None

# --- 4. CORPO PRINCIPAL ---
st.title("🏗️ SGEE+PO - Reconstrução do Painel")
st.info("Passo 1: Carregando dados e exibindo KPIs. Ignore a aparência por enquanto.")

try:
    service = conectar_google_drive()
    file_stream = baixar_arquivo_drive(service, "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg")
    # Lendo o Excel sem renomear nada
    df_calc = pd.read_excel(file_stream, sheet_name="SGEEePO", engine="openpyxl")
    df_calc = df_calc.dropna(how=\'all\')

    if df_calc is None or df_calc.empty:
        st.error("Os dados não puderam ser carregados ou processados.")
        st.stop()
    st.success("✅ Dados carregados com sucesso!")
except Exception as e:
    st.error(f"Falha crítica na inicialização do painel. Erro: {e}")
    st.stop()

# --- SEÇÃO DE KPIs (O ÚNICO ELEMENTO ADICIONADO) ---
st.header("Indicadores Chave")
kpi1, kpi2, kpi3 = st.columns(3)

kpi1.metric("Total de Registros", len(df_calc))

# Verificação de segurança para o KPI de Setor
# Usando o nome exato da coluna que vimos no diagnóstico
if "Setor Responsavel" in df_calc.columns:
    kpi2.metric("Setores Únicos", df_calc["Setor Responsavel"].nunique())
else:
    kpi2.metric("Setores Únicos", "Coluna \'Setor Responsavel\' não encontrada")

# Verificação de segurança para o KPI de Responsável
# Usando o nome exato da coluna que vimos no diagnóstico
if "Responsável" in df_calc.columns:
    kpi3.metric("Responsáveis Únicos", df_calc["Responsável"].nunique())
else:
    kpi3.metric("Responsáveis Únicos", "Coluna \'Responsável\' não encontrada")

st.markdown("---")

# --- SEÇÃO DE DADOS DETALHADOS ---
st.header("Dados Detalhados")
st.dataframe(df_calc)

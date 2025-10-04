import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_js_eval import streamlit_js_eval
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA E ESTILO ---
st.set_page_config(
    page_title="SGEE+PO - Gestão de Obras",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
 )

# FORÇAR TEMA CLARO DO STREAMLIT E ESTILOS GERAIS
st.markdown(
    """
    <style>
    /* Força o tema claro do Streamlit */
    .st-emotion-cache-vk3288 { /* Seletor para o tema principal do Streamlit */
        background-color: #F0F2F6; /* Fundo claro */
        color: #1E293B; /* Texto escuro */
    }
    /* Garante que o texto em geral seja escuro */
    body, h1, h2, h3, h4, h5, h6, p, .stMarkdown, label, [data-testid="stMetricLabel"] {
        color: #1E293B !important;
    }

    /* Outros estilos permanecem os mesmos */
    @media print { .noprint { display: none !important; } }
    [data-testid="stAppViewContainer"] { background-color: #F0F2F6; }
    h1, h3 { color: #0B3D91; }
    h3 { border-bottom: 2px solid #DDE6F6; padding-bottom: 8px; margin-top: 24px; }
    [data-testid="stMetric"] {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
        padding: 25px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    </style>
    """,
    unsafe_allow_html=True
)


# --- 2. FUNÇÕES DE BACK-END ---
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

@st.cache_data(ttl=3600)
def processar_dados_excel(file_stream):
    try:
        df = pd.read_excel(file_stream, sheet_name="SGEEePO", engine="openpyxl")
        df = df.dropna(how="all")
        
        # MAPEAMENTO PRECISO DAS COLUNAS (BASEADO NA SUA IMAGEM DE DIAGNÓSTICO)
        rename_map = {
            "Num CNT": "Num_CNT",
            "Objeto Cnt": "Objeto_Cnt",
            "Cod Empreendimento": "Cod_Empreendimento",
            "Nome Empreendimento": "Nome_Empreendimento",
            "Statusprj(Ajustada)": "Status_Obra",
            "Statusprj": "Status_Projeto",
            "Status Contrato Ajustado": "Status_Contrato",
            "Dias após vencimento": "Dias_Apos_Vencimento",
            "Setor Responsavel": "Setor", # Assumindo que esta coluna existe
            "Responsável": "Responsavel" # Assumindo que esta coluna existe
            # Adicione outras colunas que você precisa aqui
        }
        
        # Renomeia apenas as colunas que existem no DataFrame
        df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)
        
        return df
    except Exception as e:
        st.error(f"Erro ao processar o arquivo Excel: {e}"); return None

# --- 3. SIDEBAR ---
with st.sidebar:
    st.image("https://i.imgur.com/t2yw4UH.png", width=80 )
    st.header("Configurações")
    FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
    st.info(f"ID do Arquivo: ...{FILE_ID[-10:]}")
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear(); st.cache_resource.clear(); st.rerun()

    st.markdown("--- ")
    st.header("Diagnóstico")
    
    # BOTÃO DE CAPTURA DE TELA (RESTAURADO E FUNCIONAL)
    if st.button("📸 Gerar Imagem do Painel"):
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
                    a.download = "captura_painel.png";
                    a.click();
                });
            };
        """)
    st.caption("Gera uma imagem (PNG) de todo o painel para análise e diagnóstico.")

# --- 4. CORPO PRINCIPAL DO APLICATIVO ---
st.title("🏗️ SGEE+PO - Painel de Gestão de Obras")

try:
    service = conectar_google_drive()
    file_stream = baixar_arquivo_drive(service, FILE_ID)
    df_calc = processar_dados_excel(file_stream)
    if df_calc is None or df_calc.empty:
        st.error("Os dados não puderam ser carregados ou processados.")
        st.stop()
    st.success("✅ Dados carregados e painel reconstruído com sucesso!")
except Exception as e:
    st.error(f"Falha crítica na inicialização do painel. Erro: {e}")
    st.stop()

# --- SEÇÃO DE KPIs ---
st.header("Indicadores Chave")
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total de Registros", len(df_calc))
if "Setor" in df_calc.columns:
    kpi2.metric("Setores Únicos", df_calc["Setor"].nunique())
else:
    kpi2.metric("Setores Únicos", "N/A - Coluna não encontrada")
if "Responsavel" in df_calc.columns:
    kpi3.metric("Responsáveis Únicos", df_calc["Responsavel"].nunique())
else:
    kpi3.metric("Responsáveis Únicos", "N/A - Coluna não encontrada")

st.markdown("--- ")

# --- SEÇÃO DE GRÁFICOS ---
st.header("Análises Gráficas")
col_g1, col_g2 = st.columns(2)

with col_g1:
    with st.container(border=True):
        st.subheader("Contratos por Setor")
        if "Setor" in df_calc.columns and not df_calc["Setor"].dropna().empty:
            setor_counts = df_calc["Setor"].value_counts()
            fig_setor = px.pie(values=setor_counts.values, names=setor_counts.index, hole=0.4)
            fig_setor.update_layout(
                template="plotly_white", 
                paper_bgcolor="rgba(255,255,255,1)", 
                plot_bgcolor="rgba(255,255,255,1)",
                showlegend=True
            )
            st.plotly_chart(fig_setor, use_container_width=True)
        else:
            st.warning("Coluna \"Setor\" não encontrada ou vazia.")

with col_g2:
    with st.container(border=True):
        st.subheader("Top 10 Responsáveis")
        if "Responsavel" in df_calc.columns and not df_calc["Responsavel"].dropna().empty:
            resp_counts = df_calc["Responsavel"].value_counts().nlargest(10)
            fig_resp = px.bar(y=resp_counts.index, x=resp_counts.values, orientation="h", labels={"y": "", "x": "Nº de Contratos"})
            fig_resp.update_layout(
                template="plotly_white", 
                paper_bgcolor="rgba(255,255,255,1)", 
                plot_bgcolor="rgba(255,255,255,1)",
                yaxis={"categoryorder":"total ascending"}
            )
            st.plotly_chart(fig_resp, use_container_width=True)
        else:
            st.warning("Coluna \"Responsavel\" não encontrada ou vazia.")

st.markdown("--- ")

# --- SEÇÃO DE DADOS DETALHADOS ---
st.header("Dados Detalhados")
st.dataframe(df_calc)

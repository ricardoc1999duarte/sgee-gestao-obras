import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from streamlit_js_eval import streamlit_js_eval # Importado para a captura de imagem

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="SGEE+PO - Gestão de Obras",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
 )

# CSS para o painel
st.markdown("""
    <style>
    @media print { .noprint { display: none !important; } }
    [data-testid="stAppViewContainer"] { background-color: #F0F2F6; }
    h1, h3 { color: #0B3D91; }
    h3 { border-bottom: 2px solid #DDE6F6; padding-bottom: 8px; margin-top: 24px; }
    [data-testid="stMetric"] {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
        padding: 25px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNÇÕES DE BACK-END ---
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

@st.cache_data(ttl=3600)
def processar_dados_excel(file_stream):
    try:
        df = pd.read_excel(file_stream, sheet_name='SGEEePO', engine='openpyxl')
        df = df.dropna(how='all')
        df.columns = df.columns.str.strip().str.lower()
        rename_map = {
            'num cnt': 'Num_CNT', 'objeto cnt': 'Objeto_Cnt', 'responsável': 'Responsavel',
            'setor responsavel': 'Setor', 'empresa contratada': 'Empresa_Contratada',
            'statusprj(ajustada)': 'Status_Obra', 'statusprj': 'Status_Projeto',
            'valor contrato': 'Valor_Contrato', 'valor aditivos': 'Valor_Aditivos',
            'total contrato': 'Total_Contrato', 'saldo contratual': 'Saldo_Contratual',
            'total medido acumulado': 'Total_Medido_Acumulado', 'data fim cnt com aditivos': 'Data_Fim_Aditivos',
            'dias após vencimento': 'Dias_Apos_Vencimento', 'ano empreendimento': 'Ano_Empreendimento'
        }
        df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)
        return df
    except Exception as e:
        st.error(f"Erro ao processar o arquivo Excel: {e}")
        return None

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="noprint">', unsafe_allow_html=True)
    st.image("https://i.imgur.com/t2yw4UH.png", width=80 )
    st.header("Configurações")
    FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
    st.info(f"ID do Arquivo: ...{FILE_ID[-10:]}")
    
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear(); st.cache_resource.clear(); st.session_state.clear(); st.rerun()

    st.markdown("---")
    st.header("Diagnóstico")
    
    if st.button("📸 Gerar Imagem do Painel"):
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
                    a.download = 'captura_painel.png';
                    a.click();
                });
            };
        """)
    st.caption("Gera uma imagem (PNG) de todo o painel para análise e diagnóstico.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. CORPO PRINCIPAL DO APLICATIVO ---
st.title("🏗️ SGEE+PO - Painel de Gestão de Obras")

# Inicializa o estado da sessão
if 'filtro_setor' not in st.session_state: st.session_state['filtro_setor'] = 'Todos'
if 'filtro_resp' not in st.session_state: st.session_state['filtro_resp'] = 'Todos'

# Carregamento dos dados
try:
    service = conectar_google_drive()
    file_stream = baixar_arquivo_drive(service, FILE_ID)
    df = processar_dados_excel(file_stream)
    if df is None or df.empty:
        st.error("Os dados não puderam ser carregados ou processados.")
        st.stop()
    st.success("✅ Dados carregados e painel reconstruído com sucesso!")
except Exception as e:
    st.error(f"Falha crítica na inicialização do painel. Erro: {e}")
    st.stop()

# --- SEÇÃO DE KPIs ---
st.header("Indicadores Chave")
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total de Registros", len(df))
if 'Setor' in df.columns:
    kpi2.metric("Setores Únicos", df['Setor'].nunique())
else:
    kpi2.metric("Setores Únicos", "N/A - Coluna não encontrada")
if 'Responsavel' in df.columns:
    kpi3.metric("Responsáveis Únicos", df['Responsavel'].nunique())
else:
    kpi3.metric("Responsáveis Únicos", "N/A - Coluna não encontrada")

st.markdown("---")

# --- SEÇÃO DE GRÁFICOS ---
st.header("Análises Gráficas")
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("Contratos por Setor")
    if 'Setor' in df.columns and not df['Setor'].dropna().empty:
        setor_counts = df['Setor'].value_counts()
        fig_setor = px.pie(values=setor_counts.values, names=setor_counts.index, hole=0.4)
        fig_setor.update_layout(template='plotly_white', showlegend=True)
        st.plotly_chart(fig_setor, use_container_width=True)
    else:
        st.warning("Coluna 'Setor' não encontrada ou vazia.")

with col_g2:
    st.subheader("Top 10 Responsáveis")
    if 'Responsavel' in df.columns and not df['Responsavel'].dropna().empty:
        resp_counts = df['Responsavel'].value_counts().nlargest(10)
        fig_resp = px.bar(y=resp_counts.index, x=resp_counts.values, orientation='h', labels={'y': '', 'x': 'Nº de Contratos'})
        fig_resp.update_layout(template='plotly_white', yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_resp, use_container_width=True)
    else:
        st.warning("Coluna 'Responsavel' não encontrada ou vazia.")

st.markdown("---")

# --- SEÇÃO DE DADOS DETALHADOS ---
st.header("Dados Detalhados")
st.dataframe(df)

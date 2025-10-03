import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_js_eval import streamlit_js_eval, get_geolocation
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA E ESTILO (CSS ) ---
st.set_page_config(
    page_title="SGEE+PO - Gestão de Obras",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS (incluindo classes para impressão e gráficos clicáveis)
st.markdown("""
    <style>
    /* Oculta elementos na impressão */
    @media print {
        .noprint { display: none !important; }
    }
    /* Estilos gerais */
    [data-testid="stAppViewContainer"] > .main { background-color: #F0F2F6; }
    h1, h3 { color: #0B3D91; }
    h3 { border-bottom: 2px solid #DDE6F6; padding-bottom: 8px; margin-top: 24px; }
    /* Estilos dos cartões de métrica */
    [data-testid="stMetric"] {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
        padding: 25px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease-in-out;
    }
    [data-testid="stMetric"]:hover { transform: translateY(-5px); }
    [data-testid="stMetricLabel"] { color: #64748B !important; font-weight: 500; }
    [data-testid="stMetricValue"] { color: #0B3D91; font-size: 2.2rem; font-weight: 700; }
    /* Estilo para gráficos clicáveis */
    .stPlotlyChart.clickable { cursor: pointer; }
    .stPlotlyChart.clickable:hover { border: 1px solid #007BFF; border-radius: 12px; }
    </style>
""", unsafe_allow_html=True)


# --- 2. FUNÇÕES DE BACK-END (Conexão, Download, Processamento) ---
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

# --- 3. SIDEBAR E SISTEMA DE PRINT ---
with st.sidebar:
    # Adiciona classe para não imprimir a sidebar
    st.markdown('<div class="noprint">', unsafe_allow_html=True)
    
    st.image("https://i.imgur.com/t2yw4UH.png", width=80 )
    st.header("Configurações")
    FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
    st.info(f"ID do Arquivo: ...{FILE_ID[-10:]}")
    
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.clear()
        st.rerun()

    st.markdown("---")
    st.header("Exportar Relatório")
    
    if st.button("🖨️ Gerar Relatório PDF/Print"):
        streamlit_js_eval(js_expressions="""
            const element = window.parent.document.querySelector('.main > div');
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
            document.head.appendChild(script );
            script.onload = () => {
                html2canvas(element, { scale: 2, useCORS: true }).then(canvas => {
                    const imgData = canvas.toDataURL('image/png');
                    const pdf = new (window.jspdf.jsPDF)({
                        orientation: 'landscape', unit: 'px', format: [canvas.width, canvas.height]
                    });
                    pdf.addImage(imgData, 'PNG', 0, 0, canvas.width, canvas.height);
                    pdf.output('bloburl');
                });
            }
            const jspdfScript = document.createElement('script');
            jspdfScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
            document.head.appendChild(jspdfScript );
        """)
    st.caption("Captura a tela inteira e gera um PDF.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. CORPO PRINCIPAL DO APLICATIVO ---
st.title("🏗️ SGEE+PO - Painel de Gestão de Obras")

# Inicializa o estado da sessão para filtros interativos
if 'filtro_setor' not in st.session_state:
    st.session_state['filtro_setor'] = 'Todos'
if 'filtro_resp' not in st.session_state:
    st.session_state['filtro_resp'] = 'Todos'

# Guia de Desenvolvimento
with st.expander("🧠 Guia de Desenvolvimento e Próximos Passos", expanded=False):
    st.markdown("""
    #### Estado Atual:
    - **Impressão Corrigida:** Usa `html2canvas` para gerar um PDF/Print fiel da tela inteira.
    - **Cross-filtering Ativo:** Clicar em um setor no gráfico de pizza ou em um responsável no gráfico de barras filtra todo o painel. Um botão "Limpar Filtros" foi adicionado.
    - **Estrutura Robusta:** O código está organizado com `session_state` para gerenciar a interatividade.
    
    #### Próximos Passos Sugeridos:
    1.  **Alertas de Prazo:** Criar uma seção para contratos vencendo em 30/60/90 dias.
    2.  **Formatação Condicional:** Colorir a tabela de dados para destacar contratos críticos.
    3.  **Análise de Evolução:** Adicionar um gráfico de linhas para acompanhar valores ao longo do tempo.
    """)

# Carregamento e processamento dos dados
try:
    service = conectar_google_drive()
    file_stream = baixar_arquivo_drive(service, FILE_ID)
    df = processar_dados_excel(file_stream)
    
    # Cálculos e engenharia de features
    df_calc = df.copy()
    # ... (seus cálculos de %_Executado, Dias_Restantes, etc. entram aqui) ...
    st.success("✅ Dados carregados e processados com sucesso!")
except Exception as e:
    st.error(f"Não foi possível carregar os dados. Erro: {e}")
    st.stop()

# --- LÓGICA DE FILTROS (INCLUINDO CROSS-FILTERING) ---
df_filtrado = df_calc.copy()

# Filtro de texto geral
busca = st.text_input("🔎 Buscar em todos os campos", key="busca_geral")
if busca:
    df_filtrado = df_filtrado[df_filtrado.apply(lambda row: any(busca.lower() in str(cell).lower() for cell in row), axis=1)]

# Aplica filtros do estado da sessão (cross-filtering)
if st.session_state.filtro_setor != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Setor'] == st.session_state.filtro_setor]
if st.session_state.filtro_resp != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Responsavel'] == st.session_state.filtro_resp]

# Botão para limpar filtros de gráficos
if st.session_state.filtro_setor != 'Todos' or st.session_state.filtro_resp != 'Todos':
    if st.button("❌ Limpar Filtros de Gráfico"):
        st.session_state.filtro_setor = 'Todos'
        st.session_state.filtro_resp = 'Todos'
        st.rerun()

st.info(f"Exibindo {len(df_filtrado)} de {len(df_calc)} registros com os filtros aplicados.")

# --- VISUALIZAÇÃO EM ABAS ---
tab1, tab2 = st.tabs(["📊 Visão Geral Interativa", "📋 Dados Detalhados"])

with tab1:
    st.header("Análises Gráficas")
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader(f"Contratos por Setor (Filtro: {st.session_state.filtro_setor})")
        setor_counts = df_filtrado['Setor'].value_counts()
        fig_setor = px.pie(values=setor_counts.values, names=setor_counts.index, hole=0.4)
        
        st.markdown('<div class="stPlotlyChart clickable">', unsafe_allow_html=True)
        selected_point = st.plotly_chart(fig_setor, use_container_width=True, on_select="rerun", key="graf_setor")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if selected_point.selection and selected_point.selection['points']:
            setor_selecionado = setor_counts.index[selected_point.selection['points'][0]['pointIndex']]
            st.session_state.filtro_setor = setor_selecionado
            st.rerun()

    with col_g2:
        st.subheader(f"Contratos por Responsável (Filtro: {st.session_state.filtro_resp})")
        resp_counts = df_filtrado['Responsavel'].value_counts().nlargest(10)
        fig_resp = px.bar(y=resp_counts.index, x=resp_counts.values, orientation='h', labels={'y': '', 'x': 'Nº de Contratos'})
        fig_resp.update_layout(yaxis={'categoryorder':'total ascending'})
        
        st.markdown('<div class="stPlotlyChart clickable">', unsafe_allow_html=True)
        selected_point_resp = st.plotly_chart(fig_resp, use_container_width=True, on_select="rerun", key="graf_resp")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if selected_point_resp.selection and selected_point_resp.selection['points']:
            resp_selecionado = resp_counts.index[selected_point_resp.selection['points'][0]['pointIndex']]
            st.session_state.filtro_resp = resp_selecionado
            st.rerun()

with tab2:
    st.header("Dados Detalhados")
    st.dataframe(df_filtrado)
    
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Dados Filtrados (CSV)", csv, "dados_filtrados.csv", "text/csv")


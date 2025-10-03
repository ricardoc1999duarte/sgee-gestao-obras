import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA E ESTILO (CSS ) ---

# Configuração inicial da página (deve ser o primeiro comando do Streamlit)
st.set_page_config(
    page_title="SGEE+PO - Gestão de Obras",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Customizado (VERSÃO PROFISSIONAL E MELHORADA)
st.markdown("""
    <style>
    /* --- GERAL E FUNDO --- */
    [data-testid="stAppViewContainer"] > .main {
        background-color: #F0F2F6; /* Fundo cinza claro e profissional */
    }

    /* --- TIPOGRAFIA --- */
    h1, h2, h3, h4, h5, h6, p, label, [data-testid="stMarkdownContainer"] {
        color: #1E293B; /* Azul-escuro/chumbo para textos */
    }
    h1 {
        color: #0B3D91; font-weight: 600;
    }
    h3 {
        color: #0B3D91;
        border-bottom: 2px solid #DDE6F6;
        padding-bottom: 8px;
        margin-top: 24px;
    }

    /* --- CARTÕES DE MÉTRICA (KPIs) --- */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
    }
    [data-testid="stMetricLabel"] {
        color: #64748B !important; font-weight: 500;
    }
    [data-testid="stMetricValue"] {
        color: #0B3D91; font-size: 2.2rem; font-weight: 700;
    }

    /* --- GRÁFICOS E TABELAS --- */
    .stPlotlyChart {
        border-radius: 12px; padding: 10px; background-color: #FFFFFF;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    [data-testid="stDataFrame"] {
        border-radius: 12px; overflow: hidden;
    }

    /* --- BOTÕES E ALERTAS --- */
    .stDownloadButton > button {
        background-color: #007BFF; color: white; border-radius: 8px; border: none;
        padding: 10px 20px; transition: background-color 0.2s;
    }
    .stDownloadButton > button:hover { background-color: #0056b3; }
    [data-testid="stSuccess"] {
        border-left: 5px solid #28A745; background-color: #F0FFF4; border-radius: 8px;
    }
    [data-testid="stInfo"] {
        border-left: 5px solid #17A2B8; background-color: #E9F7F9; border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)


# --- 2. FUNÇÕES DE BACK-END (CONEXÃO E PROCESSAMENTO) ---

@st.cache_resource
def conectar_google_drive():
    """Conecta ao Google Drive usando as credenciais do service account."""
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=['https://www.googleapis.com/auth/drive.readonly']
         )
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        st.error(f"Erro ao conectar ao Google Drive: {e}")
        st.info("Verifique se as credenciais 'gcp_service_account' estão configuradas nos Secrets do Streamlit.")
        return None

@st.cache_data(ttl=3600)
def baixar_arquivo_drive(_service, file_id):
    """Baixa o arquivo do Google Drive e retorna um stream de bytes."""
    try:
        request = _service.files().get_media(fileId=file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        file_stream.seek(0)
        return file_stream
    except Exception as e:
        st.error(f"Erro ao baixar arquivo do Drive (ID: {file_id}): {e}")
        return None

@st.cache_data(ttl=3600)
def processar_dados_excel(file_stream):
    """Lê o arquivo Excel, limpa e padroniza os dados, retornando um DataFrame."""
    try:
        df = pd.read_excel(file_stream, sheet_name='SGEEePO', engine='openpyxl')
        df = df.dropna(how='all')
        
        # Padroniza nomes de colunas para serem mais fáceis de usar no código
        df.columns = df.columns.str.strip().str.lower()
        
        # Mapeamento para garantir consistência nos nomes das colunas
        rename_map = {
            'num cnt': 'Num_CNT', 'objeto cnt': 'Objeto_Cnt', 'responsável': 'Responsavel',
            'setor responsavel': 'Setor', 'empresa contratada': 'Empresa_Contratada',
            'statusprj(ajustada)': 'Status_Obra', 'statusprj': 'Status_Projeto',
            'valor contrato': 'Valor_Contrato', 'valor aditivos': 'Valor_Aditivos',
            'total contrato': 'Total_Contrato', 'saldo contratual': 'Saldo_Contratual',
            'total medido acumulado': 'Total_Medido_Acumulado', 'data fim cnt com aditivos': 'Data_Fim_Aditivos',
            'dias após vencimento': 'Dias_Apos_Vencimento', 'ano empreendimento': 'Ano_Empreendimento',
            'prazo contratual': 'Prazo_Contratual', 'data inicio cnt': 'Data_Inicio_Contrato'
        }
        df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)
        
        return df
    except Exception as e:
        st.error(f"Erro ao processar o arquivo Excel: {e}")
        return None

# --- 3. SIDEBAR (MENU LATERAL) ---

with st.sidebar:
    st.header("⚙️ Configurações")
    FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg" # ID do seu arquivo no Google Drive
    st.info(f"ID do Arquivo: ...{FILE_ID[-10:]}")
    
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
        
    st.markdown("---")
    st.image("https://i.imgur.com/t2yw4UH.png", width=80 ) # Exemplo de logo
    st.markdown("### SGEE+PO Dashboard")
    st.markdown("""
    Plataforma para visualização e análise de dados de empreendimentos e obras.
    """)

# --- 4. CORPO PRINCIPAL DO APLICATIVO ---

st.title("🏗️ SGEE+PO - Painel de Gestão de Obras")

# Carregamento e processamento principal dos dados
service = conectar_google_drive()
if service:
    with st.spinner("📥 Carregando e processando dados do Google Drive..."):
        file_stream = baixar_arquivo_drive(service, FILE_ID)
        if file_stream:
            df = processar_dados_excel(file_stream)
            
            if df is not None and not df.empty:
                st.success("✅ Dados carregados e processados com sucesso!")

                # --- Engenharia de Features e Cálculos ---
                df_calc = df.copy()
                
                # Converte colunas para os tipos corretos, tratando erros
                if 'Data_Fim_Aditivos' in df_calc.columns:
                    df_calc['Data_Fim_Aditivos'] = pd.to_datetime(df_calc['Data_Fim_Aditivos'], errors='coerce')
                    hoje = pd.Timestamp.now().normalize()
                    df_calc['Dias_Restantes'] = (df_calc['Data_Fim_Aditivos'] - hoje).dt.days
                
                if 'Dias_Apos_Vencimento' in df_calc.columns:
                    df_calc['Atraso'] = pd.to_numeric(df_calc['Dias_Apos_Vencimento'], errors='coerce').apply(lambda x: x if pd.notna(x) and x > 0 else 0)

                numeric_cols = ['Total_Medido_Acumulado', 'Total_Contrato', 'Valor_Contrato', 'Valor_Aditivos']
                for col in numeric_cols:
                    if col in df_calc.columns:
                        df_calc[col] = pd.to_numeric(df_calc[col], errors='coerce').fillna(0)

                if 'Total_Medido_Acumulado' in df_calc.columns and 'Total_Contrato' in df_calc.columns:
                    df_calc['%_Executado'] = df_calc.apply(lambda r: (r['Total_Medido_Acumulado'] / r['Total_Contrato'] * 100) if r['Total_Contrato'] > 0 else 0, axis=1)
                
                if 'Valor_Contrato' in df_calc.columns and 'Valor_Aditivos' in df_calc.columns:
                    df_calc['%_Aditivo'] = df_calc.apply(lambda r: (r['Valor_Aditivos'] / r['Valor_Contrato'] * 100) if r['Valor_Contrato'] > 0 else 0, axis=1)

                # --- Abas para Organização ---
                tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "💰 Análise Financeira", "📋 Dados Detalhados"])

                with tab1:
                    st.header("Resumo dos Indicadores Principais")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total de Contratos", len(df_calc))
                    
                    status_col = 'Status_Obra' if 'Status_Obra' in df_calc.columns else 'Status_Projeto'
                    if status_col in df_calc.columns:
                        em_andamento = df_calc[df_calc[status_col].str.contains('Andamento|Execução', case=False, na=False)].shape[0]
                        col2.metric("Em Andamento/Execução", em_andamento)
                    
                    col3.metric("Responsáveis Únicos", df_calc['Responsavel'].nunique() if 'Responsavel' in df_calc.columns else 0)
                    col4.metric("Setores Únicos", df_calc['Setor'].nunique() if 'Setor' in df_calc.columns else 0)
                    
                    st.markdown("---")
                    st.header("Análises Gráficas")
                    col_g1, col_g2 = st.columns(2)
                    with col_g1:
                        if 'Setor' in df_calc.columns and not df_calc['Setor'].empty:
                            st.subheader("Contratos por Setor")
                            setor_counts = df_calc['Setor'].value_counts()
                            fig = px.pie(values=setor_counts.values, names=setor_counts.index, hole=0.4)
                            st.plotly_chart(fig, use_container_width=True)
                    with col_g2:
                        if 'Responsavel' in df_calc.columns and not df_calc['Responsavel'].empty:
                            st.subheader("Top 10 Responsáveis")
                            resp_counts = df_calc['Responsavel'].value_counts().nlargest(10)
                            fig = px.bar(y=resp_counts.index, x=resp_counts.values, orientation='h', labels={'y': '', 'x': 'Nº de Contratos'})
                            fig.update_layout(yaxis={'categoryorder':'total ascending'})
                            st.plotly_chart(fig, use_container_width=True)

                with tab2:
                    st.header("Análise de Aditivos e Valores")
                    if '%_Aditivo' in df_calc.columns:
                        df_aditivo_filtrado = df_calc[df_calc['%_Aditivo'] <= 50]
                        soma_contrato = df_aditivo_filtrado['Valor_Contrato'].sum()
                        soma_aditivo = df_aditivo_filtrado['Valor_Aditivos'].sum()
                        indice_global = (soma_aditivo / soma_contrato * 100) if soma_contrato > 0 else 0
                        
                        colA1, colA2, colA3 = st.columns(3)
                        colA1.metric("Somatório Valor Contrato (Aditivo ≤ 50%)", f"R$ {soma_contrato:,.2f}")
                        colA2.metric("Somatório Valor Aditivos (Aditivo ≤ 50%)", f"R$ {soma_aditivo:,.2f}")
                        colA3.metric("Índice Global de Aditivos", f"{indice_global:.2f}%")
                    else:
                        st.warning("Colunas 'Valor_Contrato' e 'Valor_Aditivos' não encontradas para calcular os indicadores.")

                with tab3:
                    st.header("Filtros e Tabela de Dados")
                    
                    # --- Filtros ---
                    df_filtrado = df_calc.copy()
                    col_f1, col_f2, col_f3 = st.columns(3)
                    
                    busca = col_f1.text_input("🔎 Buscar em todos os campos", "")
                    if busca:
                        df_filtrado = df_filtrado[df_filtrado.apply(lambda row: any(busca.lower() in str(cell).lower() for cell in row), axis=1)]

                    filtro_setor = col_f2.selectbox("Filtrar por Setor", ['Todos'] + sorted(df_calc['Setor'].dropna().unique().tolist()), key='setor')
                    if filtro_setor != 'Todos':
                        df_filtrado = df_filtrado[df_filtrado['Setor'] == filtro_setor]
                    
                    filtro_resp = col_f3.selectbox("Filtrar por Responsável", ['Todos'] + sorted(df_calc['Responsavel'].dropna().unique().tolist()), key='resp')
                    if filtro_resp != 'Todos':
                        df_filtrado = df_filtrado[df_filtrado['Responsavel'] == filtro_resp]
                    
                    st.info(f"Exibindo {len(df_filtrado)} de {len(df_calc)} registros.")
                    
                    # --- Tabela de Dados ---
                    colunas_exibir = [
                        'Num_CNT', 'Objeto_Cnt', 'Empresa_Contratada', 'Status_Obra', 'Responsavel', 'Setor',
                        'Data_Fim_Aditivos', 'Dias_Restantes', 'Atraso', 'Valor_Contrato', 'Valor_Aditivos',
                        'Total_Contrato', 'Total_Medido_Acumulado', '%_Executado', '%_Aditivo'
                    ]
                    colunas_validas = [c for c in colunas_exibir if c in df_filtrado.columns]
                    st.dataframe(df_filtrado[colunas_validas], use_container_width=True, height=500)

                    # --- Download ---
                    csv = df_filtrado.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Baixar Dados Filtrados (CSV)",
                        data=csv,
                        file_name="dados_filtrados_sgee.csv",
                        mime="text/csv",
                    )

            else:
                st.warning("⚠️ Nenhum dado encontrado na planilha ou o arquivo está vazio.")
        else:
            st.error("❌ Falha ao baixar o arquivo do Google Drive. Verifique o ID do arquivo e as permissões.")
else:
    st.error("❌ Conexão com o Google Drive falhou. O painel não pode ser carregado.")


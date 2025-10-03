import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from st_aggrid import AgGrid, GridOptionsBuilder
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="SGEE+PO - Gestão de Obras",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
 )

# CSS customizado
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap' );
    * { font-family: 'Inter', sans-serif; }
    .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 0.5rem; }
    .compact-header { text-align: center; padding: 15px 20px; margin-bottom: 15px; background: rgba(255,255,255,0.1); border-radius: 15px; backdrop-filter: blur(10px); }
    .compact-title { font-size: 2.5rem; font-weight: 700; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 5px; }
    .compact-subtitle { font-size: 1.2rem; color: rgba(255, 255, 255, 0.9); font-weight: 400; margin: 0; }
    .horizontal-panel { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(20px); border-radius: 15px; padding: 20px; margin: 10px 0; box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); }
    .section-title-compact { font-size: 1.3rem; font-weight: 600; color: #333; margin-bottom: 15px; position: relative; padding-left: 12px; }
    .section-title-compact::before { content: ''; position: absolute; left: 0; top: 50%; transform: translateY(-50%); width: 3px; height: 20px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 2px; }
    .stMetric { background: linear-gradient(145deg, #f8f9ff, #e8ecff); border-radius: 12px; padding: 15px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.1); border-left: 4px solid #667eea; }
    .data-table-optimized { background: white; border-radius: 15px; padding: 20px; box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08); margin-top: 15px; }
    .tip-compact { background: linear-gradient(135deg, #e3f2fd, #bbdefb); border-radius: 10px; padding: 12px 16px; margin: 10px 0; border-left: 3px solid #2196f3; color: #1565c0; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

# Funções de Conexão e Processamento de Dados
@st.cache_resource
def conectar_google_drive():
    try:
        credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/drive.readonly"] )
        return build("drive", "v3", credentials=credentials)
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
        while not done:
            status, done = downloader.next_chunk()
        file_stream.seek(0)
        return file_stream
    except Exception as e:
        st.error(f"Erro ao baixar o arquivo: {e}")
        return None

@st.cache_data(ttl=3600)
def processar_dados_excel(file_stream):
    try:
        df = pd.read_excel(file_stream, engine="openpyxl")
        df = df.dropna(how="all")
        df.columns = df.columns.str.strip()

        # Mapeamento de colunas essenciais para garantir que existam
        essential_cols = {
            'Base SGEE.Valor Contrato': 0, 'Base SGEE.Valor Aditivos': 0, '% Aditivo': 0,
            'Base SGEE.Total Medido Acumulado': 0, 'Base SGEE.Saldo Contratual': 0, 'Base SGEE.Prazo Contratual': 0,
            'Base SGEE.Total Contrato': 0, 'Base SGEE.Data Fim Cnt Com Aditivos': pd.NaT,
            'Base SGEE.Setor Responsavel': 'N/A', 'Base SGEE.Responsavel': 'N/A',
            'Base SGEE.Status Contrato': 'N/A', 'Base SGEE.Empresa Contratada': 'N/A'
        }
        for col, default in essential_cols.items():
            if col not in df.columns:
                df[col] = default
            if pd.api.types.is_numeric_dtype(type(default)):
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            if pd.api.types.is_datetime64_any_dtype(type(default)):
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Coluna Calculada: Status do Prazo
        hoje = datetime.now()
        vencendo_em_30_dias = hoje + timedelta(days=30)
        df['Status do Prazo'] = 'Em Dia'
        df.loc[df['Base SGEE.Data Fim Cnt Com Aditivos'] < hoje, 'Status do Prazo'] = 'Vencido'
        df.loc[(df['Base SGEE.Data Fim Cnt Com Aditivos'] >= hoje) & (df['Base SGEE.Data Fim Cnt Com Aditivos'] <= vencendo_em_30_dias), 'Status do Prazo'] = 'Vencendo em 30 Dias'

        st.success("✅ Dados carregados e processados com sucesso.")
        return df
    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo Excel: {e}")
        return None

# --- Início da Interface ---
st.markdown("<div class='compact-header'><h1 class='compact-title'>🏗️ SGEE+PO - Gestão de Obras</h1><p class='compact-subtitle'>Dashboard Inteligente para Análise e Monitoramento de Projetos</p></div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<div style='text-align: center; padding: 20px; background: rgba(255,255,255,0.15); border-radius: 15px; margin-bottom: 20px;'><h3 style='color: white; font-weight: 600;'>⚙️ Painel de Controle</h3></div>", unsafe_allow_html=True)
    FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

try:
    service = conectar_google_drive()
    if service:
        with st.spinner("📥 Carregando e processando dados..."):
            file_stream = baixar_arquivo_drive(service, FILE_ID)
            if file_stream:
                df = processar_dados_excel(file_stream)
                
                if df is not None and not df.empty:
                    st.markdown("<div class='horizontal-panel'><h3 class='section-title-compact'>🔍 Sistema de Busca e Filtros</h3></div>", unsafe_allow_html=True)
                    
                    # Filtros principais
                    col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns(4)
                    filtro_setor = col_filtro1.selectbox("🏢 Setor", ["🌐 Todos"] + sorted(df["Base SGEE.Setor Responsavel"].dropna().unique().tolist()))
                    filtro_resp = col_filtro2.selectbox("👤 Responsável", ["🌐 Todos"] + sorted(df["Base SGEE.Responsavel"].dropna().unique().tolist()))
                    filtro_status = col_filtro3.selectbox("📋 Status do Contrato", ["🌐 Todos"] + sorted(df["Base SGEE.Status Contrato"].dropna().unique().tolist()))
                    filtro_prazo = col_filtro4.selectbox("🚦 Status do Prazo", ["🌐 Todos"] + sorted(df["Status do Prazo"].dropna().unique().tolist()))

                    # Aplicação dos filtros
                    df_filtrado = df.copy()
                    if filtro_setor != "🌐 Todos": df_filtrado = df_filtrado[df_filtrado["Base SGEE.Setor Responsavel"] == filtro_setor]
                    if filtro_resp != "🌐 Todos": df_filtrado = df_filtrado[df_filtrado["Base SGEE.Responsavel"] == filtro_resp]
                    if filtro_status != "🌐 Todos": df_filtrado = df_filtrado[df_filtrado["Base SGEE.Status Contrato"] == filtro_status]
                    if filtro_prazo != "🌐 Todos": df_filtrado = df_filtrado[df_filtrado["Status do Prazo"] == filtro_prazo]
                    
                    st.markdown("<div class='horizontal-panel'><h3 class='section-title-compact'>📈 Indicadores Chave</h3></div>", unsafe_allow_html=True)
                    
                    # Cálculos dos Indicadores
                    total_contratos = len(df_filtrado)
                    valor_total_contrato = df_filtrado['Base SGEE.Total Contrato'].sum()
                    total_medido = df_filtrado['Base SGEE.Total Medido Acumulado'].sum()
                    saldo_total = df_filtrado['Base SGEE.Saldo Contratual'].sum()
                    
                    perc_executado = (total_medido / valor_total_contrato * 100) if valor_total_contrato > 0 else 0
                    perc_saldo = (saldo_total / valor_total_contrato * 100) if valor_total_contrato > 0 else 0
                    
                    df_aditivo_valido = df_filtrado[df_filtrado['% Aditivo'] <= 0.50]
                    soma_aditivos = df_aditivo_valido['Base SGEE.Valor Aditivos'].sum()
                    soma_contrato_base = df_aditivo_valido['Base SGEE.Valor Contrato'].sum()
                    indice_aditivo = (soma_aditivos / soma_contrato_base * 100) if soma_contrato_base > 0 else 0

                    # Exibição dos Indicadores
                    cols_metricas1 = st.columns(4)
                    cols_metricas1[0].metric("📊 Total de Contratos", f"{total_contratos:,}")
                    cols_metricas1[1].metric("💲 Valor Total (Contratos)", f"R$ {valor_total_contrato:,.2f}")
                    cols_metricas1[2].metric("💰 Saldo Contratual Total", f"R$ {saldo_total:,.2f}")
                    cols_metricas1[3].metric("➕ Índice de Aditivo Global", f"{indice_aditivo:.2f}%")

                    cols_metricas2 = st.columns(2)
                    cols_metricas2[0].metric("✅ Percentual Executado", f"{perc_executado:.2f}%")
                    cols_metricas2[1].metric("⏳ Percentual de Saldo", f"{perc_saldo:.2f}%")

                    # Tabela de Dados Detalhada
                    st.markdown("<div class='horizontal-panel'><h3 class='section-title-compact'>📋 Dados Detalhados</h3></div>", unsafe_allow_html=True)
                    if not df_filtrado.empty:
                        st.markdown("<div class='tip-compact'><strong>💡 Dica:</strong> Clique no ícone de funil ao lado de cada coluna para filtrar os dados diretamente na tabela.</div>", unsafe_allow_html=True)
                        
                        gb = GridOptionsBuilder.from_dataframe(df_filtrado)
                        gb.configure_default_column(filterable=True, sortable=True, resizable=True, wrapText=True, autoHeight=True)
                        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
                        gb.configure_selection(selection_mode='multiple', use_checkbox=True)
                        
                        grid_options = gb.build()
                        
                        st.markdown("<div class='data-table-optimized'>", unsafe_allow_html=True)
                        AgGrid(
                            df_filtrado, 
                            gridOptions=grid_options, 
                            height=600, 
                            allow_unsafe_jscode=True, 
                            enable_enterprise_modules=True, # Garante que os filtros de coluna funcionem
                            theme='streamlit'
                        )
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ Nenhum registro encontrado com os filtros aplicados.")

                else:
                    st.warning("⚠️ Nenhum dado encontrado ou o arquivo está vazio.")
            else:
                st.error("❌ Falha ao baixar o arquivo do Google Drive.")
    else:
        st.error("❌ Falha na conexão com o Google Drive.")

except Exception as e:
    st.error(f"❌ Ocorreu um erro inesperado na aplicação: {e}")

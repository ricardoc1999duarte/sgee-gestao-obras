import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import openpyxl
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="SGEE+PO - Gestão de Obras",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado ultra melhorado
st.markdown("""
    <style>
    /* Importar fontes do Google */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Reset e estilos gerais */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
    }
    
    /* Painéis principais com glassmorphism */
    .glass-panel {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
        color: #333;
    }
    
    .glass-panel:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
    }
    
    /* Métricas estilizadas */
    .metric-container {
        background: linear-gradient(145deg, #f8f9ff, #e8ecff);
        border-radius: 16px;
        padding: 25px;
        margin: 10px 0;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.1);
        border-left: 5px solid #667eea;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
    
    .metric-container:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 35px rgba(102, 126, 234, 0.2);
    }
    
    /* Títulos e textos */
    .main-title {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 10px;
        text-shadow: none;
    }
    
    .subtitle {
        font-size: 1.5rem;
        color: rgba(255, 255, 255, 0.9);
        text-align: center;
        font-weight: 400;
        margin-bottom: 5px;
    }
    
    .description {
        font-size: 1.1rem;
        color: rgba(255, 255, 255, 0.8);
        text-align: center;
        font-weight: 300;
    }
    
    .section-title {
        font-size: 1.8rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 20px;
        position: relative;
        padding-left: 15px;
    }
    
    .section-title::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 30px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 2px;
    }
    
    /* Busca global estilizada */
    .search-box {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .search-box:focus-within {
        border-color: #667eea;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
    }
    
    /* Inputs customizados */
    .stTextInput > div > div > input {
        background: rgba(248, 249, 255, 0.8);
        border: 2px solid #e1e5e9;
        border-radius: 12px;
        padding: 15px 20px;
        font-size: 16px;
        color: #333;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        background: white;
    }
    
    .stSelectbox > div > div {
        background: rgba(248, 249, 255, 0.8);
        border: 2px solid #e1e5e9;
        border-radius: 12px;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #667eea;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
    }
    
    /* Botões estilizados */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(40, 167, 69, 0.4);
    }
    
    /* Gráficos */
    .chart-container {
        background: white;
        border-radius: 20px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .chart-container:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.12);
    }
    
    /* Tabela de dados */
    .data-table {
        background: white;
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Sidebar */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Cards informativos */
    .info-card {
        background: linear-gradient(145deg, #f8f9ff, #e8ecff);
        border-radius: 16px;
        padding: 20px;
        margin: 15px 0;
        border-left: 5px solid #667eea;
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.1);
        color: #333;
        transition: all 0.3s ease;
    }
    
    .info-card:hover {
        transform: translateX(5px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
    }
    
    .info-card h4 {
        color: #667eea;
        font-weight: 600;
        margin-bottom: 10px;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 25px;
        font-size: 12px;
        font-weight: 600;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-em-andamento {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
    }
    
    .status-concluido {
        background: linear-gradient(135deg, #007bff, #0056b3);
        color: white;
        box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3);
    }
    
    .status-pausado {
        background: linear-gradient(135deg, #ffc107, #e0a800);
        color: #333;
        box-shadow: 0 4px 15px rgba(255, 193, 7, 0.3);
    }
    
    /* Animações */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in-up {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.5rem;
        }
        
        .glass-panel {
            padding: 20px;
            margin: 15px 0;
        }
        
        .metric-container {
            padding: 20px;
        }
    }
    
    /* Melhorias específicas para métricas do Streamlit */
    .stMetric {
        background: linear-gradient(145deg, #f8f9ff, #e8ecff);
        border-radius: 16px;
        padding: 25px;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.1);
        border-left: 5px solid #667eea;
        transition: all 0.3s ease;
        color: #333;
    }
    
    .stMetric:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 35px rgba(102, 126, 234, 0.2);
    }
    
    .stMetric > div {
        color: #333;
    }
    
    .stMetric [data-testid="metric-container"] {
        background: transparent;
        border: none;
        box-shadow: none;
    }
    
    /* Footer */
    .footer-text {
        color: rgba(255, 255, 255, 0.9);
        font-weight: 300;
    }
    
    /* Dicas e informações */
    .tip-box {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        border-radius: 12px;
        padding: 15px 20px;
        margin: 15px 0;
        border-left: 4px solid #2196f3;
        color: #1565c0;
        font-size: 14px;
    }
    
    .tip-box strong {
        color: #0d47a1;
    }
    </style>
""", unsafe_allow_html=True)

# Função para conectar ao Google Drive
@st.cache_resource
def conectar_google_drive():
    """
    Conecta ao Google Drive usando as credenciais do service account
    """
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        service = build("drive", "v3", credentials=credentials)
        return service
    except Exception as e:
        st.error(f"Erro ao conectar ao Google Drive: {e}")
        return None

# Função para baixar arquivo do Google Drive
@st.cache_data(ttl=3600)
def baixar_arquivo_drive(_service, file_id):
    """
    Baixa o arquivo Excel do Google Drive
    """
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
        st.error(f"Erro ao baixar arquivo: {e}")
        return None

# Função para processar dados do Excel
@st.cache_data(ttl=3600)
def processar_dados_excel(file_stream):
    """
    Processa o arquivo Excel e retorna um DataFrame
    """
    try:
        df = pd.read_excel(file_stream, sheet_name="SGEEePO", engine="openpyxl")
        df = df.dropna(how="all")
        df.columns = df.columns.str.strip()
        
        # Remove duplicatas
        df_original_size = len(df)
        df = df.drop_duplicates()
        duplicatas_removidas = df_original_size - len(df)
        
        if duplicatas_removidas > 0:
            st.success(f"🧹 Removidas {duplicatas_removidas} linhas duplicadas dos dados")
        
        return df
    except Exception as e:
        st.error(f"Erro ao processar Excel: {e}")
        return None

# Função de busca global CORRIGIDA
def aplicar_busca_global(df, termo_busca):
    """
    Aplica busca global corrigida em todas as colunas do DataFrame
    """
    if not termo_busca or not termo_busca.strip():
        return df
    
    termo_busca = str(termo_busca).lower().strip()
    
    # Função para verificar se o termo está em qualquer coluna da linha
    def linha_contem_termo(row):
        for valor in row:
            if pd.notna(valor):  # Verifica se não é NaN
                if termo_busca in str(valor).lower():
                    return True
        return False
    
    # Aplica a função a cada linha
    mask = df.apply(linha_contem_termo, axis=1)
    return df[mask]

# Função para criar gráficos melhorados
def criar_graficos_dashboard(df):
    """
    Cria gráficos melhorados para o dashboard
    """
    graficos = {}
    
    # Configurações de cores personalizadas
    cores_personalizadas = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe']
    
    # Gráfico 1: Distribuição por Setor
    if "Base SGEE.Setor Responsavel" in df.columns:
        setor_counts = df["Base SGEE.Setor Responsavel"].value_counts().head(8)
        if not setor_counts.empty:
            fig1 = px.pie(
                values=setor_counts.values, 
                names=setor_counts.index,
                title="🏢 Distribuição por Setor Responsável",
                color_discrete_sequence=cores_personalizadas,
                hole=0.5
            )
            fig1.update_traces(
                textposition="inside", 
                textinfo="percent+label",
                textfont_size=12,
                hovertemplate="<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>"
            )
            fig1.update_layout(
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, x=1.05),
                font=dict(size=12, color="#333", family="Inter"),
                title_font_size=18,
                title_font_color="#333",
                title_x=0.5,
                height=500
            )
            graficos["setor"] = fig1
    
    # Gráfico 2: Status dos Contratos
    if "Base SGEE.Status Contrato" in df.columns:
        status_counts = df["Base SGEE.Status Contrato"].value_counts()
        if not status_counts.empty:
            fig2 = px.bar(
                x=status_counts.values,
                y=status_counts.index,
                orientation="h",
                title="📋 Status dos Contratos",
                labels={"x": "Quantidade", "y": "Status"},
                color=status_counts.values,
                color_continuous_scale="Viridis"
            )
            fig2.update_layout(
                showlegend=False,
                font=dict(size=12, color="#333", family="Inter"),
                title_font_size=18,
                title_font_color="#333",
                title_x=0.5,
                yaxis={"categoryorder": "total ascending"},
                height=400,
                xaxis_title="Quantidade de Contratos",
                yaxis_title="Status"
            )
            fig2.update_traces(
                hovertemplate="<b>%{y}</b><br>Quantidade: %{x}<extra></extra>"
            )
            graficos["status"] = fig2
    
    # Gráfico 3: Valores por Ano
    if "Base SGEE.Ano Finalização Contrato" in df.columns and "Base SGEE.Total Contrato" in df.columns:
        df_temp = df.dropna(subset=["Base SGEE.Ano Finalização Contrato", "Base SGEE.Total Contrato"])
        if not df_temp.empty:
            valores_ano = df_temp.groupby("Base SGEE.Ano Finalização Contrato")["Base SGEE.Total Contrato"].sum().reset_index()
            fig3 = px.line(
                valores_ano,
                x="Base SGEE.Ano Finalização Contrato",
                y="Base SGEE.Total Contrato",
                title="📈 Evolução dos Valores Contratuais por Ano",
                markers=True
            )
            fig3.update_traces(
                line=dict(width=4, color="#667eea"), 
                marker=dict(size=10, color="#764ba2"),
                hovertemplate="<b>Ano: %{x}</b><br>Valor Total: R$ %{y:,.2f}<extra></extra>"
            )
            fig3.update_layout(
                font=dict(size=12, color="#333", family="Inter"),
                title_font_size=18,
                title_font_color="#333",
                title_x=0.5,
                xaxis_title="Ano de Finalização",
                yaxis_title="Valor Total (R$)",
                height=400
            )
            graficos["valores_ano"] = fig3
    
    # Gráfico 4: Top 10 Empresas Contratadas
    if "Base SGEE.Empresa Contratada" in df.columns:
        empresa_counts = df["Base SGEE.Empresa Contratada"].value_counts().head(10)
        if not empresa_counts.empty:
            fig4 = px.bar(
                x=empresa_counts.index,
                y=empresa_counts.values,
                title="🏆 Top 10 Empresas Contratadas",
                labels={"x": "Empresa", "y": "Número de Contratos"},
                color=empresa_counts.values,
                color_continuous_scale="Blues"
            )
            fig4.update_layout(
                showlegend=False,
                font=dict(size=12, color="#333", family="Inter"),
                title_font_size=18,
                title_font_color="#333",
                title_x=0.5,
                xaxis={"tickangle": 45},
                height=500,
                xaxis_title="Empresas",
                yaxis_title="Número de Contratos"
            )
            fig4.update_traces(
                hovertemplate="<b>%{x}</b><br>Contratos: %{y}<extra></extra>"
            )
            graficos["empresas"] = fig4
    
    return graficos

# Header principal
st.markdown("""
    <div style='text-align: center; padding: 40px 20px; margin-bottom: 30px;' class='fade-in-up'>
        <h1 class='main-title'>🏗️ SGEE+PO</h1>
        <h2 class='subtitle'>Sistema de Gestão de Empreendimentos e Obras</h2>
        <p class='description'>Dashboard Inteligente para Análise e Monitoramento de Projetos</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# Sidebar melhorada
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 25px; background: rgba(255,255,255,0.15); border-radius: 20px; margin-bottom: 25px; backdrop-filter: blur(10px);'>
            <h2 style='color: white; margin-bottom: 15px; font-weight: 600;'>⚙️ Painel de Controle</h2>
        </div>
    """, unsafe_allow_html=True)
    
    FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
    
    st.markdown("""
        <div class='info-card'>
            <h4>📂 Status da Conexão</h4>
            <p style='color: #28a745; font-weight: 500;'>✅ Conectado ao Google Drive</p>
            <p style='font-size: 12px; color: #666;'>Dados sincronizados automaticamente</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("""
        <div class='info-card'>
            <h4>🚀 Funcionalidades Avançadas</h4>
            <div style='margin-top: 15px;'>
                <div style='display: flex; align-items: center; margin: 8px 0;'>
                    <span style='color: #28a745; margin-right: 8px;'>✅</span>
                    <span>Visualização em tempo real</span>
                </div>
                <div style='display: flex; align-items: center; margin: 8px 0;'>
                    <span style='color: #28a745; margin-right: 8px;'>✅</span>
                    <span>Busca global inteligente</span>
                </div>
                <div style='display: flex; align-items: center; margin: 8px 0;'>
                    <span style='color: #28a745; margin-right: 8px;'>✅</span>
                    <span>Filtros avançados</span>
                </div>
                <div style='display: flex; align-items: center; margin: 8px 0;'>
                    <span style='color: #28a745; margin-right: 8px;'>✅</span>
                    <span>Análise gráfica interativa</span>
                </div>
                <div style='display: flex; align-items: center; margin: 8px 0;'>
                    <span style='color: #28a745; margin-right: 8px;'>✅</span>
                    <span>Remoção automática de duplicatas</span>
                </div>
                <div style='display: flex; align-items: center; margin: 8px 0;'>
                    <span style='color: #28a745; margin-right: 8px;'>✅</span>
                    <span>Exportação de dados</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Conectar ao Google Drive e processar dados
try:
    service = conectar_google_drive()
    
    if service:
        with st.spinner("📥 Carregando dados do Google Drive..."):
            file_stream = baixar_arquivo_drive(service, FILE_ID)
            
            if file_stream:
                df = processar_dados_excel(file_stream)
                
                if df is not None and not df.empty:
                    st.success("✅ Dados carregados com sucesso!")
                    
                    # Indicadores principais
                    st.markdown("""
                        <div class='glass-panel fade-in-up'>
                            <h3 class='section-title'>📈 Indicadores Principais</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("📊 Total de Registros", f"{len(df):,}")
                    
                    with col2:
                        if "Base SGEE.Status Contrato" in df.columns:
                            em_andamento = df[df["Base SGEE.Status Contrato"].str.contains("andamento", case=False, na=False)].shape[0]
                            st.metric("🔄 Em Andamento", f"{em_andamento:,}")
                        else:
                            st.metric("🔄 Em Andamento", "N/A")
                    
                    with col3:
                        if "Responsavel" in df.columns:
                            responsaveis = df["Responsavel"].nunique()
                            st.metric("👥 Responsáveis", f"{responsaveis:,}")
                        else:
                            st.metric("👥 Responsáveis", "N/A")
                    
                    with col4:
                        if "Base SGEE.Setor Responsavel" in df.columns:
                            setores = df["Base SGEE.Setor Responsavel"].nunique()
                            st.metric("🏢 Setores", f"{setores:,}")
                        else:
                            st.metric("🏢 Setores", "N/A")
                    
                    st.markdown("---")
                    
                    # Sistema de busca e filtros
                    st.markdown("""
                        <div class='glass-panel fade-in-up'>
                            <h3 class='section-title'>🔍 Sistema de Busca Inteligente</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Busca Global
                    col_busca, col_info = st.columns([3, 1])
                    
                    with col_busca:
                        busca_global = st.text_input(
                            "🔍 Busca Global",
                            "",
                            placeholder="Digite qualquer termo para buscar em todas as colunas (ex: 'SUDECAP', 'andamento', '2024')...",
                            help="🎯 A busca é realizada em todas as colunas simultaneamente, ignorando maiúsculas/minúsculas"
                        )
                    
                    with col_info:
                        st.markdown("""
                            <div class='tip-box' style='margin-top: 25px;'>
                                <strong>💡 Dica:</strong> Use termos específicos para resultados mais precisos
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Aplicar busca global
                    df_busca = aplicar_busca_global(df, busca_global)
                    
                    # Filtros específicos
                    st.markdown("#### 🎛️ Filtros Avançados")
                    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
                    
                    with col_filtro1:
                        if "Base SGEE.Setor Responsavel" in df_busca.columns:
                            setores_list = ["🌐 Todos"] + sorted(df_busca["Base SGEE.Setor Responsavel"].dropna().unique().tolist())
                            filtro_setor = st.selectbox("🏢 Setor", setores_list)
                        else:
                            filtro_setor = "🌐 Todos"
                    
                    with col_filtro2:
                        if "Responsavel" in df_busca.columns:
                            resp_list = ["🌐 Todos"] + sorted(df_busca["Responsavel"].dropna().unique().tolist())
                            filtro_resp = st.selectbox("👤 Responsável", resp_list)
                        else:
                            filtro_resp = "🌐 Todos"
                    
                    with col_filtro3:
                        if "Base SGEE.Status Contrato" in df_busca.columns:
                            status_list = ["🌐 Todos"] + sorted(df_busca["Base SGEE.Status Contrato"].dropna().unique().tolist())
                            filtro_status = st.selectbox("📋 Status", status_list)
                        else:
                            filtro_status = "🌐 Todos"
                    
                    # Aplicar filtros específicos
                    df_filtrado = df_busca.copy()
                    
                    if filtro_setor != "🌐 Todos" and "Base SGEE.Setor Responsavel" in df_filtrado.columns:
                        df_filtrado = df_filtrado[df_filtrado["Base SGEE.Setor Responsavel"] == filtro_setor]
                    
                    if filtro_resp != "🌐 Todos" and "Responsavel" in df_filtrado.columns:
                        df_filtrado = df_filtrado[df_filtrado["Responsavel"] == filtro_resp]
                    
                    if filtro_status != "🌐 Todos" and "Base SGEE.Status Contrato" in df_filtrado.columns:
                        df_filtrado = df_filtrado[df_filtrado["Base SGEE.Status Contrato"] == filtro_status]
                    
                    # Informações sobre filtros
                    col_info1, col_info2, col_download = st.columns([2, 2, 1])
                    
                    with col_info1:
                        st.info(f"📊 Exibindo **{len(df_filtrado):,}** de **{len(df):,}** registros")
                    
                    with col_info2:
                        if busca_global:
                            st.info(f"🔍 Termo de busca: **'{busca_global}'**")
                    
                    with col_download:
                        if not df_filtrado.empty:
                            csv = df_filtrado.to_csv(index=False).encode("utf-8")
                            st.download_button(
                                label="📥 Exportar CSV",
                                data=csv,
                                file_name=f"sgee_obras_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                    
                    # Dashboard de gráficos
                    if not df_filtrado.empty:
                        st.markdown("---")
                        st.markdown("""
                            <div class='glass-panel fade-in-up'>
                                <h3 class='section-title'>📊 Dashboard de Análises</h3>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        graficos = criar_graficos_dashboard(df_filtrado)
                        
                        # Layout dos gráficos
                        if "setor" in graficos and "status" in graficos:
                            col_graf1, col_graf2 = st.columns(2)
                            
                            with col_graf1:
                                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                                st.plotly_chart(graficos["setor"], use_container_width=True)
                                st.markdown("</div>", unsafe_allow_html=True)
                            
                            with col_graf2:
                                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                                st.plotly_chart(graficos["status"], use_container_width=True)
                                st.markdown("</div>", unsafe_allow_html=True)
                        
                        if "valores_ano" in graficos:
                            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                            st.plotly_chart(graficos["valores_ano"], use_container_width=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                        
                        if "empresas" in graficos:
                            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                            st.plotly_chart(graficos["empresas"], use_container_width=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Tabela de dados
                    st.markdown("---")
                    st.markdown("""
                        <div class='glass-panel fade-in-up'>
                            <h3 class='section-title'>📋 Dados Detalhados</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if not df_filtrado.empty:
                        st.markdown("""
                            <div class='tip-box'>
                                <strong>💡 Dicas de navegação:</strong><br>
                                • Clique no ícone <strong>☰</strong> ao lado de cada coluna para filtrar<br>
                                • Use <strong>Ctrl+Click</strong> para selecionar múltiplas linhas<br>
                                • Arraste as bordas das colunas para redimensionar<br>
                                • Use a barra lateral da tabela para filtros avançados
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Configurar AgGrid
                        gb = GridOptionsBuilder.from_dataframe(df_filtrado)
                        
                        gb.configure_default_column(
                            filterable=True,
                            sortable=True,
                            resizable=True,
                            editable=False,
                            wrapText=True,
                            autoHeight=True
                        )
                        
                        gb.configure_pagination(
                            paginationAutoPageSize=False,
                            paginationPageSize=25
                        )
                        
                        gb.configure_selection(
                            selection_mode='multiple',
                            use_checkbox=True
                        )
                        
                        gb.configure_side_bar()
                        grid_options = gb.build()
                        
                        st.markdown("<div class='data-table'>", unsafe_allow_html=True)
                        AgGrid(
                            df_filtrado,
                            gridOptions=grid_options,
                            update_mode=GridUpdateMode.MODEL_CHANGED,
                            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                            fit_columns_on_grid_load=False,
                            theme='streamlit',
                            height=600,
                            allow_unsafe_jscode=True,
                            enable_enterprise_modules=False
                        )
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ Nenhum registro encontrado com os filtros aplicados. Tente ajustar os critérios de busca.")
                    
                else:
                    st.warning("⚠️ Nenhum dado encontrado no arquivo")
            else:
                st.error("❌ Não foi possível baixar o arquivo do Google Drive")
    else:
        st.error("❌ Não foi possível conectar ao Google Drive")

except Exception as e:
    st.error(f"❌ Erro geral: {e}")
    st.markdown("""
        <div class='glass-panel'>
            <h4>🔧 Instruções de Configuração</h4>
            <ol>
                <li>No Streamlit Cloud, acesse <strong>Settings</strong> → <strong>Secrets</strong></li>
                <li>Adicione as credenciais do Google Drive no formato TOML</li>
            </ol>
        </div>
    """, unsafe_allow_html=True)

# Footer elegante
st.markdown("---")
st.markdown("""
    <div style='text-align: center; padding: 30px 20px; background: rgba(255,255,255,0.1); border-radius: 20px; margin-top: 40px; backdrop-filter: blur(10px);'>
        <p class='footer-text' style='font-size: 1.1rem; font-weight: 500; margin-bottom: 5px;'>🏗️ <strong>SGEE+PO</strong> - Sistema de Gestão de Empreendimentos e Obras</p>
        <p class='footer-text' style='font-size: 0.9rem; opacity: 0.8;'>Desenvolvido para otimizar o controle e monitoramento de projetos de infraestrutura</p>
        <p class='footer-text' style='font-size: 0.8rem; opacity: 0.6; margin-top: 10px;'>Versão 2.0 - Dashboard Inteligente</p>
    </div>
""", unsafe_allow_html=True)

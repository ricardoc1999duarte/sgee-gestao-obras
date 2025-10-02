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
import json

# Configuração da página
st.set_page_config(
    page_title="SGEE+PO - Gestão de Obras",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado otimizado para layout horizontal e título maior
st.markdown("""
    <style>
    /* Importar fontes do Google */
    @import url(\'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap\');
    
    /* Reset e estilos gerais */
    * {
        font-family: \'Inter\', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0.5rem;
    }
    
    /* Header compacto com título maior */
    .compact-header {
        text-align: center;
        padding: 15px 20px;
        margin-bottom: 15px;
        background: rgba(255,255,255,0.1);
        border-radius: 15px;
        backdrop-filter: blur(10px);
    }
    
    .compact-title {
        font-size: 2.5rem; /* Aumentado */
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    
    .compact-subtitle {
        font-size: 1.2rem; /* Aumentado */
        color: rgba(255, 255, 255, 0.9);
        font-weight: 400;
        margin: 0;
    }
    
    /* Painéis horizontais */
    .horizontal-panel {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
        color: #333;
    }
    
    .horizontal-panel:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.15);
    }
    
    /* Métricas em linha */
    .metrics-row {
        display: flex;
        gap: 15px;
        flex-wrap: wrap;
        justify-content: space-between;
    }
    
    .metric-card {
        background: linear-gradient(145deg, #f8f9ff, #e8ecff);
        border-radius: 12px;
        padding: 15px;
        flex: 1;
        min-width: 150px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.1);
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
    }
    
    /* Seção de títulos compactos */
    .section-title-compact {
        font-size: 1.3rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 15px;
        position: relative;
        padding-left: 12px;
    }
    
    .section-title-compact::before {
        content: \'\';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 3px;
        height: 20px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 2px;
    }
    
    /* Busca global compacta */
    .search-compact {
        background: white;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .search-compact:focus-within {
        border-color: #667eea;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.2);
    }
    
    /* Inputs customizados compactos */
    .stTextInput > div > div > input {
        background: rgba(248, 249, 255, 0.8);
        border: 2px solid #e1e5e9;
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 14px;
        color: #333;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        background: white;
    }
    
    .stSelectbox > div > div {
        background: rgba(248, 249, 255, 0.8);
        border: 2px solid #e1e5e9;
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Botões estilizados */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Botão de configuração especial */
    .config-button {
        background: linear-gradient(135deg, #28a745, #20c997) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3) !important;
    }
    
    .config-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(40, 167, 69, 0.4) !important;
    }
    
    /* Gráficos horizontais */
    .chart-horizontal {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .chart-horizontal:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
    }
    
    /* Tabela otimizada */
    .data-table-optimized {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-top: 15px;
    }
    
    /* Sidebar compacta */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Cards informativos compactos */
    .info-card-compact {
        background: linear-gradient(145deg, #f8f9ff, #e8ecff);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.1);
        color: #333;
        transition: all 0.3s ease;
    }
    
    .info-card-compact:hover {
        transform: translateX(3px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.15);
    }
    
    .info-card-compact h4 {
        color: #667eea;
        font-weight: 600;
        margin-bottom: 8px;
        font-size: 1rem;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .compact-title {
            font-size: 1.5rem;
        }
        
        .horizontal-panel {
            padding: 15px;
            margin: 8px 0;
        }
        
        .metrics-row {
            flex-direction: column;
        }
    }
    
    /* Melhorias específicas para métricas do Streamlit */
    .stMetric {
        background: linear-gradient(145deg, #f8f9ff, #e8ecff);
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.1);
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
        color: #333;
    }
    
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
    }
    
    .stMetric > div {
        color: #333;
    }
    
    .stMetric [data-testid=\'metric-container\'] {
        background: transparent;
        border: none;
        box-shadow: none;
    }
    
    /* Footer compacto */
    .footer-compact {
        text-align: center;
        padding: 15px 20px;
        background: rgba(255,255,255,0.1);
        border-radius: 15px;
        margin-top: 20px;
        backdrop-filter: blur(10px);
    }
    
    .footer-text {
        color: rgba(255, 255, 255, 0.9);
        font-weight: 300;
        font-size: 0.9rem;
    }
    
    /* Dicas compactas */
    .tip-compact {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        border-radius: 10px;
        padding: 12px 16px;
        margin: 10px 0;
        border-left: 3px solid #2196f3;
        color: #1565c0;
        font-size: 13px;
    }
    
    .tip-compact strong {
        color: #0d47a1;
    }
    
    /* Configuração de colunas */
    .column-config {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
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
    Processa o arquivo Excel e retorna um DataFrame com remoção avançada de duplicatas
    """
    try:
        df = pd.read_excel(file_stream, sheet_name="SGEEePO", engine="openpyxl")
        df = df.dropna(how="all")
        df.columns = df.columns.str.strip()
        
        # Tamanho original
        df_original_size = len(df)
        
        # Normalização de dados para melhor detecção de duplicatas
        df_normalizado = df.copy()
        
        # Normalizar strings (remover espaços extras, converter para minúsculas)
        for col in df_normalizado.select_dtypes(include=["object"]).columns:
            df_normalizado[col] = df_normalizado[col].astype(str).str.strip().str.lower()
        
        # Normalizar valores numéricos (arredondar para evitar diferenças mínimas)
        for col in df_normalizado.select_dtypes(include=["float64", "int64"]).columns:
            if df_normalizado[col].dtype == "float64":
                df_normalizado[col] = df_normalizado[col].round(2)
        
        # Identificar duplicatas baseado nos dados normalizados
        duplicatas_mask = df_normalizado.duplicated(keep="first")
        duplicatas_encontradas = duplicatas_mask.sum()
        
        # Remover duplicatas do DataFrame original
        df_limpo = df[~duplicatas_mask].copy()
        
        # Reset do índice
        df_limpo = df_limpo.reset_index(drop=True)
        
        # Relatório de limpeza
        linhas_removidas = df_original_size - len(df_limpo)
        
        if linhas_removidas > 0:
            st.success(f"🧹 **Limpeza de Dados Concluída:** {duplicatas_encontradas:,} duplicatas removidas ({(duplicatas_encontradas/df_original_size*100):.1f}%)")
        else:
            st.success("✅ Nenhuma duplicata encontrada nos dados")
        
        return df_limpo
        
    except Exception as e:
        st.error(f"❌ Erro ao processar Excel: {e}")
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

# Função para configurações de colunas
def get_configuracao_colunas_default():
    """
    Retorna configuração padrão das colunas
    """
    return {
        "Num CNT": {"width": 120, "visible": True, "pinned": "left"},
        "Objeto Cnt": {"width": 400, "visible": True},  # Bem maior
        "Nome Empreendimento": {"width": 350, "visible": True},  # Bem maior
        "Escopo": {"width": 500, "visible": True},  # Maior de todos
        "Base SGEE.Empresa Contratada": {"width": 250, "visible": True},
        "Base SGEE.Setor Responsavel": {"width": 150, "visible": True},
        "Base SGEE.Status Contrato": {"width": 130, "visible": True},
        "Base SGEE.Valor Contrato": {"width": 140, "visible": True, "type": "numericColumn"},
        "Base SGEE.Total Medido Acumulado": {"width": 160, "visible": True, "type": "numericColumn"},
        "Base SGEE.Saldo Contratual": {"width": 140, "visible": True, "type": "numericColumn"},
        "Base SGEE.Data Inicio Cnt": {"width": 120, "visible": True, "type": "dateColumn"},
        "Base SGEE.Data Fim Cnt Com Aditivos": {"width": 120, "visible": True, "type": "dateColumn"},
        "Responsavel": {"width": 150, "visible": True},
        "Base SGEE.Ano Finalização Contrato": {"width": 120, "visible": False},
        "Base SGEE.Total Contrato": {"width": 140, "visible": False, "type": "numericColumn"},
        "Base SGEE.Valor Aditivos": {"width": 140, "visible": True, "type": "numericColumn"},
        "Base SGEE.Prazo Contratual": {"width": 120, "visible": True, "type": "numericColumn"}
    }

# Função para salvar configurações
def salvar_configuracao_colunas(config):
    """
    Salva configuração das colunas no session state
    """
    st.session_state["config_colunas"] = config

# Função para carregar configurações
def carregar_configuracao_colunas():
    """
    Carrega configuração das colunas do session state
    """
    if "config_colunas" not in st.session_state:
        st.session_state["config_colunas"] = get_configuracao_colunas_default()
    return st.session_state["config_colunas"]

# Função para criar gráficos melhorados
def criar_graficos_dashboard(df):
    """
    Cria gráficos melhorados para o dashboard
    """
    graficos = {}
    
    # Configurações de cores personalizadas
    cores_personalizadas = ["#667eea", "#764ba2", "#f093fb", "#f5576c", "#4facfe", "#00f2fe"]
    
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
                textfont_size=11,
                hovertemplate="<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>"
            )
            fig1.update_layout(
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, x=1.05),
                font=dict(size=11, color="#333", family="Inter"),
                title_font_size=16,
                title_font_color="#333",
                title_x=0.5,
                height=350
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
                font=dict(size=11, color="#333", family="Inter"),
                title_font_size=16,
                title_font_color="#333",
                title_x=0.5,
                yaxis={"categoryorder": "total ascending"},
                height=350,
                xaxis_title="Quantidade de Contratos",
                yaxis_title="Status"
            )
            fig2.update_traces(
                hovertemplate="<b>%{y}</b><br>Quantidade: %{x}<extra></extra>"
            )
            graficos["status"] = fig2
    
    # Gráfico 3: Top 10 Empresas Contratadas
    if "Base SGEE.Empresa Contratada" in df.columns:
        empresa_counts = df["Base SGEE.Empresa Contratada"].value_counts().head(10)
        if not empresa_counts.empty:
            fig3 = px.bar(
                x=empresa_counts.index,
                y=empresa_counts.values,
                title="🏆 Top 10 Empresas Contratadas",
                labels={"x": "Empresa", "y": "Número de Contratos"},
                color=empresa_counts.values,
                color_continuous_scale="Blues"
            )
            fig3.update_layout(
                showlegend=False,
                font=dict(size=11, color="#333", family="Inter"),
                title_font_size=16,
                title_font_color="#333",
                title_x=0.5,
                xaxis={"tickangle": 45},
                height=350,
                xaxis_title="Empresas",
                yaxis_title="Número de Contratos"
            )
            fig3.update_traces(
                hovertemplate="<b>%{x}</b><br>Contratos: %{y}<extra></extra>"
            )
            graficos["empresas"] = fig3
    
    return graficos

# Header principal compacto
st.markdown("""
    <div class=\'compact-header\'>
        <h1 class=\'compact-title\'>🏗️ SGEE+PO - Sistema de Gestão de Empreendimentos e Obras</h1>
        <p class=\'compact-subtitle\'>Dashboard Inteligente para Análise e Monitoramento de Projetos</p>
    </div>
    """, unsafe_allow_html=True)

# Sidebar melhorada e compacta
with st.sidebar:
    st.markdown("""
        <div style=\'text-align: center; padding: 20px; background: rgba(255,255,255,0.15); border-radius: 15px; margin-bottom: 20px; backdrop-filter: blur(10px);\'>
            <h3 style=\'color: white; margin-bottom: 10px; font-weight: 600;\'>⚙️ Painel de Controle</h3>
        </div>
        """, unsafe_allow_html=True)
    
    FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
    
    st.markdown("""
        <div class=\'info-card-compact\'>
            <h4>📂 Status da Conexão</h4>
            <p style=\'color: #28a745; font-weight: 500;\'>✅ Conectado ao Google Drive</p>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    # Botão de configuração de colunas
    if st.button("⚙️ Configurar Colunas", use_container_width=True, key="config_btn"):
        st.session_state["mostrar_config"] = not st.session_state.get("mostrar_config", False)

# Conectar ao Google Drive e processar dados
try:
    service = conectar_google_drive()
    
    if service:
        with st.spinner("📥 Carregando dados do Google Drive..."):
            file_stream = baixar_arquivo_drive(service, FILE_ID)
            
            if file_stream:
                df = processar_dados_excel(file_stream)
                
                if df is not None and not df.empty:
                    
                    # --- Seção de Busca e Filtros (Layout Horizontal) --- 
                    st.markdown("""
                        <div class=\'horizontal-panel\'>
                            <h3 class=\'section-title-compact\'>🔍 Sistema de Busca e Filtros</h3>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Busca Global
                    col_busca, col_info_busca = st.columns([4, 1])
                    
                    with col_busca:
                        busca_global = st.text_input(
                            "🔍 Busca Global",
                            st.session_state.get("busca_global", ""), # Mantém o valor da busca
                            placeholder="Digite qualquer termo para buscar em todas as colunas...",
                            help="🎯 A busca é realizada em todas as colunas simultaneamente",
                            key="input_busca_global"
                        )
                        st.session_state["busca_global"] = busca_global # Salva o valor da busca
                    
                    with col_info_busca:
                        st.markdown("""
                            <div class=\'tip-compact\' style=\'margin-top: 25px;\'>
                                <strong>💡 Dica:</strong> Use termos específicos
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Aplicar busca global primeiro
                    df_busca = aplicar_busca_global(df, busca_global)
                    
                    # Filtros específicos em linha
                    st.markdown("#### 🎛️ Filtros Avançados")
                    col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns(4)
                    
                    with col_filtro1:
                        if "Base SGEE.Setor Responsavel" in df_busca.columns:
                            setores_list = ["🌐 Todos"] + sorted(df_busca["Base SGEE.Setor Responsavel"].dropna().unique().tolist())
                            filtro_setor = st.selectbox("🏢 Setor", setores_list, key="filtro_setor")
                        else:
                            filtro_setor = "🌐 Todos"
                    
                    with col_filtro2:
                        if "Responsavel" in df_busca.columns:
                            resp_list = ["🌐 Todos"] + sorted(df_busca["Responsavel"].dropna().unique().tolist())
                            filtro_resp = st.selectbox("👤 Responsável", resp_list, key="filtro_resp")
                        else:
                            filtro_resp = "🌐 Todos"
                    
                    with col_filtro3:
                        if "Base SGEE.Status Contrato" in df_busca.columns:
                            status_list = ["🌐 Todos"] + sorted(df_busca["Base SGEE.Status Contrato"].dropna().unique().tolist())
                            filtro_status = st.selectbox("📋 Status", status_list, key="filtro_status")
                        else:
                            filtro_status = "🌐 Todos"
                    
                    with col_filtro4:
                        if "Base SGEE.Empresa Contratada" in df_busca.columns:
                            empresa_list = ["🌐 Todos"] + sorted(df_busca["Base SGEE.Empresa Contratada"].dropna().unique().tolist())
                            filtro_empresa = st.selectbox("🏢 Empresa", empresa_list, key="filtro_empresa")
                        else:
                            filtro_empresa = "🌐 Todos"
                    
                    # Botão Limpar todos os filtros
                    if st.button("🧹 Limpar todos os filtros", use_container_width=True):
                        st.session_state["busca_global"] = ""
                        st.session_state["filtro_setor"] = "🌐 Todos"
                        st.session_state["filtro_resp"] = "🌐 Todos"
                        st.session_state["filtro_status"] = "🌐 Todos"
                        st.session_state["filtro_empresa"] = "🌐 Todos"
                        st.rerun()

                    # Aplicar filtros específicos
                    df_filtrado = df_busca.copy()
                    
                    if filtro_setor != "🌐 Todos" and "Base SGEE.Setor Responsavel" in df_filtrado.columns:
                        df_filtrado = df_filtrado[df_filtrado["Base SGEE.Setor Responsavel"] == filtro_setor]
                    
                    if filtro_resp != "🌐 Todos" and "Responsavel" in df_filtrado.columns:
                        df_filtrado = df_filtrado[df_filtrado["Responsavel"] == filtro_resp]
                    
                    if filtro_status != "🌐 Todos" and "Base SGEE.Status Contrato" in df_filtrado.columns:
                        df_filtrado = df_filtrado[df_filtrado["Base SGEE.Status Contrato"] == filtro_status]
                    
                    if filtro_empresa != "🌐 Todos" and "Base SGEE.Empresa Contratada" in df_filtrado.columns:
                        df_filtrado = df_filtrado[df_filtrado["Base SGEE.Empresa Contratada"] == filtro_empresa]
                    
                    # --- Indicadores Principais (Layout Horizontal) ---
                    st.markdown("""
                        <div class=\'horizontal-panel\'>
                            <h3 class=\'section-title-compact\'>📈 Indicadores Principais</h3>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    
                    with col1:
                        st.metric("📊 Total Contratos", f"{len(df_filtrado):,}")
                    
                    with col2:
                        if "Base SGEE.Status Contrato" in df_filtrado.columns:
                            em_andamento = df_filtrado[df_filtrado["Base SGEE.Status Contrato"].str.contains("andamento", case=False, na=False)].shape[0]
                            st.metric("🔄 Em Andamento", f"{em_andamento:,}")
                        else:
                            st.metric("🔄 Em Andamento", "N/A")
                    
                    with col3:
                        if "Responsavel" in df_filtrado.columns:
                            responsaveis = df_filtrado["Responsavel"].nunique()
                            st.metric("👥 Responsáveis", f"{responsaveis:,}")
                        else:
                            st.metric("👥 Responsáveis", "N/A")
                    
                    with col4:
                        if "Base SGEE.Setor Responsavel" in df_filtrado.columns:
                            setores = df_filtrado["Base SGEE.Setor Responsavel"].nunique()
                            st.metric("🏢 Setores", f"{setores:,}")
                        else:
                            st.metric("🏢 Setores", "N/A")
                    
                    with col5:
                        if "Base SGEE.Valor Contrato" in df_filtrado.columns:
                            valor_total = df_filtrado["Base SGEE.Valor Contrato"].sum()
                            st.metric("💲 Valor Total", f"R$ {valor_total:,.2f}")
                        else:
                            st.metric("💲 Valor Total", "N/A")
                    
                    with col6:
                        if "Base SGEE.Total Medido Acumulado" in df_filtrado.columns and "Base SGEE.Valor Contrato" in df_filtrado.columns:
                            total_medido = df_filtrado["Base SGEE.Total Medido Acumulado"].sum()
                            valor_contrato_total = df_filtrado["Base SGEE.Valor Contrato"].sum()
                            if valor_contrato_total > 0:
                                perc_execucao = (total_medido / valor_contrato_total) * 100
                                st.metric("✅ % Execução", f"{perc_execucao:.2f}%")
                            else:
                                st.metric("✅ % Execução", "0.00%")
                        else:
                            st.metric("✅ % Execução", "N/A")

                    col7, col8, col9 = st.columns(3)

                    with col7:
                        if "Base SGEE.Saldo Contratual" in df_filtrado.columns:
                            saldo_contratual = df_filtrado["Base SGEE.Saldo Contratual"].sum()
                            st.metric("💰 Saldo Contratual", f"R$ {saldo_contratual:,.2f}")
                        else:
                            st.metric("💰 Saldo Contratual", "N/A")

                    with col8:
                        if "Base SGEE.Valor Aditivos" in df_filtrado.columns and "Base SGEE.Valor Contrato" in df_filtrado.columns:
                            valor_aditivos = df_filtrado["Base SGEE.Valor Aditivos"].sum()
                            valor_contrato_original = df_filtrado["Base SGEE.Valor Contrato"].sum() - valor_aditivos # Assumindo que Valor Contrato já inclui aditivos
                            if valor_contrato_original > 0:
                                taxa_aditivos = (valor_aditivos / valor_contrato_original) * 100
                                st.metric("➕ Taxa Aditivos", f"{taxa_aditivos:.2f}%")
                            else:
                                st.metric("➕ Taxa Aditivos", "0.00%")
                        else:
                            st.metric("➕ Taxa Aditivos", "N/A")

                    with col9:
                        if "Base SGEE.Prazo Contratual" in df_filtrado.columns:
                            prazo_medio = df_filtrado["Base SGEE.Prazo Contratual"].mean()
                            st.metric("⏳ Prazo Médio (dias)", f"{prazo_medio:.0f}")
                        else:
                            st.metric("⏳ Prazo Médio (dias)", "N/A")

                    # Dashboard de gráficos (Layout Horizontal)
                    if not df_filtrado.empty:
                        st.markdown("""
                            <div class=\'horizontal-panel\'>
                                <h3 class=\'section-title-compact\'>📊 Dashboard de Análises</h3>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        graficos = criar_graficos_dashboard(df_filtrado)
                        
                        # Layout dos gráficos em linha
                        if graficos:
                            col_graf1, col_graf2, col_graf3 = st.columns(3)
                            
                            if "setor" in graficos:
                                with col_graf1:
                                    st.markdown("<div class=\'chart-horizontal\'>", unsafe_allow_html=True)
                                    st.plotly_chart(graficos["setor"], use_container_width=True)
                                    st.markdown("</div>", unsafe_allow_html=True)
                            
                            if "status" in graficos:
                                with col_graf2:
                                    st.markdown("<div class=\'chart-horizontal\'>", unsafe_allow_html=True)
                                    st.plotly_chart(graficos["status"], use_container_width=True)
                                    st.markdown("</div>", unsafe_allow_html=True)
                            
                            if "empresas" in graficos:
                                with col_graf3:
                                    st.markdown("<div class=\'chart-horizontal\'>", unsafe_allow_html=True)
                                    st.plotly_chart(graficos["empresas"], use_container_width=True)
                                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Informações sobre filtros
                    col_info_final, col_download = st.columns([4, 1])
                    
                    with col_info_final:
                        if busca_global:
                            st.info(f"🔍 Termo de busca ativo: **\'{busca_global}\'** | Registros encontrados: **{len(df_filtrado):,}**")
                        else:
                            st.info(f"✅ Exibindo todos os registros: **{len(df_filtrado):,}**")
                    
                    with col_download:
                        if not df_filtrado.empty:
                            csv = df_filtrado.to_csv(index=False).encode("utf-8")
                            st.download_button(
                                label="📥 Exportar CSV",
                                data=csv,
                                file_name=f"sgee_obras_{pd.Timestamp.now().strftime(\"%Y%m%d_%H%M\")}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                    
                    # Tabela de dados otimizada
                    st.markdown("""
                        <div class=\'horizontal-panel\'>
                            <h3 class=\'section-title-compact\'>📋 Dados Detalhados</h3>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if not df_filtrado.empty:
                        st.markdown("""
                            <div class=\'tip-compact\'>
                                <strong>💡 Navegação:</strong> Use os filtros da tabela, redimensione colunas arrastando as bordas, e use Ctrl+Click para seleção múltipla
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Carregar configuração de colunas
                        config_colunas = carregar_configuracao_colunas()
                        
                        # Filtrar apenas colunas visíveis
                        colunas_visiveis = [col for col in df_filtrado.columns if config_colunas.get(col, {}).get("visible", True)]
                        df_exibir = df_filtrado[colunas_visiveis].copy()
                        
                        # Configurar AgGrid com larguras otimizadas
                        gb = GridOptionsBuilder.from_dataframe(df_exibir)
                        
                        # Configuração padrão das colunas
                        gb.configure_default_column(
                            filterable=True,
                            sortable=True,
                            resizable=True,
                            editable=False,
                            wrapText=True,
                            autoHeight=True,
                            minWidth=80,
                            maxWidth=600
                        )
                        
                        # Aplicar configurações específicas das colunas
                        for col_name, config in config_colunas.items():
                            if col_name in df_exibir.columns and config.get("visible", True):
                                col_config = {k: v for k, v in config.items() if k != "visible"}
                                gb.configure_column(col_name, **col_config)
                        
                        # Configurar paginação
                        gb.configure_pagination(
                            paginationAutoPageSize=False,
                            paginationPageSize=30
                        )
                        
                        # Configurar seleção
                        gb.configure_selection(
                            selection_mode=\'multiple\',
                            use_checkbox=True
                        )
                        
                        # Configurar sidebar
                        gb.configure_side_bar()
                        
                        # Configurações adicionais do grid
                        gb.configure_grid_options(
                            enableRangeSelection=True,
                            enableCellTextSelection=True,
                            suppressMenuHide=True,
                            suppressColumnVirtualisation=False
                        )
                        
                        grid_options = gb.build()
                        
                        st.markdown("<div class=\'data-table-optimized\'>", unsafe_allow_html=True)
                        AgGrid(
                            df_exibir,
                            gridOptions=grid_options,
                            update_mode=GridUpdateMode.MODEL_CHANGED,
                            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                            fit_columns_on_grid_load=False,
                            theme=\'streamlit\',
                            height=500,
                            allow_unsafe_jscode=True,
                            enable_enterprise_modules=False
                        )
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ Nenhum registro encontrado com os filtros aplicados.")
                    
                    # Configuração de colunas (se ativada, exibida no final para não atrapalhar o fluxo)
                    if st.session_state.get("mostrar_config", False):
                        st.markdown("""
                            <div class=\'horizontal-panel\'>
                                <h3 class=\'section-title-compact\'>⚙️ Configuração de Colunas</h3>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        config_atual = carregar_configuracao_colunas()
                        
                        col_config1, col_config2, col_config3 = st.columns(3)
                        
                        # Criar uma lista de todas as colunas possíveis para exibição
                        todas_colunas_possiveis = sorted(list(set(df.columns.tolist() + list(get_configuracao_colunas_default().keys()))))

                        # Dividir as colunas em 3 para exibir em 3 colunas no Streamlit
                        part1 = todas_colunas_possiveis[:len(todas_colunas_possiveis)//3]
                        part2 = todas_colunas_possiveis[len(todas_colunas_possiveis)//3:2*len(todas_colunas_possiveis)//3]
                        part3 = todas_colunas_possiveis[2*len(todas_colunas_possiveis)//3:]

                        with col_config1:
                            for col in part1:
                                if col not in config_atual: # Adiciona colunas novas com default visible=True
                                    config_atual[col] = {"width": 150, "visible": True}
                                config_atual[col]["visible"] = st.checkbox(
                                    col.replace("Base SGEE.", "").replace("_", " "),
                                    value=config_atual[col]["visible"],
                                    key=f"vis_{col}"
                                )
                        
                        with col_config2:
                            for col in part2:
                                if col not in config_atual:
                                    config_atual[col] = {"width": 150, "visible": True}
                                config_atual[col]["visible"] = st.checkbox(
                                    col.replace("Base SGEE.", "").replace("_", " "),
                                    value=config_atual[col]["visible"],
                                    key=f"vis_{col}"
                                )
                        
                        with col_config3:
                            for col in part3:
                                if col not in config_atual:
                                    config_atual[col] = {"width": 150, "visible": True}
                                config_atual[col]["visible"] = st.checkbox(
                                    col.replace("Base SGEE.", "").replace("_", " "),
                                    value=config_atual[col]["visible"],
                                    key=f"vis_{col}"
                                )
                        
                        col_save, col_reset = st.columns(2)
                        with col_save:
                            if st.button("💾 Salvar Configuração", use_container_width=True):
                                salvar_configuracao_colunas(config_atual)
                                st.success("✅ Configuração salva!")
                        
                        with col_reset:
                            if st.button("🔄 Restaurar Padrão", use_container_width=True):
                                st.session_state["config_colunas"] = get_configuracao_colunas_default()
                                st.success("✅ Configuração restaurada!")
                                st.rerun()
                        
                        st.markdown("---")

                else:
                    st.warning("⚠️ Nenhum dado encontrado no arquivo")
            else:
                st.error("❌ Não foi possível baixar o arquivo do Google Drive")
    else:
        st.error("❌ Não foi possível conectar ao Google Drive")

except Exception as e:
    st.error(f"❌ Erro geral: {e}")

# Footer compacto
st.markdown("""
    <div class=\'footer-compact\'>
        <p class=\'footer-text\'><strong>🏗️ SGEE+PO</strong> - Sistema de Gestão de Empreendimentos e Obras | Versão 3.0 Otimizada</p>
    </div>
    """, unsafe_allow_html=True)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap' );
    
    /* Reset e estilos gerais */
    * {
        font-family: 'Inter', sans-serif;
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
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 3px;
        height: 20px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 2px;
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
    
    .stMetric [data-testid='metric-container'] {
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
    </style>
    """, unsafe_allow_html=True)

# Função para conectar ao Google Drive
@st.cache_resource
def conectar_google_drive():
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
    try:
        df = pd.read_excel(file_stream, engine="openpyxl")
        df = df.dropna(how="all")
        df.columns = df.columns.str.strip()
        
        # Garantir que colunas numéricas essenciais existam e sejam numéricas
        numeric_cols = ['Valor Contrato', 'Valor Aditivos', '% Aditivo', 'Total Medido Acumulado', 'Saldo Contratual', 'Prazo Contratual']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                # Se a coluna não existir, crie-a com zeros para evitar erros posteriores
                df[col] = 0

        df_original_size = len(df)
        
        # Normalização de dados para melhor detecção de duplicatas
        df_normalizado = df.copy()
        for col in df_normalizado.select_dtypes(include=["object"]).columns:
            df_normalizado[col] = df_normalizado[col].astype(str).str.strip().str.lower()
        
        duplicatas_mask = df_normalizado.duplicated(keep="first")
        df_limpo = df[~duplicatas_mask].reset_index(drop=True)
        
        duplicatas_encontradas = duplicatas_mask.sum()
        if duplicatas_encontradas > 0:
            st.success(f"🧹 **Limpeza de Dados:** {duplicatas_encontradas:,} duplicatas removidas.")
        else:
            st.success("✅ Dados carregados sem duplicatas.")
            
        return df_limpo
        
    except Exception as e:
        st.error(f"❌ Erro ao processar Excel: {e}")
        return None

# Função de busca global
def aplicar_busca_global(df, termo_busca):
    if not termo_busca or not termo_busca.strip():
        return df
    
    termo_busca = str(termo_busca).lower().strip()
    
    # Aplica a busca em todas as colunas convertidas para string
    mask = df.apply(lambda row: any(termo_busca in str(val).lower() for val in row), axis=1)
    return df[mask]

# Função para configurações de colunas
def get_configuracao_colunas_default():
    return {
        "Num CNT": {"width": 120, "visible": True, "pinned": "left"},
        "Objeto Cnt": {"width": 400, "visible": True},
        "Nome Empreendimento": {"width": 350, "visible": True},
        "Escopo": {"width": 500, "visible": True},
        "Empresa Contratada": {"width": 250, "visible": True},
        "Setor Responsavel": {"width": 150, "visible": True},
        "Status Contrato": {"width": 130, "visible": True},
        "Valor Contrato": {"width": 140, "visible": True, "type": "numericColumn"},
        "Total Medido Acumulado": {"width": 160, "visible": True, "type": "numericColumn"},
        "Saldo Contratual": {"width": 140, "visible": True, "type": "numericColumn"},
        "Data Inicio Cnt": {"width": 120, "visible": True, "type": "dateColumn"},
        "Data Fim Cnt Com Aditivos": {"width": 120, "visible": True, "type": "dateColumn"},
        "Responsavel": {"width": 150, "visible": True},
        "Ano Finalização Contrato": {"width": 120, "visible": False},
        "Total Contrato": {"width": 140, "visible": False, "type": "numericColumn"},
        "Valor Aditivos": {"width": 140, "visible": True, "type": "numericColumn"},
        "Prazo Contratual": {"width": 120, "visible": True, "type": "numericColumn"}
    }

# Função para salvar/carregar configurações de colunas
def carregar_configuracao_colunas():
    if "config_colunas" not in st.session_state:
        st.session_state["config_colunas"] = get_configuracao_colunas_default()
    return st.session_state["config_colunas"]

def salvar_configuracao_colunas(config):
    st.session_state["config_colunas"] = config

# Função para criar gráficos
def criar_graficos_dashboard(df):
    graficos = {}
    cores = ["#667eea", "#764ba2", "#f093fb", "#f5576c", "#4facfe", "#00f2fe"]
    
    # Gráfico 1: Distribuição por Setor
    if "Setor Responsavel" in df.columns:
        setor_counts = df["Setor Responsavel"].value_counts().head(8)
        if not setor_counts.empty:
            fig1 = px.pie(values=setor_counts.values, names=setor_counts.index, title="🏢 Distribuição por Setor", color_discrete_sequence=cores, hole=0.5)
            fig1.update_traces(textposition="inside", textinfo="percent+label", textfont_size=11)
            fig1.update_layout(showlegend=True, font=dict(family="Inter"), title_x=0.5, height=350)
            graficos["setor"] = fig1
    
    # Gráfico 2: Status dos Contratos
    if "Status Contrato" in df.columns:
        status_counts = df["Status Contrato"].value_counts()
        if not status_counts.empty:
            fig2 = px.bar(x=status_counts.values, y=status_counts.index, orientation="h", title="📋 Status dos Contratos", labels={"x": "Quantidade", "y": "Status"}, color=status_counts.values, color_continuous_scale="Viridis")
            fig2.update_layout(font=dict(family="Inter"), title_x=0.5, yaxis={"categoryorder": "total ascending"}, height=350)
            graficos["status"] = fig2
    
    # Gráfico 3: Top 10 Empresas Contratadas
    if "Empresa Contratada" in df.columns:
        empresa_counts = df["Empresa Contratada"].value_counts().head(10)
        if not empresa_counts.empty:
            fig3 = px.bar(x=empresa_counts.index, y=empresa_counts.values, title="🏆 Top 10 Empresas", labels={"x": "Empresa", "y": "Nº de Contratos"}, color=empresa_counts.values, color_continuous_scale="Blues")
            fig3.update_layout(font=dict(family="Inter"), title_x=0.5, xaxis={"tickangle": 45}, height=350)
            graficos["empresas"] = fig3
            
    return graficos

# --- Início da Interface ---

# Header
st.markdown("""
    <div class='compact-header'>
        <h1 class='compact-title'>🏗️ SGEE+PO - Sistema de Gestão de Empreendimentos e Obras</h1>
        <p class='compact-subtitle'>Dashboard Inteligente para Análise e Monitoramento de Projetos</p>
    </div>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("<div style='text-align: center; padding: 20px; background: rgba(255,255,255,0.15); border-radius: 15px; margin-bottom: 20px; backdrop-filter: blur(10px);'><h3 style='color: white; font-weight: 600;'>⚙️ Painel de Controle</h3></div>", unsafe_allow_html=True)
    FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
    st.markdown("<div class='info-card-compact'><h4>📂 Status da Conexão</h4><p style='color: #28a745; font-weight: 500;'>✅ Conectado ao Google Drive</p></div>", unsafe_allow_html=True)
    
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    if st.button("⚙️ Configurar Colunas da Tabela", use_container_width=True):
        st.session_state["mostrar_config"] = not st.session_state.get("mostrar_config", False)

# Conectar e processar dados
try:
    service = conectar_google_drive()
    if service:
        with st.spinner("📥 Carregando e processando dados..."):
            file_stream = baixar_arquivo_drive(service, FILE_ID)
            if file_stream:
                df = processar_dados_excel(file_stream)
                
                if df is not None and not df.empty:
                    # --- Seção de Busca e Filtros ---
                    st.markdown("<div class='horizontal-panel'><h3 class='section-title-compact'>🔍 Sistema de Busca e Filtros</h3></div>", unsafe_allow_html=True)
                    
                    busca_global = st.text_input("🔍 Busca Global", st.session_state.get("busca_global", ""), placeholder="Digite para buscar em todas as colunas...")
                    st.session_state["busca_global"] = busca_global
                    
                    df_busca = aplicar_busca_global(df, busca_global)
                    
                    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
                    
                    with col_filtro1:
                        setores_list = ["🌐 Todos"] + sorted(df_busca["Setor Responsavel"].dropna().unique().tolist())
                        filtro_setor = st.selectbox("🏢 Setor", setores_list, key="filtro_setor")
                    
                    with col_filtro2:
                        resp_list = ["🌐 Todos"] + sorted(df_busca["Responsavel"].dropna().unique().tolist())
                        filtro_resp = st.selectbox("👤 Responsável", resp_list, key="filtro_resp")
                    
                    with col_filtro3:
                        status_list = ["🌐 Todos"] + sorted(df_busca["Status Contrato"].dropna().unique().tolist())
                        filtro_status = st.selectbox("📋 Status", status_list, key="filtro_status")

                    # Aplicar filtros
                    df_filtrado = df_busca.copy()
                    if filtro_setor != "🌐 Todos": df_filtrado = df_filtrado[df_filtrado["Setor Responsavel"] == filtro_setor]
                    if filtro_resp != "🌐 Todos": df_filtrado = df_filtrado[df_filtrado["Responsavel"] == filtro_resp]
                    if filtro_status != "🌐 Todos": df_filtrado = df_filtrado[df_filtrado["Status Contrato"] == filtro_status]
                    
                    # --- Indicadores Principais ---
                    st.markdown("<div class='horizontal-panel'><h3 class='section-title-compact'>📈 Indicadores Principais</h3></div>", unsafe_allow_html=True)
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1: st.metric("📊 Total Contratos", f"{len(df_filtrado):,}")
                    with col2: st.metric("👥 Responsáveis", f"{df_filtrado['Responsavel'].nunique():,}")
                    with col3: st.metric("🏢 Setores", f"{df_filtrado['Setor Responsavel'].nunique():,}")
                    with col4: st.metric("💲 Valor Total", f"R$ {df_filtrado['Valor Contrato'].sum():,.2f}")
                    
                    total_medido = df_filtrado["Total Medido Acumulado"].sum()
                    valor_contrato_total = df_filtrado["Valor Contrato"].sum()
                    perc_execucao = (total_medido / valor_contrato_total * 100) if valor_contrato_total > 0 else 0
                    with col5: st.metric("✅ % Execução", f"{perc_execucao:.2f}%")

                    # --- NOVOS INDICADORES ---
                    col6, col7, col8 = st.columns(3)
                    with col6:
                        saldo_contratual = df_filtrado["Saldo Contratual"].sum()
                        st.metric("💰 Saldo Contratual", f"R$ {saldo_contratual:,.2f}")

                    with col7:
                        # Cálculo da Taxa de Aditivos com a regra de negócio
                        df_aditivo_valido = df_filtrado[df_filtrado['% Aditivo'] <= 0.50]
                        soma_aditivos = df_aditivo_valido['Valor Aditivos'].sum()
                        soma_contrato_base = df_aditivo_valido['Valor Contrato'].sum() - soma_aditivos
                        taxa_aditivos = (soma_aditivos / soma_contrato_base * 100) if soma_contrato_base > 0 else 0
                        st.metric("➕ Taxa Aditivos (Global)", f"{taxa_aditivos:.2f}%")

                    with col8:
                        prazo_medio = df_filtrado["Prazo Contratual"][df_filtrado["Prazo Contratual"] > 0].mean()
                        st.metric("⏳ Prazo Médio (dias)", f"{prazo_medio:.0f}" if pd.notna(prazo_medio) else "N/A")

                    # --- Dashboard de Gráficos ---
                    if not df_filtrado.empty:
                        st.markdown("<div class='horizontal-panel'><h3 class='section-title-compact'>📊 Dashboard de Análises</h3></div>", unsafe_allow_html=True)
                        graficos = criar_graficos_dashboard(df_filtrado)
                        if graficos:
                            col_graf1, col_graf2, col_graf3 = st.columns(3)
                            if "setor" in graficos:
                                with col_graf1:
                                    st.markdown("<div class='chart-horizontal'>", unsafe_allow_html=True)
                                    st.plotly_chart(graficos["setor"], use_container_width=True)
                                    st.markdown("</div>", unsafe_allow_html=True)
                            if "status" in graficos:
                                with col_graf2:
                                    st.markdown("<div class='chart-horizontal'>", unsafe_allow_html=True)
                                    st.plotly_chart(graficos["status"], use_container_width=True)
                                    st.markdown("</div>", unsafe_allow_html=True)
                            if "empresas" in graficos:
                                with col_graf3:
                                    st.markdown("<div class='chart-horizontal'>", unsafe_allow_html=True)
                                    st.plotly_chart(graficos["empresas"], use_container_width=True)
                                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # --- Tabela de Dados ---
                    st.markdown("<div class='horizontal-panel'><h3 class='section-title-compact'>📋 Dados Detalhados</h3></div>", unsafe_allow_html=True)
                    if not df_filtrado.empty:
                        st.markdown("<div class='tip-compact'><strong>💡 Navegação:</strong> Use a barra lateral da tabela para mostrar/ocultar colunas, filtre e ordene clicando nos cabeçalhos.</div>", unsafe_allow_html=True)
                        
                        config_colunas = carregar_configuracao_colunas()
                        colunas_visiveis = [col for col, conf in config_colunas.items() if conf.get("visible", True) and col in df_filtrado.columns]
                        df_exibir = df_filtrado[colunas_visiveis]
                        
                        gb = GridOptionsBuilder.from_dataframe(df_exibir)
                        gb.configure_default_column(filterable=True, sortable=True, resizable=True, wrapText=True, autoHeight=True)
                        
                        for col_name, config in config_colunas.items():
                            if col_name in df_exibir.columns:
                                gb.configure_column(col_name, **{k: v for k, v in config.items() if k != "visible"})
                        
                        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
                        gb.configure_selection(selection_mode='multiple', use_checkbox=True)
                        gb.configure_side_bar() # Habilita a barra lateral de colunas
                        
                        grid_options = gb.build()
                        
                        st.markdown("<div class='data-table-optimized'>", unsafe_allow_html=True)
                        AgGrid(df_exibir, gridOptions=grid_options, height=500, allow_unsafe_jscode=True, enable_enterprise_modules=False, theme='streamlit')
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ Nenhum registro encontrado com os filtros aplicados.")
                    
                    # --- Configuração de Colunas (Opcional) ---
                    if st.session_state.get("mostrar_config", False):
                        st.markdown("<div class='horizontal-panel'><h3 class='section-title-compact'>⚙️ Configuração de Visibilidade das Colunas</h3></div>", unsafe_allow_html=True)
                        
                        config_atual = carregar_configuracao_colunas()
                        # Adiciona colunas novas que possam ter surgido no arquivo de dados
                        for col in df.columns:
                            if col not in config_atual:
                                config_atual[col] = {"width": 150, "visible": True}

                        todas_colunas = sorted(config_atual.keys())
                        num_cols = 3
                        cols_per_section = (len(todas_colunas) + num_cols - 1) // num_cols
                        
                        col_config_list = st.columns(num_cols)
                        for i, col_name in enumerate(todas_colunas):
                            col_idx = i // cols_per_section
                            with col_config_list[col_idx]:
                                config_atual[col_name]["visible"] = st.checkbox(col_name, value=config_atual[col_name].get("visible", True), key=f"vis_{col_name}")
                        
                        col_save, col_reset = st.columns(2)
                        if col_save.button("💾 Salvar Configuração", use_container_width=True):
                            salvar_configuracao_colunas(config_atual)
                            st.success("✅ Configuração salva! A tabela será atualizada.")
                            st.rerun()
                        
                        if col_reset.button("🔄 Restaurar Padrão", use_container_width=True):
                            st.session_state["config_colunas"] = get_configuracao_colunas_default()
                            st.success("✅ Configuração restaurada! A tabela será atualizada.")
                            st.rerun()

                else:
                    st.warning("⚠️ Nenhum dado encontrado ou o arquivo está vazio.")
            else:
                st.error("❌ Falha ao baixar o arquivo do Google Drive.")
    else:
        st.error("❌ Falha na conexão com o Google Drive.")

except Exception as e:
    st.error(f"❌ Ocorreu um erro inesperado na aplicação: {e}")

# Footer
st.markdown("""
    <div class='footer-compact'>
        <p class='footer-text'><strong>🏗️ SGEE+PO</strong> - Sistema de Gestão de Empreendimentos e Obras | Versão 3.0 Otimizada</p>
    </div>
    """, unsafe_allow_html=True)

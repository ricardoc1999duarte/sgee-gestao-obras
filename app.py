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
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="SGEE+PO - BI Avançado",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0.5rem;
    }
    
    .alert-critical {
        background: linear-gradient(135deg, #ff6b6b, #ee5a6f);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 8px 25px rgba(255, 107, 107, 0.3);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #ffd93d, #f6b93b);
        color: #333;
        padding: 15px;
        border-radius: 12px;
        margin: 10px 0;
        box-shadow: 0 6px 20px rgba(255, 217, 61, 0.3);
    }
    
    .alert-info {
        background: linear-gradient(135deg, #6dd5ed, #2193b0);
        color: white;
        padding: 15px;
        border-radius: 12px;
        margin: 10px 0;
        box-shadow: 0 6px 20px rgba(109, 213, 237, 0.3);
    }
    
    .kpi-card {
        background: linear-gradient(145deg, #ffffff, #f0f0f0);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.15);
    }
    
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .kpi-label {
        font-size: 0.9rem;
        color: #666;
        font-weight: 500;
    }
    
    .section-header {
        background: rgba(255,255,255,0.95);
        padding: 15px 20px;
        border-radius: 12px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    .section-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #333;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Funções de conexão (mantidas)
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

@st.cache_data(ttl=3600)
def processar_dados_excel(file_stream):
    try:
        df = pd.read_excel(file_stream, sheet_name="SGEEePO", engine="openpyxl")
        df = df.dropna(how="all")
        df.columns = df.columns.str.strip()
        
        # Remover duplicatas
        df_original_size = len(df)
        df_normalizado = df.copy()
        
        for col in df_normalizado.select_dtypes(include=["object"]).columns:
            df_normalizado[col] = df_normalizado[col].astype(str).str.strip().str.lower()
        
        for col in df_normalizado.select_dtypes(include=["float64", "int64"]).columns:
            if df_normalizado[col].dtype == "float64":
                df_normalizado[col] = df_normalizado[col].round(2)
        
        duplicatas_mask = df_normalizado.duplicated(keep="first")
        df_limpo = df[~duplicatas_mask].copy()
        df_limpo = df_limpo.reset_index(drop=True)
        
        linhas_removidas = df_original_size - len(df_limpo)
        if linhas_removidas > 0:
            st.success(f"🧹 {linhas_removidas:,} duplicatas removidas ({(linhas_removidas/df_original_size*100):.1f}%)")
        
        return df_limpo
    except Exception as e:
        st.error(f"❌ Erro ao processar Excel: {e}")
        return None

# NOVA FUNÇÃO: Calcular métricas avançadas
def calcular_metricas_avancadas(df):
    """Calcula KPIs críticos para gestão de obras"""
    metricas = {}
    hoje = pd.Timestamp.now()
    
    # Converter colunas de data
    if 'Data Fim Cnt Com Aditivos' in df.columns:
        df['Data Fim Cnt Com Aditivos'] = pd.to_datetime(df['Data Fim Cnt Com Aditivos'], errors='coerce')
    if 'Data Inicio Cnt' in df.columns:
        df['Data Inicio Cnt'] = pd.to_datetime(df['Data Inicio Cnt'], errors='coerce')
    
    # 1. Contratos Vencidos
    if 'Data Fim Cnt Com Aditivos' in df.columns:
        vencidos = df[df['Data Fim Cnt Com Aditivos'] < hoje]
        metricas['vencidos'] = len(vencidos)
        metricas['df_vencidos'] = vencidos
    else:
        metricas['vencidos'] = 0
        metricas['df_vencidos'] = pd.DataFrame()
    
    # 2. Vencendo em 30/60/90 dias
    if 'Data Fim Cnt Com Aditivos' in df.columns:
        vencendo_30 = df[(df['Data Fim Cnt Com Aditivos'] >= hoje) & 
                         (df['Data Fim Cnt Com Aditivos'] <= hoje + timedelta(days=30))]
        vencendo_60 = df[(df['Data Fim Cnt Com Aditivos'] > hoje + timedelta(days=30)) & 
                         (df['Data Fim Cnt Com Aditivos'] <= hoje + timedelta(days=60))]
        vencendo_90 = df[(df['Data Fim Cnt Com Aditivos'] > hoje + timedelta(days=60)) & 
                         (df['Data Fim Cnt Com Aditivos'] <= hoje + timedelta(days=90))]
        
        metricas['vencendo_30'] = len(vencendo_30)
        metricas['vencendo_60'] = len(vencendo_60)
        metricas['vencendo_90'] = len(vencendo_90)
        metricas['df_vencendo_30'] = vencendo_30
    else:
        metricas['vencendo_30'] = 0
        metricas['vencendo_60'] = 0
        metricas['vencendo_90'] = 0
        metricas['df_vencendo_30'] = pd.DataFrame()
    
    # 3. % Execução
    if 'Total Medido Acumulado' in df.columns and 'Valor Contrato' in df.columns:
        df['Perc_Execucao'] = (df['Total Medido Acumulado'] / df['Valor Contrato'] * 100).fillna(0)
        metricas['exec_media'] = df['Perc_Execucao'].mean()
        
        # Contratos com baixa execução (< 50%)
        baixa_exec = df[df['Perc_Execucao'] < 50]
        metricas['baixa_execucao'] = len(baixa_exec)
    else:
        metricas['exec_media'] = 0
        metricas['baixa_execucao'] = 0
    
    # 4. Saldo Contratual Crítico (< 10%)
    if 'Saldo Contratual' in df.columns and 'Valor Contrato' in df.columns:
        df['Perc_Saldo'] = (df['Saldo Contratual'] / df['Valor Contrato'] * 100).fillna(0)
        saldo_critico = df[df['Perc_Saldo'] < 10]
        metricas['saldo_critico'] = len(saldo_critico)
        metricas['df_saldo_critico'] = saldo_critico
    else:
        metricas['saldo_critico'] = 0
        metricas['df_saldo_critico'] = pd.DataFrame()
    
    # 5. Taxa de Aditivos Alta (> 25%)
    if 'Valor Aditivos' in df.columns and 'Valor Contrato' in df.columns:
        df['Taxa_Aditivos'] = ((df['Valor Aditivos'] / (df['Valor Contrato'] - df['Valor Aditivos'])) * 100).fillna(0)
        aditivos_alto = df[df['Taxa_Aditivos'] > 25]
        metricas['aditivos_alto'] = len(aditivos_alto)
        metricas['taxa_media_aditivos'] = df['Taxa_Aditivos'].mean()
    else:
        metricas['aditivos_alto'] = 0
        metricas['taxa_media_aditivos'] = 0
    
    # 6. Velocidade de Execução (R$/dia)
    if all(col in df.columns for col in ['Total Medido Acumulado', 'Data Inicio Cnt', 'Data Fim Cnt Com Aditivos']):
        df['Dias_Contrato'] = (hoje - df['Data Inicio Cnt']).dt.days
        df['Velocidade_Exec'] = (df['Total Medido Acumulado'] / df['Dias_Contrato']).replace([np.inf, -np.inf], 0).fillna(0)
        metricas['velocidade_media'] = df['Velocidade_Exec'].mean()
    else:
        metricas['velocidade_media'] = 0
    
    # 7. Classificação por Situação
    df['Situacao'] = 'Normal'
    if 'Data Fim Cnt Com Aditivos' in df.columns:
        df.loc[df['Data Fim Cnt Com Aditivos'] < hoje, 'Situacao'] = 'Vencido'
        df.loc[(df['Data Fim Cnt Com Aditivos'] >= hoje) & 
               (df['Data Fim Cnt Com Aditivos'] <= hoje + timedelta(days=30)), 'Situacao'] = 'Crítico'
        df.loc[(df['Data Fim Cnt Com Aditivos'] > hoje + timedelta(days=30)) & 
               (df['Data Fim Cnt Com Aditivos'] <= hoje + timedelta(days=60)), 'Situacao'] = 'Alerta'
    
    metricas['df_processado'] = df
    
    return metricas

# NOVA FUNÇÃO: Criar painel de alertas
def criar_painel_alertas(metricas):
    """Cria cards de alertas críticos"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if metricas['vencidos'] > 0:
            st.markdown(f"""
                <div class='alert-critical'>
                    <h2 style='margin:0; font-size:2.5rem;'>⚠️ {metricas['vencidos']}</h2>
                    <p style='margin:5px 0 0 0; font-size:1.1rem;'>CONTRATOS VENCIDOS</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class='alert-info'>
                    <h2 style='margin:0; font-size:2rem;'>✅ 0</h2>
                    <p style='margin:5px 0 0 0;'>Contratos Vencidos</p>
                </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if metricas['vencendo_30'] > 0:
            st.markdown(f"""
                <div class='alert-warning'>
                    <h2 style='margin:0; font-size:2.5rem;'>⏰ {metricas['vencendo_30']}</h2>
                    <p style='margin:5px 0 0 0; font-size:1.1rem;'>VENCENDO EM 30 DIAS</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class='alert-info'>
                    <h2 style='margin:0; font-size:2rem;'>✅ 0</h2>
                    <p style='margin:5px 0 0 0;'>Vencendo em 30 Dias</p>
                </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if metricas['saldo_critico'] > 0:
            st.markdown(f"""
                <div class='alert-warning'>
                    <h2 style='margin:0; font-size:2.5rem;'>💰 {metricas['saldo_critico']}</h2>
                    <p style='margin:5px 0 0 0; font-size:1.1rem;'>SALDO CRÍTICO (&lt;10%)</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class='alert-info'>
                    <h2 style='margin:0; font-size:2rem;'>✅ 0</h2>
                    <p style='margin:5px 0 0 0;'>Saldo Crítico</p>
                </div>
            """, unsafe_allow_html=True)

# NOVA FUNÇÃO: KPIs avançados
def criar_kpis_avancados(metricas, df):
    """Cria painel de KPIs estratégicos"""
    
    st.markdown("<div class='section-header'><h2 class='section-title'>📊 Indicadores Estratégicos</h2></div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Execução Média",
            f"{metricas['exec_media']:.1f}%",
            help="% média de execução financeira"
        )
    
    with col2:
        if 'Valor Contrato' in df.columns:
            valor_total = df['Valor Contrato'].sum()
            st.metric(
                "Valor em Carteira",
                f"R$ {valor_total/1e6:.1f}M",
                help="Valor total dos contratos"
            )
        else:
            st.metric("Valor em Carteira", "N/A")
    
    with col3:
        st.metric(
            "Velocidade Média",
            f"R$ {metricas['velocidade_media']/1000:.1f}K/dia",
            help="Velocidade média de execução"
        )
    
    with col4:
        st.metric(
            "Taxa de Aditivos",
            f"{metricas['taxa_media_aditivos']:.1f}%",
            delta=f"{metricas['aditivos_alto']} contratos > 25%",
            delta_color="inverse",
            help="Taxa média de aditivos"
        )
    
    with col5:
        criticos = metricas['vencidos'] + metricas['vencendo_30'] + metricas['saldo_critico']
        st.metric(
            "Contratos Críticos",
            criticos,
            delta=f"{(criticos/len(df)*100):.1f}% do total" if len(df) > 0 else "0%",
            delta_color="inverse",
            help="Vencidos + Vencendo30d + Saldo<10%"
        )

# NOVA FUNÇÃO: Gráfico de vencimentos mensais (heatmap)
def criar_heatmap_vencimentos(df):
    """Cria heatmap de vencimentos por mês"""
    if 'Data Fim Cnt Com Aditivos' in df.columns:
        df_copy = df.copy()
        df_copy['Mes_Vencimento'] = pd.to_datetime(df_copy['Data Fim Cnt Com Aditivos'], errors='coerce').dt.to_period('M')
        vencimentos_mes = df_copy['Mes_Vencimento'].value_counts().sort_index()
        
        if not vencimentos_mes.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[str(m) for m in vencimentos_mes.index],
                y=vencimentos_mes.values,
                marker=dict(
                    color=vencimentos_mes.values,
                    colorscale='Reds',
                    showscale=True,
                    colorbar=dict(title="Qtd")
                ),
                hovertemplate='<b>%{x}</b><br>Contratos: %{y}<extra></extra>'
            ))
            
            fig.update_layout(
                title="📅 Distribuição de Vencimentos por Mês",
                xaxis_title="Mês",
                yaxis_title="Quantidade de Contratos",
                height=350,
                showlegend=False
            )
            
            return fig
    return None

# NOVA FUNÇÃO: Top contratos críticos
def exibir_contratos_criticos(metricas):
    """Exibe lista de contratos que precisam atenção imediata"""
    
    st.markdown("<div class='section-header'><h2 class='section-title'>🚨 Contratos Prioritários</h2></div>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["⚠️ Vencidos", "⏰ Vencendo (30d)", "💰 Saldo Crítico"])
    
    with tab1:
        if not metricas['df_vencidos'].empty:
            df_display = metricas['df_vencidos'][['Num CNT', 'Objeto Cnt', 'Empresa Contratada', 
                                                   'Data Fim Cnt Com Aditivos', 'Valor Contrato', 
                                                   'Saldo Contratual']].head(10)
            st.dataframe(df_display, use_container_width=True, height=300)
        else:
            st.info("✅ Nenhum contrato vencido")
    
    with tab2:
        if not metricas['df_vencendo_30'].empty:
            df_display = metricas['df_vencendo_30'][['Num CNT', 'Objeto Cnt', 'Empresa Contratada', 
                                                      'Data Fim Cnt Com Aditivos', 'Valor Contrato']].head(10)
            st.dataframe(df_display, use_container_width=True, height=300)
        else:
            st.info("✅ Nenhum contrato vencendo nos próximos 30 dias")
    
    with tab3:
        if not metricas['df_saldo_critico'].empty:
            df_display = metricas['df_saldo_critico'][['Num CNT', 'Objeto Cnt', 'Empresa Contratada', 
                                                        'Saldo Contratual', 'Perc_Saldo']].head(10)
            st.dataframe(df_display, use_container_width=True, height=300)
        else:
            st.info("✅ Nenhum contrato com saldo crítico")

# ==================== MAIN APP ====================

st.markdown("""
    <div style='text-align: center; padding: 25px; background: rgba(255,255,255,0.95); border-radius: 20px; margin-bottom: 20px;'>
        <h1 style='font-size: 2.8rem; font-weight: 700; background: linear-gradient(135deg, #667eea, #764ba2); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px;'>
            🏗️ SGEE+PO - Business Intelligence
        </h1>
        <p style='font-size: 1.3rem; color: #666; font-weight: 400;'>
            Sistema Avançado de Gestão e Monitoramento de Obras
        </p>
    </div>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 20px; background: rgba(255,255,255,0.15); 
                    border-radius: 15px; margin-bottom: 20px; backdrop-filter: blur(10px);'>
            <h3 style='color: white; margin-bottom: 10px; font-weight: 600;'>⚙️ Controles</h3>
        </div>
        """, unsafe_allow_html=True)
    
    FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
    
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🎯 Filtros Rápidos")
    
    filtro_situacao = st.multiselect(
        "Situação do Contrato",
        ["Normal", "Alerta", "Crítico", "Vencido"],
        default=["Normal", "Alerta", "Crítico", "Vencido"]
    )

# Processar dados
try:
    service = conectar_google_drive()
    
    if service:
        with st.spinner("📥 Carregando dados..."):
            file_stream = baixar_arquivo_drive(service, FILE_ID)
            
            if file_stream:
                df = processar_dados_excel(file_stream)
                
                if df is not None and not df.empty:
                    
                    # Calcular métricas
                    metricas = calcular_metricas_avancadas(df)
                    df = metricas['df_processado']
                    
                    # Aplicar filtro de situação
                    if filtro_situacao:
                        df = df[df['Situacao'].isin(filtro_situacao)]
                    
                    # PAINEL DE ALERTAS
                    st.markdown("## 🚨 Alertas Críticos")
                    criar_painel_alertas(metricas)
                    
                    st.markdown("---")
                    
                    # KPIs AVANÇADOS
                    criar_kpis_avancados(metricas, df)
                    
                    st.markdown("---")
                    
                    # GRÁFICOS
                    col_g1, col_g2 = st.columns(2)
                    
                    with col_g1:
                        fig_venc = criar_heatmap_vencimentos(df)
                        if fig_venc:
                            st.plotly_chart(fig_venc, use_container_width=True)
                    
                    with col_g2:
                        if 'Situacao' in df.columns:
                            situacao_counts = df['Situacao'].value_counts()
                            fig_sit = px.pie(
                                values=situacao_counts.values,
                                names=situacao_counts.index,
                                title="📊 Distribuição por Situação",
                                color_discrete_map={
                                    'Vencido': '#ff6b6b',
                                    'Crítico': '#ffd93d',
                                    'Alerta': '#6dd5ed',
                                    'Normal': '#51cf66'
                                },
                                hole=0.4
                            )
                            fig_sit.update_traces(textposition='inside', textinfo='percent+label')
                            fig_sit.update_layout(height=350)
                            st.plotly_chart(fig_sit, use_container_width=True)
                    
                    st.markdown("---")
                    
                    # CONTRATOS CRÍTICOS
                    exibir_contratos_criticos(metricas)
                    
                    st.markdown("---")
                    
                    # TABELA COMPLETA
                    st.markdown("<div class='section-header'><h2 class='section-title'>📋 Base Completa de Dados</h2></div>", unsafe_allow_html=True)
                    
                    # Busca global
                    busca = st.text_input("🔍 Buscar", placeholder="Digite para filtrar...")
                    
                    if busca:
                        mask = df.astype(str).apply(lambda x: x.str.contains(busca, case=False, na=False)).any(axis=1)
                        df_exibir = df[mask]
                    else:
                        df_exibir = df
                    
                    st.info(f"📊 Exibindo {len(df_exibir):,} de {len(df):,} contratos")
                    
                    # AgGrid com cores por situação
                    gb = GridOptionsBuilder.from_dataframe(df_exibir)
                    gb.configure_default_column(filterable=True, sortable=True, resizable=True)
                    gb.configure_pagination(paginationPageSize=20)
                    gb.configure_selection(selection_mode='multiple', use_checkbox=True)
                    
                    # Destacar linhas críticas
                    gb.configure_grid_options(
                        rowClassRules={
                            'bg-danger': 'data.Situacao == "Vencido"',
                            'bg-warning': 'data.Situacao == "Crítico"',
                        }
                    )
                    
                    grid_options = gb.build()
                    
                    AgGrid(
                        df_exibir,
                        gridOptions=grid_options,
                        theme='streamlit',
                        height=500,
                        fit_columns_on_grid_load=False
                    )
                    

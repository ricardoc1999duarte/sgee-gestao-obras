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

# CSS customizado (sem alterações)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap' );
    * { font-family: 'Inter', sans-serif; }
    .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 0.5rem; }
    .compact-header { text-align: center; padding: 15px 20px; margin-bottom: 15px; background: rgba(255,255,255,0.1); border-radius: 15px; backdrop-filter: blur(10px); }
    .compact-title { font-size: 2.5rem; font-weight: 700; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 5px; }
    .compact-subtitle { font-size: 1.2rem; color: rgba(255, 255, 255, 0.9); font-weight: 400; margin: 0; }
    .horizontal-panel { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(20px); border-radius: 15px; padding: 20px; margin: 10px 0; box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); transition: all 0.3s ease; color: #333; }
    .section-title-compact { font-size: 1.3rem; font-weight: 600; color: #333; margin-bottom: 15px; position: relative; padding-left: 12px; }
    .section-title-compact::before { content: ''; position: absolute; left: 0; top: 50%; transform: translateY(-50%); width: 3px; height: 20px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 2px; }
    .stMetric { background: linear-gradient(145deg, #f8f9ff, #e8ecff); border-radius: 12px; padding: 15px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.1); border-left: 4px solid #667eea; transition: all 0.3s ease; color: #333; }
    .data-table-optimized { background: white; border-radius: 15px; padding: 20px; box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08); border: 1px solid rgba(255, 255, 255, 0.2); margin-top: 15px; }
    .tip-compact { background: linear-gradient(135deg, #e3f2fd, #bbdefb); border-radius: 10px; padding: 12px 16px; margin: 10px 0; border-left: 3px solid #2196f3; color: #1565c0; font-size: 13px; }
    .tip-compact strong { color: #0d47a1; }
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
        
        essential_cols = {
            'Base SGEE.Valor Contrato': 0, 'Base SGEE.Valor Aditivos': 0, '% Aditivo': 0,
            'Base SGEE.Total Medido Acumulado': 0, 'Base SGEE.Saldo Contratual': 0, 'Base SGEE.Prazo Contratual': 0,
            'Base SGEE.Setor Responsavel': 'N/A', 'Base SGEE.Responsavel': 'N/A',
            'Base SGEE.Status Contrato': 'N/A', 'Base SGEE.Empresa Contratada': 'N/A'
        }

        for col, default_value in essential_cols.items():
            if col not in df.columns:
                df[col] = default_value
            if isinstance(default_value, (int, float)):
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

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
    mask = df.apply(lambda row: any(termo_busca in str(val).lower() for val in row), axis=1)
    return df[mask]

# Função para criar gráficos
def criar_graficos_dashboard(df):
    graficos = {}
    cores = ["#667eea", "#764ba2", "#f093fb", "#f5576c", "#4facfe", "#00f2fe"]
    
    if "Base SGEE.Setor Responsavel" in df.columns:
        setor_counts = df["Base SGEE.Setor Responsavel"].value_counts().head(8)
        if not setor_counts.empty:
            fig1 = px.pie(values=setor_counts.values, names=setor_counts.index, title="🏢 Distribuição por Setor", color_discrete_sequence=cores, hole=0.5)
            fig1.update_traces(textposition="inside", textinfo="percent+label", textfont_size=11)
            fig1.update_layout(showlegend=True, font=dict(family="Inter"), title_x=0.5, height=350)
            graficos["setor"] = fig1
    
    if "Base SGEE.Status Contrato" in df.columns:
        status_counts = df["Base SGEE.Status Contrato"].value_counts()
        if not status_counts.empty:
            fig2 = px.bar(x=status_counts.values, y=status_counts.index, orientation="h", title="📋 Status dos Contratos", labels={"x": "Quantidade", "y": "Status"}, color=status_counts.values, color_continuous_scale="Viridis")
            fig2.update_layout(font=dict(family="Inter"), title_x=0.5, yaxis={"categoryorder": "total ascending"}, height=350)
            graficos["status"] = fig2
    
    if "Base SGEE.Empresa Contratada" in df.columns:
        empresa_counts = df["Base SGEE.Empresa Contratada"].value_counts().head(10)
        if not empresa_counts.empty:
            fig3 = px.bar(x=empresa_counts.index, y=empresa_counts.values, title="🏆 Top 10 Empresas", labels={"x": "Empresa", "y": "Nº de Contratos"}, color=empresa_counts.values, color_continuous_scale="Blues")
            fig3.update_layout(font=dict(family="Inter"), title_x=0.5, xaxis={"tickangle": 45}, height=350)
            graficos["empresas"] = fig3
            
    return graficos

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
                    
                    busca_global = st.text_input("🔍 Busca Global", st.session_state.get("busca_global", ""), placeholder="Digite para buscar em todas as colunas...")
                    st.session_state["busca_global"] = busca_global
                    
                    df_busca = aplicar_busca_global(df, busca_global)
                    
                    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
                    
                    with col_filtro1:
                        setores_list = ["🌐 Todos"] + sorted(df_busca["Base SGEE.Setor Responsavel"].dropna().unique().tolist())
                        filtro_setor = st.selectbox("🏢 Setor", setores_list, key="filtro_setor")
                    
                    with col_filtro2:
                        resp_list = ["🌐 Todos"] + sorted(df_busca["Base SGEE.Responsavel"].dropna().unique().tolist())
                        filtro_resp = st.selectbox("👤 Responsável", resp_list, key="filtro_resp")
                    
                    with col_filtro3:
                        status_list = ["🌐 Todos"] + sorted(df_busca["Base SGEE.Status Contrato"].dropna().unique().tolist())
                        filtro_status = st.selectbox("📋 Status", status_list, key="filtro_status")

                    df_filtrado = df_busca.copy()
                    if filtro_setor != "🌐 Todos": df_filtrado = df_filtrado[df_filtrado["Base SGEE.Setor Responsavel"] == filtro_setor]
                    if filtro_resp != "🌐 Todos": df_filtrado = df_filtrado[df_filtrado["Base SGEE.Responsavel"] == filtro_resp]
                    if filtro_status != "🌐 Todos": df_filtrado = df_filtrado[df_filtrado["Base SGEE.Status Contrato"] == filtro_status]
                    
                    st.markdown("<div class='horizontal-panel'><h3 class='section-title-compact'>📈 Indicadores Principais</h3></div>", unsafe_allow_html=True)
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1: st.metric("📊 Total Contratos", f"{len(df_filtrado):,}")
                    with col2: st.metric("👥 Responsáveis", f"{df_filtrado['Base SGEE.Responsavel'].nunique():,}")
                    with col3: st.metric("🏢 Setores", f"{df_filtrado['Base SGEE.Setor Responsavel'].nunique():,}")
                    with col4: st.metric("💲 Valor Total", f"R$ {df_filtrado['Base SGEE.Valor Contrato'].sum():,.2f}")
                    
                    total_medido = df_filtrado["Base SGEE.Total Medido Acumulado"].sum()
                    valor_contrato_total = df_filtrado["Base SGEE.Valor Contrato"].sum()
                    perc_execucao = (total_medido / valor_contrato_total * 100) if valor_contrato_total > 0 else 0
                    with col5: st.metric("✅ % Execução", f"{perc_execucao:.2f}%")

                    col6, col7, col8 = st.columns(3)
                    with col6:
                        saldo_contratual = df_filtrado["Base SGEE.Saldo Contratual"].sum()
                        st.metric("💰 Saldo Contratual", f"R$ {saldo_contratual:,.2f}")

                    with col7:
                        df_aditivo_valido = df_filtrado[df_filtrado['% Aditivo'] <= 0.50]
                        soma_aditivos = df_aditivo_valido['Base SGEE.Valor Aditivos'].sum()
                        soma_contrato_base = df_aditivo_valido['Base SGEE.Valor Contrato'].sum() - df_aditivo_valido['Base SGEE.Valor Aditivos'].sum()
                        taxa_aditivos = (soma_aditivos / soma_contrato_base * 100) if soma_contrato_base > 0 else 0
                        st.metric("➕ Taxa Aditivos (Global)", f"{taxa_aditivos:.2f}%")

                    with col8:
                        prazo_medio = df_filtrado["Base SGEE.Prazo Contratual"][df_filtrado["Base SGEE.Prazo Contratual"] > 0].mean()
                        st.metric("⏳ Prazo Médio (dias)", f"{prazo_medio:.0f}" if pd.notna(prazo_medio) else "N/A")

                    if not df_filtrado.empty:
                        st.markdown("<div class='horizontal-panel'><h3 class='section-title-compact'>📊 Dashboard de Análises</h3></div>", unsafe_allow_html=True)
                        graficos = criar_graficos_dashboard(df_filtrado)
                        if graficos:
                            col_graf1, col_graf2, col_graf3 = st.columns(3)
                            if "setor" in graficos:
                                with col_graf1: st.plotly_chart(graficos["setor"], use_container_width=True)
                            if "status" in graficos:
                                with col_graf2: st.plotly_chart(graficos["status"], use_container_width=True)
                            if "empresas" in graficos:
                                with col_graf3: st.plotly_chart(graficos["empresas"], use_container_width=True)
                    
                    st.markdown("<div class='horizontal-panel'><h3 class='section-title-compact'>📋 Dados Detalhados</h3></div>", unsafe_allow_html=True)
                    if not df_filtrado.empty:
                        st.markdown("<div class='tip-compact'><strong>💡 Dica:</strong> Clique no ícone de funil  बगल de cada coluna para filtrar os dados diretamente na tabela.</div>", unsafe_allow_html=True)
                        
                        gb = GridOptionsBuilder.from_dataframe(df_filtrado)
                        gb.configure_default_column(
                            filterable=True, # Habilita o filtro em todas as colunas
                            sortable=True, 
                            resizable=True, 
                            wrapText=True, 
                            autoHeight=True
                        )
                        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
                        gb.configure_selection(selection_mode='multiple', use_checkbox=True)
                        
                        grid_options = gb.build()
                        
                        st.markdown("<div class='data-table-optimized'>", unsafe_allow_html=True)
                        AgGrid(
                            df_filtrado, 
                            gridOptions=grid_options, 
                            height=600, 
                            allow_unsafe_jscode=True, 
                            # CORREÇÃO CRÍTICA: Habilita os recursos avançados, incluindo filtros de coluna
                            enable_enterprise_modules=True, 
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

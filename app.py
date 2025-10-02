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

# CSS customizado melhorado
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
    }
    
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border: 1px solid rgba(255,255,255,0.2);
        transition: transform 0.3s ease;
    }
    
    .stMetric:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 35px rgba(0,0,0,0.2);
    }
    
    .metric-card {
        background: linear-gradient(145deg, #ffffff, #f0f2f6);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border-left: 5px solid #667eea;
    }
    
    .search-container {
        background: rgba(255,255,255,0.95);
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
    }
    
    .filter-section {
        background: rgba(255,255,255,0.9);
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    
    .data-table {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    .stSelectbox > div > div {
        background-color: white;
        border-radius: 8px;
    }
    
    .stTextInput > div > div > input {
        background-color: white;
        border-radius: 8px;
        border: 2px solid #e1e5e9;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .chart-container {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    .status-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        text-align: center;
    }
    
    .status-em-andamento {
        background-color: #28a745;
        color: white;
    }
    
    .status-concluido {
        background-color: #007bff;
        color: white;
    }
    
    .status-pausado {
        background-color: #ffc107;
        color: black;
    }
    
    h1, h2, h3 {
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .info-card {
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
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
        # As credenciais devem ser adicionadas nos Secrets do Streamlit
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        st.error(f"Erro ao conectar ao Google Drive: {e}")
        return None

# Função para baixar arquivo do Google Drive
@st.cache_data(ttl=3600)  # Cache por 1 hora
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
        # Lê o arquivo Excel (suporta .xlsm)
        df = pd.read_excel(file_stream, sheet_name='SGEEePO', engine='openpyxl')
        
        # Remove linhas vazias
        df = df.dropna(how='all')
        
        # Renomeia colunas para facilitar o uso
        df.columns = df.columns.str.strip()
        
        # Remove duplicatas baseado em todas as colunas
        df_original_size = len(df)
        df = df.drop_duplicates()
        duplicatas_removidas = df_original_size - len(df)
        
        if duplicatas_removidas > 0:
            st.info(f"🧹 Removidas {duplicatas_removidas} linhas duplicadas dos dados")
        
        return df
    except Exception as e:
        st.error(f"Erro ao processar Excel: {e}")
        return None

# Função melhorada de busca global
def aplicar_busca_global(df, termo_busca):
    """
    Aplica busca global melhorada em todas as colunas do DataFrame
    """
    if not termo_busca.strip():
        return df
    
    # Converte o termo de busca para minúsculas
    termo_busca = termo_busca.lower().strip()
    
    # Cria máscara de busca
    mask = pd.Series([False] * len(df))
    
    # Busca em cada coluna
    for coluna in df.columns:
        try:
            # Converte valores para string e aplica busca case-insensitive
            coluna_str = df[coluna].astype(str).str.lower()
            mask_coluna = coluna_str.str.contains(termo_busca, na=False, regex=False)
            mask = mask | mask_coluna
        except Exception:
            # Se houver erro em alguma coluna, continua com as outras
            continue
    
    return df[mask]

# Função para criar gráficos melhorados
def criar_graficos_dashboard(df):
    """
    Cria gráficos melhorados para o dashboard
    """
    graficos = {}
    
    # Gráfico 1: Distribuição por Setor
    if 'Base SGEE.Setor Responsavel' in df.columns:
        setor_counts = df['Base SGEE.Setor Responsavel'].value_counts().head(10)
        fig1 = px.pie(
            values=setor_counts.values, 
            names=setor_counts.index,
            title="Distribuição por Setor Responsável",
            color_discrete_sequence=px.colors.qualitative.Set3,
            hole=0.4
        )
        fig1.update_traces(textposition='inside', textinfo='percent+label')
        fig1.update_layout(
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5),
            font=dict(size=12),
            title_font_size=16
        )
        graficos['setor'] = fig1
    
    # Gráfico 2: Status dos Contratos
    if 'Base SGEE.Status Contrato' in df.columns:
        status_counts = df['Base SGEE.Status Contrato'].value_counts()
        fig2 = px.bar(
            x=status_counts.values,
            y=status_counts.index,
            orientation='h',
            title="Status dos Contratos",
            labels={'x': 'Quantidade', 'y': 'Status'},
            color=status_counts.values,
            color_continuous_scale='Viridis'
        )
        fig2.update_layout(
            showlegend=False,
            font=dict(size=12),
            title_font_size=16,
            yaxis={'categoryorder': 'total ascending'}
        )
        graficos['status'] = fig2
    
    # Gráfico 3: Valores por Ano
    if 'Base SGEE.Ano Finalização Contrato' in df.columns and 'Base SGEE.Total Contrato' in df.columns:
        df_temp = df.dropna(subset=['Base SGEE.Ano Finalização Contrato', 'Base SGEE.Total Contrato'])
        if not df_temp.empty:
            valores_ano = df_temp.groupby('Base SGEE.Ano Finalização Contrato')['Base SGEE.Total Contrato'].sum().reset_index()
            fig3 = px.line(
                valores_ano,
                x='Base SGEE.Ano Finalização Contrato',
                y='Base SGEE.Total Contrato',
                title="Evolução dos Valores Contratuais por Ano",
                markers=True
            )
            fig3.update_traces(line=dict(width=3), marker=dict(size=8))
            fig3.update_layout(
                font=dict(size=12),
                title_font_size=16,
                xaxis_title="Ano de Finalização",
                yaxis_title="Valor Total (R$)"
            )
            graficos['valores_ano'] = fig3
    
    # Gráfico 4: Top 10 Empresas Contratadas
    if 'Base SGEE.Empresa Contratada' in df.columns:
        empresa_counts = df['Base SGEE.Empresa Contratada'].value_counts().head(10)
        fig4 = px.bar(
            x=empresa_counts.index,
            y=empresa_counts.values,
            title="Top 10 Empresas Contratadas",
            labels={'x': 'Empresa', 'y': 'Número de Contratos'},
            color=empresa_counts.values,
            color_continuous_scale='Blues'
        )
        fig4.update_layout(
            showlegend=False,
            font=dict(size=12),
            title_font_size=16,
            xaxis={'tickangle': 45}
        )
        graficos['empresas'] = fig4
    
    return graficos

# Header principal
st.markdown("""
    <div style='text-align: center; padding: 20px; margin-bottom: 30px;'>
        <h1 style='font-size: 3rem; margin-bottom: 10px;'>🏗️ SGEE+PO</h1>
        <h2 style='font-size: 1.5rem; opacity: 0.9;'>Sistema de Gestão de Empreendimentos e Obras</h2>
        <p style='font-size: 1.1rem; opacity: 0.8;'>Dashboard Inteligente para Análise e Monitoramento</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# Sidebar melhorada
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 20px; background: rgba(255,255,255,0.1); border-radius: 15px; margin-bottom: 20px;'>
            <h2 style='color: white; margin-bottom: 10px;'>⚙️ Configurações</h2>
        </div>
    """, unsafe_allow_html=True)
    
    # ID do arquivo no Google Drive
    FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
    
    st.markdown("""
        <div class='info-card'>
            <h4>📂 Status da Conexão</h4>
            <p>✅ Conectado ao Google Drive</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("""
        <div class='info-card'>
            <h4>📊 Funcionalidades</h4>
            <ul style='margin: 0; padding-left: 20px;'>
                <li>✅ Visualização em tempo real</li>
                <li>✅ Busca global inteligente</li>
                <li>✅ Filtros avançados</li>
                <li>✅ Análise gráfica interativa</li>
                <li>✅ Remoção automática de duplicatas</li>
                <li>✅ Exportação de dados</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

# Conectar ao Google Drive e baixar dados
try:
    service = conectar_google_drive()
    
    if service:
        with st.spinner("📥 Carregando dados do Google Drive..."):
            file_stream = baixar_arquivo_drive(service, FILE_ID)
            
            if file_stream:
                df = processar_dados_excel(file_stream)
                
                if df is not None and not df.empty:
                    st.success("✅ Dados carregados com sucesso!")
                    
                    # Indicadores principais melhorados
                    st.markdown("""
                        <div class='search-container'>
                            <h3 style='color: #333; margin-bottom: 20px; text-shadow: none;'>📈 Indicadores Principais</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("📊 Total de Registros", f"{len(df):,}")
                    
                    with col2:
                        if 'Base SGEE.Status Contrato' in df.columns:
                            em_andamento = df[df['Base SGEE.Status Contrato'].str.contains('andamento', case=False, na=False)].shape[0]
                            st.metric("🔄 Em Andamento", em_andamento)
                        else:
                            st.metric("🔄 Em Andamento", "N/A")
                    
                    with col3:
                        if 'Responsavel' in df.columns:
                            responsaveis = df['Responsavel'].nunique()
                            st.metric("👥 Responsáveis", responsaveis)
                        else:
                            st.metric("👥 Responsáveis", "N/A")
                    
                    with col4:
                        if 'Base SGEE.Setor Responsavel' in df.columns:
                            setores = df['Base SGEE.Setor Responsavel'].nunique()
                            st.metric("🏢 Setores", setores)
                        else:
                            st.metric("🏢 Setores", "N/A")
                    
                    st.markdown("---")
                    
                    # Seção de filtros melhorada
                    st.markdown("""
                        <div class='search-container'>
                            <h3 style='color: #333; margin-bottom: 20px; text-shadow: none;'>🔍 Sistema de Busca e Filtros</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Busca Global Melhorada
                    col_busca_principal, col_info = st.columns([3, 1])
                    
                    with col_busca_principal:
                        busca_global = st.text_input(
                            "🔍 Busca Global Inteligente",
                            "",
                            placeholder="Digite qualquer termo para buscar em todas as colunas (ex: 'SUDECAP', 'andamento', '2024')...",
                            help="A busca é realizada em todas as colunas simultaneamente, ignorando maiúsculas/minúsculas"
                        )
                    
                    with col_info:
                        st.markdown("""
                            <div style='margin-top: 25px;'>
                                <small>💡 <strong>Dica:</strong> Use termos específicos para resultados mais precisos</small>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Aplicar busca global primeiro
                    df_busca = aplicar_busca_global(df, busca_global)
                    
                    # Filtros específicos
                    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
                    
                    with col_filtro1:
                        if 'Base SGEE.Setor Responsavel' in df_busca.columns:
                            setores_list = ['Todos'] + sorted(df_busca['Base SGEE.Setor Responsavel'].dropna().unique().tolist())
                            filtro_setor = st.selectbox("🏢 Filtrar por Setor", setores_list)
                        else:
                            filtro_setor = 'Todos'
                    
                    with col_filtro2:
                        if 'Responsavel' in df_busca.columns:
                            resp_list = ['Todos'] + sorted(df_busca['Responsavel'].dropna().unique().tolist())
                            filtro_resp = st.selectbox("👤 Filtrar por Responsável", resp_list)
                        else:
                            filtro_resp = 'Todos'
                    
                    with col_filtro3:
                        if 'Base SGEE.Status Contrato' in df_busca.columns:
                            status_list = ['Todos'] + sorted(df_busca['Base SGEE.Status Contrato'].dropna().unique().tolist())
                            filtro_status = st.selectbox("📋 Filtrar por Status", status_list)
                        else:
                            filtro_status = 'Todos'
                    
                    # Aplicar filtros específicos
                    df_filtrado = df_busca.copy()
                    
                    if filtro_setor != 'Todos' and 'Base SGEE.Setor Responsavel' in df_filtrado.columns:
                        df_filtrado = df_filtrado[df_filtrado['Base SGEE.Setor Responsavel'] == filtro_setor]
                    
                    if filtro_resp != 'Todos' and 'Responsavel' in df_filtrado.columns:
                        df_filtrado = df_filtrado[df_filtrado['Responsavel'] == filtro_resp]
                    
                    if filtro_status != 'Todos' and 'Base SGEE.Status Contrato' in df_filtrado.columns:
                        df_filtrado = df_filtrado[df_filtrado['Base SGEE.Status Contrato'] == filtro_status]
                    
                    # Informações sobre filtros aplicados
                    col_info1, col_info2, col_download = st.columns([2, 2, 1])
                    
                    with col_info1:
                        st.info(f"📊 Exibindo **{len(df_filtrado):,}** de **{len(df):,}** registros totais")
                    
                    with col_info2:
                        if busca_global:
                            st.info(f"🔍 Busca ativa: **'{busca_global}'**")
                    
                    with col_download:
                        csv = df_filtrado.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Baixar CSV",
                            data=csv,
                            file_name=f"sgee_obras_filtrado_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    # Gráficos melhorados
                    if not df_filtrado.empty:
                        st.markdown("---")
                        st.markdown("""
                            <div class='search-container'>
                                <h3 style='color: #333; margin-bottom: 20px; text-shadow: none;'>📊 Dashboard de Análises</h3>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        graficos = criar_graficos_dashboard(df_filtrado)
                        
                        # Layout dos gráficos
                        if 'setor' in graficos and 'status' in graficos:
                            col_graf1, col_graf2 = st.columns(2)
                            
                            with col_graf1:
                                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                                st.plotly_chart(graficos['setor'], use_container_width=True)
                                st.markdown("</div>", unsafe_allow_html=True)
                            
                            with col_graf2:
                                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                                st.plotly_chart(graficos['status'], use_container_width=True)
                                st.markdown("</div>", unsafe_allow_html=True)
                        
                        if 'valores_ano' in graficos:
                            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                            st.plotly_chart(graficos['valores_ano'], use_container_width=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                        
                        if 'empresas' in graficos:
                            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                            st.plotly_chart(graficos['empresas'], use_container_width=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Tabela de dados melhorada
                    st.markdown("---")
                    st.markdown("""
                        <div class='search-container'>
                            <h3 style='color: #333; margin-bottom: 20px; text-shadow: none;'>📋 Dados Detalhados</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if not df_filtrado.empty:
                        # Configurar AgGrid com melhorias
                        gb = GridOptionsBuilder.from_dataframe(df_filtrado)
                        
                        # Habilitar filtros em todas as colunas
                        gb.configure_default_column(
                            filterable=True,
                            sortable=True,
                            resizable=True,
                            editable=False,
                            wrapText=True,
                            autoHeight=True
                        )
                        
                        # Configurações de paginação
                        gb.configure_pagination(
                            paginationAutoPageSize=False,
                            paginationPageSize=25
                        )
                        
                        # Configurações de seleção
                        gb.configure_selection(
                            selection_mode='multiple',
                            use_checkbox=True
                        )
                        
                        # Sidebar com filtros
                        gb.configure_side_bar()
                        
                        # Construir opções
                        grid_options = gb.build()
                        
                        # Exibir a tabela com AgGrid
                        st.markdown("""
                            <div class='data-table'>
                                <p><strong>💡 Dicas de uso:</strong></p>
                                <ul>
                                    <li>Clique no ícone <strong>☰</strong> ao lado de cada coluna para filtrar</li>
                                    <li>Use <strong>Ctrl+Click</strong> para selecionar múltiplas linhas</li>
                                    <li>Arraste as bordas das colunas para redimensionar</li>
                                </ul>
                            </div>
                        """, unsafe_allow_html=True)
                        
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
                    else:
                        st.warning("⚠️ Nenhum registro encontrado com os filtros aplicados. Tente ajustar os critérios de busca.")
                    
                else:
                    st.warning("⚠️ Nenhum dado encontrado no arquivo")
            else:
                st.error("❌ Não foi possível baixar o arquivo do Google Drive")
    else:
        st.error("❌ Não foi possível conectar ao Google Drive")
        st.info("💡 Verifique se as credenciais foram configuradas corretamente nos Secrets")

except Exception as e:
    st.error(f"❌ Erro geral: {e}")
    st.markdown("""
        <div class='info-card'>
            <h4>🔧 Instruções de Configuração:</h4>
            <ol>
                <li>No Streamlit Cloud, vá em <strong>Settings</strong> > <strong>Secrets</strong></li>
                <li>Adicione o conteúdo do arquivo JSON baixado no formato:</li>
            </ol>
            <pre style='background: #f8f9fa; padding: 15px; border-radius: 8px; overflow-x: auto;'>
[gcp_service_account]
type = "service_account"
project_id = "seu-projeto-id"
private_key_id = "sua-chave-id"
private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
client_email = "seu-email@projeto.iam.gserviceaccount.com"
client_id = "seu-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "sua-cert-url"
            </pre>
        </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; padding: 20px; opacity: 0.8;'>
        <p style='color: white;'>🏗️ <strong>SGEE+PO</strong> - Sistema de Gestão de Empreendimentos e Obras</p>
        <p style='color: white; font-size: 0.9rem;'>Desenvolvido para otimizar o controle e monitoramento de projetos</p>
    </div>
""", unsafe_allow_html=True)

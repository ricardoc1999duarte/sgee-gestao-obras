import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import openpyxl

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
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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
        
        return df
    except Exception as e:
        st.error(f"Erro ao processar Excel: {e}")
        return None

# Header
st.title("🏗️ SGEE+PO - Sistema de Gestão de Empreendimentos e Obras")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # ID do arquivo no Google Drive
    FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
    
    st.info("📂 Conectado ao Google Drive")
    
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Sobre o Sistema")
    st.markdown("""
    Este sistema permite:
    - ✅ Visualização em tempo real
    - ✅ Filtros avançados
    - ✅ Análise gráfica
    - ✅ Exportação de dados
    """)

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
                    
                    # Exibir informações básicas
                    st.markdown("### 📈 Indicadores Principais")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total de Registros", len(df))
                    
                    with col2:
                        if 'Status/pri' in df.columns:
                            em_andamento = df[df['Status/pri'].str.contains('Andamento', na=False)].shape[0]
                            st.metric("Em Andamento", em_andamento)
                        else:
                            st.metric("Em Andamento", "N/A")
                    
                    with col3:
                        if 'Responsavel' in df.columns:
                            responsaveis = df['Responsavel'].nunique()
                            st.metric("Responsáveis", responsaveis)
                        else:
                            st.metric("Responsáveis", "N/A")
                    
                    with col4:
                        if 'Setor' in df.columns:
                            setores = df['Setor'].nunique()
                            st.metric("Setores", setores)
                        else:
                            st.metric("Setores", "N/A")
                    
                        # Novos Indicadores
                        st.markdown("---")
                        st.markdown("### 🏆 Indicadores Avançados")
                        colA1, colA2, colA3, colA4 = st.columns(4)
                        with colA1:
                            if 'Valor Contrato' in df.columns:
                                valor_total = df['Valor Contrato'].sum()
                                st.metric("Valor Total Contratado", f"R$ {valor_total:,.2f}")
                            else:
                                st.metric("Valor Total Contratado", "N/A")
                        with colA2:
                            if 'Saldo Contratual' in df.columns:
                                saldo_total = df['Saldo Contratual'].sum()
                                st.metric("Saldo Contratual", f"R$ {saldo_total:,.2f}")
                            else:
                                st.metric("Saldo Contratual", "N/A")
                        with colA3:
                            if 'Total Medido Acumulado' in df.columns:
                                medido_total = df['Total Medido Acumulado'].sum()
                                st.metric("Total Medido Acumulado", f"R$ {medido_total:,.2f}")
                            else:
                                st.metric("Total Medido Acumulado", "N/A")
                        with colA4:
                            if 'Dias após vencimento' in df.columns:
                                vencidos = df[df['Dias após vencimento'] > 0].shape[0]
                                st.metric("Contratos Vencidos", vencidos)
                            else:
                                st.metric("Contratos Vencidos", "N/A")
                        st.markdown("---")
                    st.markdown("---")
                    
                    # Filtros
                    st.markdown("### 🔍 Filtros")
                    
                    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
                    
                    with col_filtro1:
                        busca = st.text_input("🔎 Buscar por nome ou contrato", "")
                    
                    with col_filtro2:
                        if 'Setor' in df.columns:
                            setores_list = ['Todos'] + sorted(df['Setor'].dropna().unique().tolist())
                            filtro_setor = st.selectbox("Setor", setores_list)
                        else:
                            filtro_setor = 'Todos'
                    
                    with col_filtro3:
                        if 'Responsavel' in df.columns:
                            resp_list = ['Todos'] + sorted(df['Responsavel'].dropna().unique().tolist())
                            filtro_resp = st.selectbox("Responsável", resp_list)
                        else:
                            filtro_resp = 'Todos'

                        # Filtros Avançados
                        col_filtro4, col_filtro5, col_filtro6 = st.columns(3)
                        with col_filtro4:
                            if 'Empresa Contratada' in df.columns:
                                empresas_list = ['Todos'] + sorted(df['Empresa Contratada'].dropna().unique().tolist())
                                filtro_empresa = st.selectbox("Empresa Contratada", empresas_list)
                            else:
                                filtro_empresa = 'Todos'
                        with col_filtro5:
                            if 'Statusprj' in df.columns:
                                status_list = ['Todos'] + sorted(df['Statusprj'].dropna().unique().tolist())
                                filtro_status = st.selectbox("Status Projeto", status_list)
                            else:
                                filtro_status = 'Todos'
                        with col_filtro6:
                            if 'Ano Empreendimento' in df.columns:
                                anos_list = ['Todos'] + sorted(df['Ano Empreendimento'].dropna().unique().tolist())
                                filtro_ano = st.selectbox("Ano Empreendimento", anos_list)
                            else:
                                filtro_ano = 'Todos'
                    
                    # Aplicar filtros
                    df_filtrado = df.copy()
                    
                    if busca:
                            busca_lower = busca.lower()
                            df_filtrado = df_filtrado[df_filtrado.astype(str).apply(lambda x: busca_lower in x.str.lower().to_string(), axis=1)]
                    
                    if filtro_setor != 'Todos' and 'Setor' in df_filtrado.columns:
                        df_filtrado = df_filtrado[df_filtrado['Setor'] == filtro_setor]
                    
                    if filtro_resp != 'Todos' and 'Responsavel' in df_filtrado.columns:
                        df_filtrado = df_filtrado[df_filtrado['Responsavel'] == filtro_resp]

                        if filtro_empresa != 'Todos' and 'Empresa Contratada' in df_filtrado.columns:
                            df_filtrado = df_filtrado[df_filtrado['Empresa Contratada'] == filtro_empresa]
                        if filtro_status != 'Todos' and 'Statusprj' in df_filtrado.columns:
                            df_filtrado = df_filtrado[df_filtrado['Statusprj'] == filtro_status]
                        if filtro_ano != 'Todos' and 'Ano Empreendimento' in df_filtrado.columns:
                            df_filtrado = df_filtrado[df_filtrado['Ano Empreendimento'] == filtro_ano]
                    
                    st.info(f"📊 Exibindo {len(df_filtrado)} de {len(df)} registros")
                    
                    # Gráficos
                    st.markdown("---")
                    st.markdown("### 📊 Análises Gráficas")
                    
                    col_graf1, col_graf2 = st.columns(2)
                    
                    with col_graf1:
                        if 'Setor' in df_filtrado.columns:
                            st.markdown("#### Distribuição por Setor")
                            setor_counts = df_filtrado['Setor'].value_counts()
                            fig1 = px.pie(values=setor_counts.values, names=setor_counts.index, 
                                         color_discrete_sequence=px.colors.qualitative.Set3)
                            st.plotly_chart(fig1, use_container_width=True)

                            # Gráfico de Prazo Contratual
                            if 'Prazo Contratual' in df_filtrado.columns:
                                st.markdown("#### Prazo Contratual (dias)")
                                fig_prazo = px.histogram(df_filtrado, x='Prazo Contratual', nbins=20, title='Distribuição do Prazo Contratual')
                                st.plotly_chart(fig_prazo, use_container_width=True)
                    
                    with col_graf2:
                        if 'Responsavel' in df_filtrado.columns:
                            st.markdown("#### Obras por Responsável")
                            resp_counts = df_filtrado['Responsavel'].value_counts().head(10)
                            fig2 = px.bar(x=resp_counts.values, y=resp_counts.index, 
                                         orientation='h',
                                         labels={'x': 'Quantidade', 'y': 'Responsável'},
                                         color_discrete_sequence=['#667eea'])
                            st.plotly_chart(fig2, use_container_width=True)

                            # Gráfico de Valor Total por Empresa
                            if 'Empresa Contratada' in df_filtrado.columns and 'Valor Contrato' in df_filtrado.columns:
                                st.markdown("#### Top Empresas por Valor Contratado")
                                empresa_valor = df_filtrado.groupby('Empresa Contratada')['Valor Contrato'].sum().sort_values(ascending=False).head(10)
                                fig_emp = px.bar(x=empresa_valor.values, y=empresa_valor.index, orientation='h',
                                                labels={'x': 'Valor Total', 'y': 'Empresa'}, color_discrete_sequence=['#764ba2'])
                                st.plotly_chart(fig_emp, use_container_width=True)

                            # Gráfico de Evolução do Medido Acumulado
                            if 'Data Inicio Cnt' in df_filtrado.columns and 'Total Medido Acumulado' in df_filtrado.columns:
                                st.markdown("#### Evolução do Medido Acumulado")
                                df_filtrado['Data Inicio Cnt'] = pd.to_datetime(df_filtrado['Data Inicio Cnt'], errors='coerce')
                                evolucao = df_filtrado.groupby('Data Inicio Cnt')['Total Medido Acumulado'].sum().reset_index()
                                fig_evol = px.line(evolucao, x='Data Inicio Cnt', y='Total Medido Acumulado', title='Evolução do Medido Acumulado')
                                st.plotly_chart(fig_evol, use_container_width=True)
                    
                    # Tabela de dados
                    st.markdown("---")
                    st.markdown("### 📋 Dados Detalhados")
                    
                    # Opção de download
                    col_download1, col_download2 = st.columns([1, 4])
                    with col_download1:
                        csv = df_filtrado.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Baixar CSV",
                            data=csv,
                            file_name="sgee_obras_filtrado.csv",
                            mime="text/csv"
                        )
                    
                    # Exibir tabela
                    st.dataframe(df_filtrado, use_container_width=True, height=400)
                    
                else:
                    st.warning("⚠️ Nenhum dado encontrado no arquivo")
            else:
                st.error("❌ Não foi possível baixar o arquivo do Google Drive")
    else:
        st.error("❌ Não foi possível conectar ao Google Drive")
        st.info("💡 Verifique se as credenciais foram configuradas corretamente nos Secrets")

except Exception as e:
    st.error(f"❌ Erro geral: {e}")
    st.info("""
    ### 🔧 Instruções de Configuração:
    
    1. No Streamlit Cloud, vá em **Settings** > **Secrets**
    2. Adicione o conteúdo do arquivo JSON baixado no formato:
    
    ```toml
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
    ```
    """)

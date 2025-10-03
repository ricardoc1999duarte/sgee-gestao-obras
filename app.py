import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# --- Configuração da Página ---
st.set_page_config(
    page_title="SGEE+PO - Gestão de Obras",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
 )

# --- CSS Customizado ---
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border: 1px solid #e6e6e6;
    }
    .stButton>button {
        background-color: #667eea;
        color: white;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Funções de Conexão e Processamento de Dados ---

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
    """Lê o arquivo Excel e retorna um DataFrame limpo."""
    try:
        df = pd.read_excel(file_stream, sheet_name='SGEEePO', engine='openpyxl')
        df = df.dropna(how='all')
        # CORREÇÃO: Padroniza nomes de colunas para remover espaços e acentos
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
        
        # Mapeamento de nomes de colunas antigos para novos (ajuste conforme sua planilha)
        # Isso ajuda a manter a consistência
        rename_map = {
            'num_cnt': 'Num_CNT', 'objeto_cnt': 'Objeto_Cnt', 'responsável': 'Responsavel',
            'setor_responsavel': 'Setor', 'empresa_contratada': 'Empresa_Contratada',
            'statusprj(ajustada)': 'Status_Obra', 'statusprj': 'Status_Projeto',
            'valor_contrato': 'Valor_Contrato', 'valor_aditivos': 'Valor_Aditivos',
            'total_contrato': 'Total_Contrato', 'saldo_contratual': 'Saldo_Contratual',
            'total_medido_acumulado': 'Total_Medido_Acumulado', 'data_fim_cnt_com_aditivos': 'Data_Fim_Aditivos',
            'dias_após_vencimento': 'Dias_Apos_Vencimento', 'ano_empreendimento': 'Ano_Empreendimento',
            'prazo_contratual': 'Prazo_Contratual', 'data_inicio_cnt': 'Data_Inicio_Contrato'
        }
        
        # Renomeia apenas as colunas que existem no DataFrame
        df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)
        
        return df
    except Exception as e:
        st.error(f"Erro ao processar o arquivo Excel: {e}")
        return None

# --- Início da Interface do App ---

st.title("🏗️ SGEE+PO - Sistema de Gestão de Empreendimentos e Obras")
st.markdown("---")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Configurações")
    FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg"
    st.info(f"ID do Arquivo: ...{FILE_ID[-10:]}")
    
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.cache_resource.clear()
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

# --- Carregamento e Processamento Principal ---
service = conectar_google_drive()
if service:
    with st.spinner("📥 Carregando e processando dados..."):
        file_stream = baixar_arquivo_drive(service, FILE_ID)
        if file_stream:
            df = processar_dados_excel(file_stream)
            
            if df is not None and not df.empty:
                st.success("✅ Dados carregados e processados com sucesso!")

                # --- Cálculos e Engenharia de Features ---
                df_calc = df.copy()

                # Datas e Prazos
                if 'Data_Fim_Aditivos' in df_calc.columns:
                    df_calc['Data_Fim_Aditivos'] = pd.to_datetime(df_calc['Data_Fim_Aditivos'], errors='coerce')
                    hoje = pd.Timestamp.now().normalize()
                    df_calc['Dias_Restantes'] = (df_calc['Data_Fim_Aditivos'] - hoje).dt.days
                
                if 'Dias_Apos_Vencimento' in df_calc.columns:
                    df_calc['Atraso'] = df_calc['Dias_Apos_Vencimento'].apply(lambda x: x if pd.notna(x) and x > 0 else 0)

                # Valores Financeiros
                numeric_cols = ['Total_Medido_Acumulado', 'Total_Contrato', 'Saldo_Contratual', 'Valor_Contrato', 'Valor_Aditivos']
                for col in numeric_cols:
                    if col in df_calc.columns:
                        df_calc[col] = pd.to_numeric(df_calc[col], errors='coerce').fillna(0)

                if 'Total_Medido_Acumulado' in df_calc.columns and 'Total_Contrato' in df_calc.columns:
                    df_calc['%_Executado'] = df_calc.apply(lambda row: (row['Total_Medido_Acumulado'] / row['Total_Contrato'] * 100) if row['Total_Contrato'] > 0 else 0, axis=1).round(2)
                
                if 'Valor_Contrato' in df_calc.columns and 'Valor_Aditivos' in df_calc.columns:
                    df_calc['%_Aditivo'] = df_calc.apply(lambda row: (row['Valor_Aditivos'] / row['Valor_Contrato'] * 100) if row['Valor_Contrato'] > 0 else 0, axis=1).round(2)

                # --- Indicadores Principais (KPIs) ---
                st.markdown("### 📈 Indicadores Principais")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total de Contratos", len(df_calc))
                
                # CORREÇÃO: Verifica a coluna correta para status
                status_col = 'Status_Obra' if 'Status_Obra' in df_calc.columns else ('Status_Projeto' if 'Status_Projeto' in df_calc.columns else None)
                if status_col:
                    em_andamento = df_calc[df_calc[status_col].str.contains('Andamento|Execução', case=False, na=False)].shape[0]
                    col2.metric("Em Andamento/Execução", em_andamento)
                else:
                    col2.metric("Em Andamento", "N/A")

                col3.metric("Responsáveis Únicos", df_calc['Responsavel'].nunique() if 'Responsavel' in df_calc.columns else "N/A")
                col4.metric("Setores Únicos", df_calc['Setor'].nunique() if 'Setor' in df_calc.columns else "N/A")

                # --- Indicadores Avançados (Conforme solicitado) ---
                st.markdown("---")
                st.markdown("### 🏆 Indicadores de Aditivos (Regra de Negócio)")
                colA1, colA2, colA3 = st.columns(3)

                if '%_Aditivo' in df_calc.columns:
                    # Filtra contratos com % aditivo <= 50%
                    df_aditivo_filtrado = df_calc[df_calc['%_Aditivo'] <= 50]
                    
                    soma_contrato = df_aditivo_filtrado['Valor_Contrato'].sum()
                    soma_aditivo = df_aditivo_filtrado['Valor_Aditivos'].sum()
                    
                    indice_global = (soma_aditivo / soma_contrato * 100) if soma_contrato > 0 else 0
                    
                    colA1.metric("Somatório Valor Contrato (Aditivo ≤ 50%)", f"R$ {soma_contrato:,.2f}")
                    colA2.metric("Somatório Valor Aditivos (Aditivo ≤ 50%)", f"R$ {soma_aditivo:,.2f}")
                    colA3.metric("Índice Global de Aditivos", f"{indice_global:.2f}%")
                else:
                    colA1.metric("Somatório Valor Contrato", "N/A")
                    colA2.metric("Somatório Valor Aditivos", "N/A")
                    colA3.metric("Índice Global de Aditivos", "N/A")

                # --- Filtros ---
                st.markdown("---")
                st.markdown("### 🔍 Filtros Dinâmicos")
                
                # CORREÇÃO: Lógica de filtros corrigida (não mais aninhada)
                df_filtrado = df_calc.copy()

                col_f1, col_f2, col_f3 = st.columns(3)
                
                # Filtro de Busca Geral
                busca = col_f1.text_input("🔎 Buscar em todo o registro (contrato, objeto, etc.)", "")
                if busca:
                    busca_lower = busca.lower()
                    # Pesquisa em todas as colunas convertidas para string
                    df_filtrado = df_filtrado[df_filtrado.apply(lambda row: any(busca_lower in str(cell).lower() for cell in row), axis=1)]

                # Filtros em Selectbox
                def create_selectbox(column_name, label):
                    if column_name in df_calc.columns:
                        options = ['Todos'] + sorted(df_calc[column_name].dropna().unique().tolist())
                        return st.selectbox(label, options)
                    return 'Todos'

                filtro_setor = col_f2.selectbox("Setor", ['Todos'] + sorted(df_calc['Setor'].dropna().unique()) if 'Setor' in df_calc.columns else ['Todos'])
                filtro_resp = col_f3.selectbox("Responsável", ['Todos'] + sorted(df_calc['Responsavel'].dropna().unique()) if 'Responsavel' in df_calc.columns else ['Todos'])
                
                if filtro_setor != 'Todos':
                    df_filtrado = df_filtrado[df_filtrado['Setor'] == filtro_setor]
                if filtro_resp != 'Todos':
                    df_filtrado = df_filtrado[df_filtrado['Responsavel'] == filtro_resp]
                
                st.info(f"📊 Exibindo {len(df_filtrado)} de {len(df_calc)} registros após filtros.")

                # --- Análises Gráficas ---
                st.markdown("---")
                st.markdown("### 📊 Análises Gráficas")
                col_g1, col_g2 = st.columns(2)

                with col_g1:
                    if 'Setor' in df_filtrado.columns and not df_filtrado['Setor'].empty:
                        st.markdown("#### Contratos por Setor")
                        setor_counts = df_filtrado['Setor'].value_counts()
                        fig = px.pie(values=setor_counts.values, names=setor_counts.index, title="Distribuição por Setor", hole=0.3)
                        st.plotly_chart(fig, use_container_width=True)

                with col_g2:
                    if 'Responsavel' in df_filtrado.columns and not df_filtrado['Responsavel'].empty:
                        st.markdown("#### Top 10 Responsáveis por Nº de Contratos")
                        resp_counts = df_filtrado['Responsavel'].value_counts().nlargest(10)
                        fig = px.bar(y=resp_counts.index, x=resp_counts.values, orientation='h', labels={'y': 'Responsável', 'x': 'Nº de Contratos'})
                        fig.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig, use_container_width=True)

                # --- Tabela de Dados Detalhada ---
                st.markdown("---")
                st.markdown("### 📋 Dados Detalhados")
                
                # Colunas para exibir (usando os nomes padronizados)
                colunas_exibir = [
                    'Num_CNT', 'Objeto_Cnt', 'Empresa_Contratada', 'Status_Obra', 'Responsavel', 'Setor',
                    'Data_Fim_Aditivos', 'Dias_Restantes', 'Atraso',
                    'Valor_Contrato', 'Valor_Aditivos', 'Total_Contrato', 'Total_Medido_Acumulado', 
                    '%_Executado', '%_Aditivo'
                ]
                colunas_validas = [c for c in colunas_exibir if c in df_filtrado.columns]
                
                st.dataframe(df_filtrado[colunas_validas], use_container_width=True, height=500)

                # Opção de Download
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


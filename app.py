import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import openpyxl
from datetime import datetime

# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="SGEE+PO - Dashboard BI Profissional",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Customizado para um Tema Mais Moderno ---
st.markdown("""<style>
@import url(\'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap\');
html, body, [class*="st-emotion-cache"] {
    font-family: \'Inter\', sans-serif;
}
.main .block-container {
    padding-top: 2rem;
    padding-right: 2rem;
    padding-left: 2rem;
    padding-bottom: 2rem;
}
.stApp {
    background-color: #f0f2f6; /* Light gray background */
}
.dark .stApp {
    background-color: #1e1e1e; /* Dark background */
}
h1, h2, h3, h4, h5, h6 {
    color: #262626;
}
.dark h1, .dark h2, .dark h3, .dark h4, .dark h5, .dark h6 {
    color: #f0f2f6;
}
.stMetric {
    background-color: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    border-left: 5px solid #4CAF50; /* Green accent */
}
.dark .stMetric {
    background-color: #2d2d2d;
    color: #f0f2f6;
    border-left: 5px solid #66BB6A; /* Lighter green accent for dark mode */
}
.stMetric label {
    color: #555555;
}
.dark .stMetric label {
    color: #cccccc;
}
.stMetric .css-10trblm.e16nr0p30 {
    font-size: 1.5rem;
    font-weight: 600;
}
.stButton>button {
    border-radius: 8px;
    border: 1px solid #e0e0e0;
    color: #333333;
    background-color: #ffffff;
}
.dark .stButton>button {
    border: 1px solid #444444;
    color: #eeeeee;
    background-color: #333333;
}
.stSelectbox, .stTextInput {
    border-radius: 8px;
}
.stMultiSelect div[data-baseweb="select"] > div {
    border-radius: 8px;
}
.stTabs [data-baseweb="tab-list"] button {
    background-color: #ffffff;
    border-radius: 8px 8px 0 0;
    border-bottom: none;
}
.dark .stTabs [data-baseweb="tab-list"] button {
    background-color: #2d2d2d;
    color: #f0f2f6;
}
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
    border-bottom: 3px solid #4CAF50;
    color: #4CAF50;
    font-weight: 600;
}
.dark .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
    border-bottom: 3px solid #66BB6A;
    color: #66BB6A;
}
.stAlert {
    border-radius: 8px;
}
.css-1dp5vir.e8zbici2 {
    background-color: #ffffff;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    padding: 1rem;
}
.dark .css-1dp5vir.e8zbici2 {
    background-color: #2d2d2d;
    color: #f0f2f6;
}
</style>
""", unsafe_allow_html=True)

# --- Funções de Conexão e Download do Google Drive ---
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

# --- Função de Processamento de Dados (com Deduplicação e Limpeza) ---
@st.cache_data(ttl=3600)
def processar_dados(file_stream):
    try:
        df = pd.read_excel(file_stream, sheet_name="SGEEePO", engine="openpyxl")
        
        # Limpeza inicial: remover linhas e colunas totalmente vazias
        df = df.dropna(how="all")
        df = df.dropna(axis=1, how="all")
        
        # Renomear colunas para padronização e facilitar o acesso
        df.columns = df.columns.str.strip().str.replace(" ", "_").str.replace("/", "_").str.replace(".", "_")
        
        # Padronizar nomes de colunas importantes
        df = df.rename(columns={
            "Num_CNT": "Num_Contrato",
            "Objeto_Cnt": "Objeto_Contrato",
            "Cod_Empreendimento": "Codigo_Empreendimento",
            "Nome_Empreendimento": "Nome_Empreendimento",
            "Statusprj": "Status_Projeto",
            "Base_SGEE_Setor_Responsavel": "Setor_Responsavel",
            "Codtrf": "Codigo_TRF",
            "Escopo": "Escopo",
            "Executor": "Executor",
            "Desctematica": "Desc_Tematica",
            "Descfinalidade": "Desc_Finalidade",
            "Nome_Atv": "Nome_Atividade",
            "Responsavel": "Responsavel",
            "Foco": "Foco",
            "Ano_Empreendimento": "Ano_Empreendimento",
            "Seq_Empreendimento": "Sequencia_Empreendimento",
            "Nome_Meta": "Nome_Meta",
            "Valor_Atv": "Valor_Atividade",
            "Prioridade": "Prioridade",
            "Programaempree": "Programa_Empreendimento",
            "Valorrealizado": "Valor_Realizado_Atividade",
            "Valorplanejado": "Valor_Planejado_Atividade",
            "Valortotal": "Valor_Total_Atividade",
            "Nome": "Nome_Geral",
            "Fonte_Rec": "Fonte_Recurso",
            "Base_SGEE_Ano_Finalização_Contrato": "Ano_Finalizacao_Contrato",
            "Base_SGEE_Empresa_Contratada": "Empresa_Contratada",
            "Base_SGEE_Numero_Licitacao": "Numero_Licitacao",
            "Base_SGEE_Responsavel": "Responsavel_Base_SGEE",
            "Base_SGEE_Status_Contrato": "Status_Contrato",
            "Base_SGEE_Programa": "Programa_Base_SGEE",
            "Base_SGEE_Data_Assin_Cnt": "Data_Assinatura_Contrato",
            "Base_SGEE_Tipo_Cnt": "Tipo_Contrato",
            "Base_SGEE_Numero_Dias_Aditivados": "Numero_Dias_Aditivados",
            "Base_SGEE_Total_Contrato": "Total_Contrato",
            "Base_SGEE_Saldo_Contratual": "Saldo_Contratual",
            "Base_SGEE_Total_Medido_Acumulado": "Total_Medido_Acumulado",
            "Base_SGEE_Ordem_Renovação": "Ordem_Renovacao",
            "Base_SGEE_Num_Aditivo_Renovação": "Num_Aditivo_Renovacao",
            "Base_SGEE_Data_Última_Renovação": "Data_Ultima_Renovacao",
            "Base_SGEE_Vl_Total_Aditivo_Última_Renovação": "Valor_Total_Aditivo_Ultima_Renovacao",
            "Base_SGEE_Data_Inicio_Cnt": "Data_Inicio_Contrato",
            "Base_SGEE_Data_Fim_Cnt_Original": "Data_Fim_Contrato_Original",
            "Base_SGEE_Data_Fim_Cnt_Com_Aditivos": "Data_Fim_Contrato_Com_Aditivos",
            "Base_SGEE_Valor_Contrato": "Valor_Contrato",
            "Base_SGEE_Valor_Aditivos": "Valor_Aditivos",
            "Base_SGEE_Prazo_Contratual": "Prazo_Contratual"
        })

        # Converter tipos de dados
        date_cols = [
            "Data_Assinatura_Contrato", "Data_Ultima_Renovacao",
            "Data_Inicio_Contrato", "Data_Fim_Contrato_Original",
            "Data_Fim_Contrato_Com_Aditivos"
        ]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors=\'coerce\')

        numeric_cols = [
            "Ano_Empreendimento", "Sequencia_Empreendimento", "Valor_Atividade",
            "Prioridade", "Valor_Realizado_Atividade", "Valor_Planejado_Atividade",
            "Valor_Total_Atividade", "Ano_Finalizacao_Contrato",
            "Numero_Dias_Aditivados", "Total_Contrato", "Saldo_Contratual",
            "Total_Medido_Acumulado", "Num_Aditivo_Renovacao",
            "Valor_Total_Aditivo_Ultima_Renovacao", "Valor_Contrato",
            "Valor_Aditivos", "Prazo_Contratual"
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors=\'coerce\').fillna(0)

        # --- Deduplicação Inteligente ---
        id_cols = ["Num_Contrato", "Codigo_Empreendimento", "Codigo_TRF", "Nome_Atividade"]
        
        initial_rows = len(df)
        df_deduplicado = df.drop_duplicates(subset=id_cols, keep=\'first\')
        duplicates_removed = initial_rows - len(df_deduplicado)

        st.session_state["duplicates_removed"] = duplicates_removed
        st.session_state["total_initial_records"] = initial_rows

        return df_deduplicado
    except Exception as e:
        st.error(f"Erro ao processar Excel: {e}")
        return None

# --- Funções Auxiliares para Formatação e KPIs ---
def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calculate_kpis(df):
    total_registros = len(df)
    total_contratado = df["Total_Contrato"].sum()
    total_realizado = df["Total_Medido_Acumulado"].sum()
    saldo_contratual = df["Saldo_Contratual"].sum()
    
    em_andamento = df[df["Status_Contrato"].str.contains("andamento|execucao", case=False, na=False)].shape[0]
    concluidos = df[df["Status_Contrato"].str.contains("concluido", case=False, na=False)].shape[0]
    
    percentual_execucao = (total_realizado / total_contratado * 100) if total_contratado > 0 else 0

    return {
        "Total de Registros": {"value": total_registros, "format": "number", "icon": "📝"},
        "Total Contratado": {"value": total_contratado, "format": "currency", "icon": "💰"},
        "Total Realizado": {"value": total_realizado, "format": "currency", "icon": "✅"},
        "Saldo Contratual": {"value": saldo_contratual, "format": "currency", "icon": "⏳"},
        "Em Andamento": {"value": em_andamento, "format": "number", "icon": "🚧"},
        "Concluídos": {"value": concluidos, "format": "number", "icon": "🎉"},
        "Execução": {"value": percentual_execucao, "format": "percentage", "icon": "📈"},
    }

# --- Layout do Dashboard --- 
st.title("📊 SGEE+PO - Dashboard de Gestão de Obras")
st.markdown("<p style=\'font-size:1.1rem; color: #555;\'>Visão geral e acompanhamento de empreendimentos e contratos.</p>", unsafe_allow_html=True)
st.markdown("---")

# --- Sidebar --- 
with st.sidebar:
    st.header("⚙️ Configurações e Filtros")
    
    FILE_ID = "1VTCrrZWwWsmhE8nNrGWmEggrgeRbjCCg" # ID do arquivo no Google Drive
    st.info("📂 Conectado ao Google Drive")
    
    if st.button("🔄 Atualizar Dados", help="Limpa o cache e recarrega os dados do Google Drive"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🔍 Filtros Globais")

# --- Carregamento e Filtros ---
try:
    service = conectar_google_drive()
    
    if service:
        with st.spinner("📥 Carregando e processando dados do Google Drive..."):
            file_stream = baixar_arquivo_drive(service, FILE_ID)
            
            if file_stream:
                df_original = processar_dados(file_stream)
                
                if df_original is not None and not df_original.empty:
                    st.success("✅ Dados carregados e processados com sucesso!")
                    
                    if "duplicates_removed" in st.session_state and st.session_state["duplicates_removed"] > 0:
                        st.info(f\'🗑️ {st.session_state["duplicates_removed"]} registros duplicados removidos de {st.session_state["total_initial_records"]} originais.\')

                    # --- Filtros Globais --- 
                    all_setores = ["Todos"] + sorted(df_original["Setor_Responsavel"].dropna().unique().tolist())
                    all_responsaveis = ["Todos"] + sorted(df_original["Responsavel"].dropna().unique().tolist())
                    all_status = ["Todos"] + sorted(df_original["Status_Contrato"].dropna().unique().tolist())

                    with st.sidebar:
                        busca_global = st.text_input("🔎 Buscar em tudo", "", placeholder="Digite um termo para buscar em todas as colunas")
                        filtro_setor = st.selectbox("Setor Responsável", all_setores)
                        filtro_responsavel = st.selectbox("Responsável", all_responsaveis)
                        filtro_status = st.selectbox("Status do Contrato", all_status)

                        min_date = df_original["Data_Assinatura_Contrato"].min().to_pydatetime() if not pd.isna(df_original["Data_Assinatura_Contrato"].min()) else datetime(2000, 1, 1)
                        max_date = df_original["Data_Assinatura_Contrato"].max().to_pydatetime() if not pd.isna(df_original["Data_Assinatura_Contrato"].max()) else datetime.now()
                        
                        date_range = st.slider(
                            "Período de Assinatura do Contrato",
                            value=(min_date, max_date),
                            format="DD/MM/YYYY"
                        )

                        min_valor = float(df_original["Total_Contrato"].min())
                        max_valor = float(df_original["Total_Contrato"].max())
                        valor_range = st.slider(
                            "Faixa de Valor Contratado",
                            min_value=min_valor,
                            max_value=max_valor,
                            value=(min_valor, max_valor),
                            format="R$ %.2f"
                        )

                    # --- Aplicação dos Filtros --- 
                    df_filtrado = df_original.copy()

                    if busca_global:
                        df_filtrado = df_filtrado[df_filtrado.apply(lambda row: row.astype(str).str.contains(busca_global, case=False, na=False).any(), axis=1)]
                    
                    if filtro_setor != "Todos":
                        df_filtrado = df_filtrado[df_filtrado["Setor_Responsavel"] == filtro_setor]
                    
                    if filtro_responsavel != "Todos":
                        df_filtrado = df_filtrado[df_filtrado["Responsavel"] == filtro_responsavel]
                    
                    if filtro_status != "Todos":
                        df_filtrado = df_filtrado[df_filtrado["Status_Contrato"] == filtro_status]

                    if date_range:
                        start_date, end_date = date_range
                        df_filtrado = df_filtrado[
                            (df_filtrado["Data_Assinatura_Contrato"] >= pd.to_datetime(start_date)) &
                            (df_filtrado["Data_Assinatura_Contrato"] <= pd.to_datetime(end_date))
                        ]
                    
                    if valor_range:
                        min_val, max_val = valor_range
                        df_filtrado = df_filtrado[
                            (df_filtrado["Total_Contrato"] >= min_val) &
                            (df_filtrado["Total_Contrato"] <= max_val)
                        ]

                    st.sidebar.markdown("---")
                    st.sidebar.markdown(f"**Registros Exibidos:** {len(df_filtrado)} de {len(df_original)}")

                    # --- Abas para Organização do Dashboard ---
                    tab1, tab2, tab3 = st.tabs(["📈 Visão Geral", "📊 Análises Detalhadas", "📋 Dados Brutos"])

                    with tab1:
                        st.header("Indicadores Chave de Performance (KPIs)")
                        kpis = calculate_kpis(df_filtrado)
                        cols = st.columns(4) 
                        kpi_items = list(kpis.items())
                        for i in range(len(kpi_items)):
                            kpi_name, kpi_data = kpi_items[i]
                            with cols[i % 4]:
                                if kpi_data["format"] == "currency":
                                    st.metric(label=f\'{kpi_data["icon"]} {kpi_name}\", value=format_currency(kpi_data["value"]))
                                elif kpi_data["format"] == "percentage":
                                    st.metric(label=f\'{kpi_data["icon"]} {kpi_name}\", value=f\'{kpi_data["value"]:.2f}%\')
                                else:
                                    st.metric(label=f\'{kpi_data["icon"]} {kpi_name}\", value=f\'{kpi_data["value"]:,.0f}\".replace(",", "."))
                        
                        st.markdown("---")
                        st.header("Visão Geral Gráfica")

                        col_chart1, col_chart2 = st.columns(2)
                        with col_chart1:
                            if "Setor_Responsavel" in df_filtrado.columns and not df_filtrado["Setor_Responsavel"].empty:
                                setor_counts = df_filtrado["Setor_Responsavel"].value_counts().reset_index()
                                setor_counts.columns = ["Setor", "Quantidade"]
                                fig_setor = px.pie(setor_counts, values="Quantidade", names="Setor", title="Distribuição por Setor Responsável",
                                                   color_discrete_sequence=px.colors.qualitative.Pastel)
                                st.plotly_chart(fig_setor, use_container_width=True)
                            else:
                                st.warning("Dados de Setor Responsável insuficientes para o gráfico.")

                        with col_chart2:
                            if "Status_Contrato" in df_filtrado.columns and not df_filtrado["Status_Contrato"].empty:
                                status_counts = df_filtrado["Status_Contrato"].value_counts().reset_index()
                                status_counts.columns = ["Status", "Quantidade"]
                                fig_status = px.bar(status_counts, x="Status", y="Quantidade", title="Contratos por Status",
                                                    color="Status", color_discrete_map={
                                                        "Em andamento": "#4CAF50", "Concluído": "#2196F3",
                                                        "Cancelado": "#F44336", "Suspenso": "#FFC107"
                                                    })
                                st.plotly_chart(fig_status, use_container_width=True)
                            else:
                                st.warning("Dados de Status do Contrato insuficientes para o gráfico.")

                    with tab2:
                        st.header("Análises Detalhadas")

                        if "Responsavel" in df_filtrado.columns and "Total_Contrato" in df_filtrado.columns:
                            resp_value = df_filtrado.groupby("Responsavel")["Total_Contrato"].sum().nlargest(10).reset_index()
                            fig_resp_value = px.bar(resp_value, x="Total_Contrato", y="Responsavel", orientation="h",
                                                    title="Top 10 Responsáveis por Valor Contratado",
                                                    labels={"Total_Contrato": "Valor Contratado", "Responsavel": "Responsável"},
                                                    color_discrete_sequence=px.colors.sequential.Viridis)
                            st.plotly_chart(fig_resp_value, use_container_width=True)
                        else:
                            st.warning("Dados de Responsável ou Valor Contratado insuficientes para o gráfico.")

                        if "Ano_Empreendimento" in df_filtrado.columns and "Total_Contrato" in df_filtrado.columns and "Total_Medido_Acumulado" in df_filtrado.columns:
                            df_yearly = df_filtrado.groupby("Ano_Empreendimento")[["Total_Contrato", "Total_Medido_Acumulado"]].sum().reset_index()
                            df_yearly = df_yearly.sort_values("Ano_Empreendimento")
                            fig_yearly = px.line(df_yearly, x="Ano_Empreendimento", y=["Total_Contrato", "Total_Medido_Acumulado"],
                                                 title="Evolução Anual de Contratado vs. Realizado",
                                                 labels={"value": "Valor", "Ano_Empreendimento": "Ano"},
                                                 line_shape="spline", render_mode="svg")
                            fig_yearly.update_traces(mode=\'lines+markers\')
                            st.plotly_chart(fig_yearly, use_container_width=True)
                        else:
                            st.warning("Dados de Ano, Total Contratado ou Total Realizado insuficientes para o gráfico de evolução.")

                    with tab3:
                        st.header("Dados Brutos")
                        st.write(f"Exibindo {len(df_filtrado)} de {len(df_original)} registros.")
                        
                        st.dataframe(df_filtrado, use_container_width=True)

                        csv = df_filtrado.to_csv(index=False).encode(\'utf-8\')
                        st.download_button(
                            label="📥 Baixar Dados Filtrados (CSV)",
                            data=csv,
                            file_name="sgee_dados_filtrados.csv",
                            mime="text/csv",
                            help="Baixa os dados atualmente exibidos na tabela como um arquivo CSV."
                        )

                else:
                    st.warning("⚠️ Nenhum dado encontrado no arquivo ou DataFrame vazio após processamento.")
            else:
                st.error("❌ Não foi possível baixar o arquivo do Google Drive. Verifique o FILE_ID.")
    else:
        st.error("❌ Não foi possível conectar ao Google Drive. Verifique as credenciais.")
        st.info("""
### 🔧 Instruções de Configuração de Credenciais (Secrets do Streamlit):

1. No Streamlit Cloud, vá em **Settings** > **Secrets**.
2. Adicione o conteúdo do arquivo JSON da sua conta de serviço do Google Cloud no formato:

```toml
[gcp_service_account]
type = "service_account"
project_id = "seu-projeto-id"
private_key_id = "sua-chave-id"
private_key = """-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"""
client_email = "seu-email@projeto.iam.gserviceaccount.com"
client_id = "seu-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "sua-cert-url"
```
""")

except Exception as e:
    st.error(f"❌ Erro geral no aplicativo: {e}")

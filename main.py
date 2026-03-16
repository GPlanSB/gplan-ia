import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# CONFIGURAÇÃO
st.set_page_config(
    page_title="GPlan IA",
    page_icon="🚀",
    layout="wide"
)

# ESTILO VISUAL
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{
background-color:#0E1117;
color:white;
}

.metric-card{
background:#1F2937;
padding:15px;
border-radius:10px;
border:1px solid #374151;
}
</style>
""", unsafe_allow_html=True)

st.title("🚀 GPlan IA — Sistema Inteligente de Gestão")

st.markdown("---")

# SIDEBAR
st.sidebar.header("📥 Importar Dados")

file = st.sidebar.file_uploader(
    "Envie seu arquivo",
    type=["xlsx","csv"]
)

# PROCESSAMENTO
if file:

    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    st.sidebar.success("Arquivo carregado!")

    # FILTROS DINÂMICOS
    st.sidebar.markdown("### 🎯 Filtros")

    if "Responsavel" in df.columns:
        resp = st.sidebar.multiselect(
            "Responsável",
            df["Responsavel"].unique(),
            default=df["Responsavel"].unique()
        )
        df = df[df["Responsavel"].isin(resp)]

    if "Status" in df.columns:
        status = st.sidebar.multiselect(
            "Status",
            df["Status"].unique(),
            default=df["Status"].unique()
        )
        df = df[df["Status"].isin(status)]

    # KPI
    st.subheader("📊 Indicadores Estratégicos")

    total = len(df)

    if "Status" in df.columns:
        atrasadas = len(df[df["Status"] == "Atrasado"])
    else:
        atrasadas = 0

    progresso = ((total - atrasadas) / total) * 100 if total > 0 else 0

    col1,col2,col3,col4 = st.columns(4)

    col1.metric("Total de Tarefas", total)
    col2.metric("Tarefas Atrasadas", atrasadas)
    col3.metric("Saúde do Projeto", f"{progresso:.1f}%")
    col4.metric("Risco Operacional", "Baixo" if progresso > 80 else "Alto")

    st.markdown("---")

    # GRÁFICOS

    colA,colB = st.columns(2)

    if "Status" in df.columns:

        fig_status = px.pie(
            df,
            names="Status",
            title="Distribuição de Status",
            template="plotly_dark"
        )

        colA.plotly_chart(fig_status, use_container_width=True)

    if "Responsavel" in df.columns:

        fig_resp = px.bar(
            df,
            x="Responsavel",
            title="Carga de Trabalho por Responsável",
            template="plotly_dark"
        )

        colB.plotly_chart(fig_resp, use_container_width=True)

    # GRÁFICO DE EVOLUÇÃO

    if "Data" in df.columns:

        df["Data"] = pd.to_datetime(df["Data"])

        evolucao = df.groupby("Data").size().reset_index(name="Tarefas")

        fig = px.line(
            evolucao,
            x="Data",
            y="Tarefas",
            title="Evolução do Projeto",
            template="plotly_dark"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # TABELA DE DADOS
    st.subheader("📋 Base de Dados")

    st.dataframe(df, use_container_width=True)

# CHATBOT

st.markdown("---")
st.subheader("🤖 Consultor GPlan")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

prompt = st.chat_input("Pergunte algo sobre o projeto...")

if prompt:

    st.session_state.chat_history.append(
        {"role":"user","content":prompt}
    )

    with st.chat_message("user"):
        st.write(prompt)

    # RESPOSTA IA

    if "atraso" in prompt.lower():

        response = """
### 🚨 Diagnóstico Operacional

Identifiquei risco no fluxo de execução.

Plano recomendado:

1️⃣ Revisar gargalos na etapa de execução  
2️⃣ Limitar tarefas simultâneas (WIP)  
3️⃣ Aplicar reuniões rápidas de alinhamento (Daily)  
4️⃣ Priorizar tarefas críticas  

Framework recomendado: **Kanban + PMBOK**
"""

    elif "produtividade" in prompt.lower():

        response = """
### 📈 Análise de Produtividade

Sugestões:

• redistribuir carga de trabalho  
• eliminar tarefas bloqueadas  
• definir responsáveis claros  
• medir throughput semanal
"""

    else:

        response = "Estou analisando os dados. Pergunte sobre **atrasos, produtividade ou riscos**."

    with st.chat_message("assistant"):
        st.write(response)

    st.session_state.chat_history.append(
        {"role":"assistant","content":response}
    )

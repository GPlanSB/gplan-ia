import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI

client = OpenAI()

st.set_page_config(
    page_title="GPlan IA",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 GPlan IA — Copiloto de Gerenciamento de Projetos")

st.sidebar.header("Importar dados")

file = st.sidebar.file_uploader(
    "Envie sua planilha",
    type=["xlsx","csv"]
)

# ---------------------------
# LEITURA DOS DADOS
# ---------------------------

if file:

    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    st.success("Dados carregados!")

    st.subheader("📊 Dashboard do Projeto")

    total = len(df)

    atrasadas = 0
    if "Status" in df.columns:
        atrasadas = len(df[df["Status"]=="Atrasado"])

    progresso = ((total - atrasadas) / total) * 100 if total else 0

    c1,c2,c3 = st.columns(3)

    c1.metric("Total de Tarefas", total)
    c2.metric("Atrasadas", atrasadas)
    c3.metric("Saúde do Projeto", f"{progresso:.1f}%")

    # gráfico

    if "Status" in df.columns:

        fig = px.pie(
            df,
            names="Status",
            title="Distribuição de Status"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ---------------------------
    # CHAT IA
    # ---------------------------

    st.subheader("🧠 Converse com o GPlan IA")

    SYSTEM_PROMPT = """
Você é o GPlan IA, um especialista em Gerenciamento de Projetos.

Você domina:

PMBOK
Scrum
Kanban
Lean Project Management
Gestão de riscos
Gestão de cronograma
Gestão de recursos

Seu papel é ajudar o gerente do projeto a tomar decisões.

Sempre:

analise os dados do projeto
identifique riscos
detecte gargalos
sugira planos de ação
responda como um consultor estratégico

Nunca responda superficialmente.
"""

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Pergunte qualquer coisa sobre o projeto"):

        st.session_state.messages.append(
            {"role":"user","content":prompt}
        )

        with st.chat_message("user"):
            st.write(prompt)

        # contexto dos dados
        contexto = df.head(50).to_string()

        pergunta = f"""
Dados do projeto:

{contexto}

Pergunta do gerente:

{prompt}

Analise os dados e responda.
"""

        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":SYSTEM_PROMPT},
                {"role":"user","content":pergunta}
            ]
        )

        texto = resposta.choices[0].message.content

        with st.chat_message("assistant"):
            st.write(texto)

        st.session_state.messages.append(
            {"role":"assistant","content":texto}
        )

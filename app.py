import streamlit as st
from core.agent import OrionAgent
from services.bi_service import generate_dashboard

st.set_page_config(page_title="ORION PMO AI", layout="wide")

st.title("🧠 ORION PMO AI - Head de Operações")

if "agent" not in st.session_state:
    st.session_state.agent = OrionAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.sidebar.header("Configuração")

project_name = st.sidebar.text_input("Nome do Projeto")
project_type = st.sidebar.selectbox("Tipo", ["Produção", "Serviço"])
deadline = st.sidebar.date_input("Prazo")

if st.sidebar.button("Gerar Planejamento"):
    response = st.session_state.agent.generate_plan(project_name, project_type, deadline)
    st.session_state.messages.append(("ORION", response))

if st.sidebar.button("Gerar BI"):
    st.session_state.show_dashboard = True

st.subheader("💬 Conversa Estratégica")

for role, msg in st.session_state.messages:
    st.write(f"**{role}:** {msg}")

user_input = st.text_input("Digite sua mensagem")

if user_input:
    response = st.session_state.agent.chat(user_input)
    st.session_state.messages.append(("Você", user_input))
    st.session_state.messages.append(("ORION", response))

if st.session_state.get("show_dashboard"):
    st.subheader("📊 Business Intelligence")
    generate_dashboard()

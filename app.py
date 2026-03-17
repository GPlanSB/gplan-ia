import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# Configuração Master
st.set_page_config(page_title="GPlan IA Master", page_icon="🧠", layout="wide")

# Visual Dark Profissional
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stButton>button { background-color: #4285F4; color: white; border-radius: 8px; }
    .stMetric { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# Ligar o Motor Gemini
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-pro')
except:
    st.error("Configure a GOOGLE_API_KEY nos Secrets do Streamlit!")
    st.stop()

# Memória e Dados
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    st.session_state.df = None

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("⚙️ GPlan Control")
    file = st.file_uploader("Subir Cronograma (Excel/CSV)", type=["xlsx", "csv"])
    if file:
        st.session_state.df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
        st.success("Dados integrados!")
    
    st.divider()
    st.subheader("⚡ Ações Rápidas")
    if st.button("🚨 Análise de Riscos"):
        st.session_state.prompt_automatico = "Analise os riscos deste projeto agora."
    if st.button("📋 Plano 5W2H"):
        st.session_state.prompt_automatico = "Gere um plano 5W2H para as pendências."

# --- PAINEL PRINCIPAL ---
st.title("🧠 GPlan IA — Copiloto Master")

# Dashboard (Só aparece se tiver arquivo)
if st.session_state.df is not None:
    df = st.session_state.df
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Tarefas", len(df))
    
    status_col = next((c for c in df.columns if 'status' in c.lower()), None)
    if status_col:
        atrasadas = len(df[df[status_col].str.contains("Atrasado|Late", case=False)])
        c2.metric("Atrasadas", atrasadas, delta_color="inverse")
        c3.metric("Saúde", f"{((len(df)-atrasadas)/len(df))*100:.1f}%")

st.divider()

# Histórico do Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrada de Texto
prompt_manual = st.chat_input("Comande o GPlan IA...")
final_prompt = getattr(st.session_state, 'prompt_automatico', prompt_manual)

if final_prompt:
    if hasattr(st.session_state, 'prompt_automatico'):
        del st.session_state.prompt_automatico

    st.session_state.messages.append({"role": "user", "content": final_prompt})
    with st.chat_message("user"):
        st.markdown(final_prompt)

    # Contexto para o Gemini
    contexto = ""
    if st.session_state.df is not None:
        contexto = f"Contexto do Projeto:\n{st.session_state.df.to_string()}\n\n"

    with st.chat_message("assistant"):
        with st.spinner("Gemini pensando..."):
            response = st.session_state.chat.send_message(f"{contexto} Usuário pergunta: {final_prompt}")
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

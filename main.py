"""
GPlan IA 4.0 — Enterprise Edition (Gemini 2.5 Flash)
Design Premium Minimalista + BI Automático + Botões Funcionais + Ícone Profissional SVG
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import json
import networkx as nx
import google.generativeai as genai
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="GPlan IA 4.0",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== VISUAL PREMIUM MINIMALISTA ======================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background: #0a0f1c;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    [data-testid="stSidebar"] {
        background: #111827;
        border-right: 1px solid #1f2937;
    }
    
    h1, h2, h3 {
        font-weight: 700;
        color: #60a5fa;
        margin: 0.5rem 0;
    }
    
    .stMetric {
        background: #1f2937;
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #334155;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        transition: transform 0.3s;
    }
    
    .stMetric:hover {
        transform: translateY(-4px);
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #1e40af, #3b82f6);
        border: none;
        border-radius: 12px;
        font-weight: 600;
        padding: 14px;
        margin: 10px 0;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(59,130,246,0.4);
    }
    
    .header-container {
        text-align: center;
        padding: 2rem 0 1rem;
    }
    
    .header-svg {
        width: 80px;
        height: 80px;
        margin-bottom: 0.5rem;
    }
    
    .chat-container [data-testid="stChatMessage"] {
        background: #1f2937 !important;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 1.2rem;
        margin: 1rem 0;
    }
    
    .stChatInput > div > div > textarea {
        background: #1f2937;
        color: #e2e8f0;
        border: 1px solid #334155;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Ícone profissional SVG (estilo Grok-like: cérebro abstrato minimalista, olhando pra frente, em azul ciano)
GROK_ICON_SVG = """
<svg class="header-svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#60a5fa"/>
      <stop offset="100%" style="stop-color:#3b82f6"/>
    </linearGradient>
  </defs>
  <!-- Círculo base (cabeça) -->
  <circle cx="50" cy="50" r="42" fill="none" stroke="url(#grad)" stroke-width="6" opacity="0.9"/>
  <!-- Olhos minimalistas (olhando pra frente) -->
  <circle cx="38" cy="42" r="6" fill="#60a5fa"/>
  <circle cx="62" cy="42" r="6" fill="#60a5fa"/>
  <!-- Cérebro abstrato / circuitos -->
  <path d="M30 55 Q50 70 70 55 M35 60 Q50 80 65 60" stroke="#60a5fa" stroke-width="5" fill="none" opacity="0.7"/>
  <path d="M40 65 Q50 50 60 65" stroke="#3b82f6" stroke-width="4" fill="none"/>
</svg>
"""

# ====================== GEMINI ======================
@st.cache_resource
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key: return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction="""Você é o GPlan IA 4.0, assistente sênior de gestão de projetos. 
Responda em português brasileiro profissional, detalhado e estruturado. 
Use tabelas, listas e insights acionáveis baseados em PMBOK/Scrum."""
    )

gemini_model = init_gemini()

# Estado
if "df" not in st.session_state: st.session_state.df = None
if "column_map" not in st.session_state: st.session_state.column_map = {}
if "project_name" not in st.session_state: st.session_state.project_name = "Projeto"
if "messages" not in st.session_state: st.session_state.messages = []

# Funções dashboard (igual anterior, mas limpa)
def calcular_caminho_critico(df, col_map):
    if df is None or df.empty: return {"caminho": []}
    G = nx.DiGraph()
    for _, row in df.iterrows():
        tarefa = str(row.get(col_map.get('tarefa'), ''))
        if not tarefa: continue
        G.add_node(tarefa)
        preds = str(row.get(col_map.get('predecessores', ''), '')).split(',')
        for p in [x.strip() for x in preds if x.strip()]:
            if p in df[col_map.get('tarefa', pd.Series())].astype(str).values:
                G.add_edge(p, tarefa)
    try:
        return {"caminho": nx.dag_longest_path(G)}
    except:
        return {"caminho": []}

def gerar_dashboard(df, col_map):
    if df is None or df.empty: return
    cp = calcular_caminho_critico(df, col_map)
    atrasadas = len(df[df[col_map['status']].astype(str).str.contains("atrasado|late|pendente", case=False, na=False)])
    total = len(df)
    saude = round(100 - (atrasadas / total * 100) if total > 0 else 0, 1)
    
    cols = st.columns(4)
    cols[0].metric("Total Tarefas", total)
    cols[1].metric("Caminho Crítico", len(cp['caminho']))
    cols[2].metric("Atrasadas", atrasadas, delta=f"-{atrasadas}")
    cols[3].metric("Saúde", f"{saude}%")
    
    c1, c2 = st.columns([3,2])
    with c1:
        fig = px.timeline(df.assign(Start=pd.to_datetime(df[col_map['inicio']]), Finish=pd.to_datetime(df[col_map['fim']])),
                          x_start="Start", x_end="Finish", y=col_map['tarefa'], color=col_map.get('status'))
        fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        fig_pie = px.pie(df, names=col_map['status'], color_discrete_sequence=px.colors.sequential.Blues)
        fig_pie.update_layout(template="plotly_dark", height=380)
        st.plotly_chart(fig_pie, use_container_width=True)

# SIDEBAR
with st.sidebar:
    st.markdown(GROK_ICON_SVG, unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; margin-top:-10px;'>GPlan IA</h2>", unsafe_allow_html=True)
    
    uploaded = st.file_uploader("Cronograma", type=["xlsx","csv"])
    
    if uploaded:
        try:
            df = pd.read_excel(uploaded) if 'xlsx' in uploaded.name.lower() else pd.read_csv(uploaded)
            st.session_state.df = df
            st.success("Carregado")
            
            cols = list(df.columns)
            st.session_state.column_map = {
                'tarefa': st.selectbox("Tarefa", cols, index=0),
                'inicio': st.selectbox("Início", cols, index=0),
                'fim': st.selectbox("Fim", cols, index=0),
                'status': st.selectbox("Status", cols, index=0),
                'responsavel': st.selectbox("Responsável", cols, index=0),
                'predecessores': st.selectbox("Predecessores", [""] + cols),
            }
        except: st.error("Erro ao ler arquivo")
    
    if st.session_state.df is not None:
        st.markdown("### Ações Rápidas")
        if st.button("Análise de Riscos"):
            st.session_state.messages.append({"role": "user", "content": "Faça análise completa de riscos do projeto atual."})
            st.rerun()
        if st.button("Relatório Métricas"):
            st.session_state.messages.append({"role": "user", "content": "Gere relatório de métricas e saúde do projeto."})
            st.rerun()
        if st.button("Plano 5W2H Recuperação"):
            st.session_state.messages.append({"role": "user", "content": "Monte plano 5W2H para tarefas atrasadas."})
            st.rerun()
        if st.button("Resumo Executivo"):
            st.session_state.messages.append({"role": "user", "content": "Crie resumo executivo para diretoria."})
            st.rerun()

# MAIN
st.markdown('<div style="text-align:center;">' + GROK_ICON_SVG + '<h1>GPlan IA 4.0</h1></div>', unsafe_allow_html=True)

if st.session_state.df is not None:
    gerar_dashboard(st.session_state.df, st.session_state.column_map)
    st.divider()
    st.subheader("Assistente")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Pergunte..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    if gemini_model and st.session_state.df is not None:
        with st.chat_message("assistant"):
            with st.spinner("..."):
                try:
                    chat = gemini_model.start_chat(history=[{"role": "user" if m["role"]=="user" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]])
                    contexto = f"Dados: {st.session_state.df.head(6).to_string()}"
                    resp = chat.send_message(f"{contexto}\nPergunta: {prompt}")
                    answer = resp.text
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e: st.error(str(e))
    else:
        st.warning("Carregue cronograma primeiro.")

st.caption("GPlan IA 4.0 • Premium • 2026")

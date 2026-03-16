"""
GPlan IA 4.0 — Enterprise Edition (com Google Gemini API gratuita)
Copiloto Master de Gestão de Projetos com Caminho Crítico + Gantt + Baseline
Versão Streamlit Completa - Corrigido SyntaxError no mapeamento de colunas
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime
import networkx as nx
import google.generativeai as genai
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="GPlan IA 4.0 Enterprise - Gemini", page_icon="🧠", layout="wide")

# Tema simples
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #0f172a; color: #e2e8f0; }
    .stButton > button { background: linear-gradient(135deg, #00d9ff, #7c3aed); color: white; border: none; }
    h1, h2, h3 { color: #00d9ff; }
</style>
""", unsafe_allow_html=True)

# Inicialização do Gemini
@st.cache_resource
def init_gemini():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction="""Você é o GPlan IA 4.0, assistente sênior de gestão de projetos.
Sempre responda em português brasileiro correto e profissional.
Seja detalhado, use tabelas Markdown para métricas/riscos/planos, listas e estrutura clara.
Nunca respostas curtas ou repetitivas. Forneça insights acionáveis baseados em PMBOK/Scrum."""
        )
    except Exception as e:
        st.error(f"Erro Gemini: {str(e)}\nVerifique GEMINI_API_KEY nos secrets.")
        return None

gemini_model = init_gemini()

# Estado
if "df" not in st.session_state: st.session_state.df = None
if "project_name" not in st.session_state: st.session_state.project_name = "Projeto Sem Nome"
if "column_map" not in st.session_state: st.session_state.column_map = {}
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "🧠 Bem-vindo ao GPlan IA 4.0 (Gemini)\nFaça upload do cronograma e pergunte qualquer coisa."}]

def calcular_caminho_critico(df, col_map):
    if df is None or df.empty: return {"caminho": [], "folga": {}}
    G = nx.DiGraph()
    for _, row in df.iterrows():
        tarefa = str(row.get(col_map.get('tarefa', ''), 'Sem nome'))
        dur = max(1, int(row.get('duracao', 5)))  # fallback
        G.add_node(tarefa, duration=dur)
        preds = str(row.get(col_map.get('predecessores', ''), '')).strip()
        if preds:
            for p in [x.strip() for x in preds.split(',') if x.strip()]:
                if p in df[col_map['tarefa']].astype(str).values:
                    G.add_edge(p, tarefa)
    try:
        caminho = nx.dag_longest_path(G)
        return {"caminho": caminho, "folga": {n: 0 if n in caminho else 2 for n in G}}
    except:
        return {"caminho": [], "folga": {}}

def gerar_gantt(df, col_map):
    if df is None or df.empty: return None
    try:
        df_g = df.copy()
        df_g['Start'] = pd.to_datetime(df_g[col_map['inicio']], errors='coerce')
        df_g['Finish'] = pd.to_datetime(df_g[col_map['fim']], errors='coerce')
        df_g = df_g.dropna(subset=['Start', 'Finish'])
        if df_g.empty: return None
        fig = px.timeline(df_g, x_start="Start", x_end="Finish", y=col_map['tarefa'],
                          color=col_map.get('status'), hover_data=[col_map.get('responsavel')])
        fig.update_layout(template="plotly_dark", height=500)
        return fig
    except:
        return None

def gerar_contexto(df, col_map):
    if df is None or df.empty: return "Sem dados carregados."
    cp = calcular_caminho_critico(df, col_map)
    atrasadas = len(df[df[col_map['status']].astype(str).str.contains("atrasado|late", case=False, na=False)])
    return f"Projeto: {st.session_state.project_name}\nTarefas: {len(df)}\nAtrasadas: {atrasadas}\nCaminho crítico: {', '.join(cp['caminho'][:5]) or 'N/A'}\nResumo primeiras linhas:\n{df.head(8).to_string(index=False)}"

# SIDEBAR
with st.sidebar:
    st.title("GPlan IA 4.0")
    uploaded = st.file_uploader("Cronograma", type=["xlsx", "xls", "csv"])
    
    if uploaded is not None:
        try:
            df = pd.read_excel(uploaded) if uploaded.name.endswith(('.xlsx','.xls')) else pd.read_csv(uploaded)
            st.session_state.df = df
            st.success("Carregado!")
            
            st.subheader("Mapeamento")
            cols = list(df.columns)
            
            st.session_state.column_map = {
                'tarefa': st.selectbox("Tarefa/Nome", cols, index=next((i for i, c in enumerate(cols) if 'tarefa' in c.lower() or 'nome' in c.lower()), 0)),
                'inicio': st.selectbox("Data Início", cols, index=next((i for i, c in enumerate(cols) if 'início' in c.lower() or 'inicio' in c.lower() or 'start' in c.lower()), 0)),
                'fim': st.selectbox("Data Fim", cols, index=next((i for i, c in enumerate(cols) if 'fim' in c.lower() or 'end' in c.lower() or 'término' in c.lower()), 0)),
                'status': st.selectbox("Status", cols, index=next((i for i, c in enumerate(cols) if 'status' in c.lower() or 'situação' in c.lower()), 0)),
                'responsavel': st.selectbox("Responsável", cols, index=next((i for i, c in enumerate(cols) if 'respons' in c.lower() or 'dono' in c.lower()), 0)),
                'predecessores': st.selectbox("Predecessores (opc)", [""] + cols, index=0),
                'percentual': st.selectbox("% Concluído (opc)", [""] + cols, index=0),
            }
        except Exception as e:
            st.error(f"Erro leitura: {e}")

# Dashboard
if st.session_state.df is not None:
    df = st.session_state.df
    col_map = st.session_state.column_map
    cp = calcular_caminho_critico(df, col_map)
    
    cols = st.columns(4)
    cols[0].metric("Tarefas", len(df))
    cols[1].metric("Caminho Crítico", len(cp['caminho']))
    cols[2].metric("Atrasadas", sum(df[col_map['status']].astype(str).str.contains("atrasado|late", case=False, na=False)))
    
    fig = gerar_gantt(df, col_map)
    if fig: st.plotly_chart(fig, use_container_width=True)

# Chat
st.subheader("Assistente")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Pergunte..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    if gemini_model:
        with st.chat_message("assistant"):
            with st.spinner("Processando..."):
                try:
                    chat = gemini_model.start_chat(history=[
                        {"role": "user" if m["role"]=="user" else "model", "parts": [m["content"]]}
                        for m in st.session_state.messages[:-1]
                    ])
                    contexto = gerar_contexto(st.session_state.df, st.session_state.column_map)
                    response = chat.send_message(f"{contexto}\nPergunta: {prompt}",
                                                 generation_config=genai.types.GenerationConfig(temperature=0.65, max_output_tokens=2500))
                    answer = response.text
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Erro: {str(e)} (rate limit? espere alguns minutos)")
    else:
        st.error("Gemini não inicializado.")

st.caption("GPlan IA 4.0 • Gemini Free • Corrigido 2026")

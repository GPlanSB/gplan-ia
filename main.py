"""
GPlan IA 4.0 — Enterprise Edition (com Google Gemini API gratuita)
Atualizado março 2026: modelo corrigido para gemini-2.5-flash
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

# Tema
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #0f172a; color: #e2e8f0; }
    .stButton > button { background: linear-gradient(135deg, #00d9ff, #7c3aed); color: white; border: none; }
    h1, h2, h3 { color: #00d9ff; }
</style>
""", unsafe_allow_html=True)

# Gemini init - MODELO ATUALIZADO
@st.cache_resource
def init_gemini():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada nos secrets")
        genai.configure(api_key=api_key)
        
        return genai.GenerativeModel(
            model_name='gemini-2.5-flash',  # ← Correção aqui! (ou 'gemini-2.5-flash-lite')
            system_instruction="""Você é o GPlan IA 4.0, assistente sênior de gestão de projetos.
Sempre responda em português brasileiro correto e profissional.
Seja detalhado, use tabelas Markdown para métricas/riscos/planos 5W2H, listas e estrutura clara.
Nunca respostas curtas ou repetitivas. Forneça insights acionáveis baseados em PMBOK/Scrum/Kanban."""
        )
    except Exception as e:
        st.error(f"Erro ao inicializar Gemini: {str(e)}\nVerifique a chave API nos secrets e se o modelo está disponível na sua região.")
        return None

gemini_model = init_gemini()

# Estado da sessão
if "df" not in st.session_state: st.session_state.df = None
if "project_name" not in st.session_state: st.session_state.project_name = "Projeto Sem Nome"
if "column_map" not in st.session_state: st.session_state.column_map = {}
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "🧠 Bem-vindo ao GPlan IA 4.0 (Gemini 2.5 Flash)\nFaça upload do cronograma e pergunte qualquer coisa sobre riscos, caminho crítico, métricas etc."}]

# Funções (mantidas, com robustez)
def calcular_caminho_critico(df, col_map):
    if df is None or df.empty: return {"caminho": [], "folga": {}}
    G = nx.DiGraph()
    for _, row in df.iterrows():
        tarefa = str(row.get(col_map.get('tarefa', ''), 'Sem nome'))
        dur = max(1, int(row.get('duracao', row.get('duração', 5))))
        G.add_node(tarefa, duration=dur)
        preds = str(row.get(col_map.get('predecessores', ''), '')).strip()
        if preds:
            for p in [x.strip() for x in preds.split(',') if x.strip()]:
                if p in df[col_map.get('tarefa', 'Tarefa')].astype(str).values:
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
        fig.update_layout(template="plotly_dark", height=500, title="Diagrama de Gantt")
        return fig
    except Exception as e:
        st.warning(f"Gantt não gerado: {e}")
        return None

def gerar_contexto(df, col_map):
    if df is None or df.empty: return "Sem dados carregados."
    cp = calcular_caminho_critico(df, col_map)
    atrasadas = len(df[df[col_map['status']].astype(str).str.contains(r"atrasado|atraso|late", case=False, na=False)])
    return f"Projeto: {st.session_state.project_name}\nTotal tarefas: {len(df)}\nAtrasadas: {atrasadas}\nCaminho crítico (top 5): {', '.join(cp['caminho'][:5]) or 'N/A'}\nResumo:\n{df.head(8).to_string(index=False)}"

# SIDEBAR
with st.sidebar:
    st.title("GPlan IA 4.0")
    uploaded = st.file_uploader("Cronograma (Excel/CSV)", type=["xlsx", "xls", "csv"])
    
    if uploaded is not None:
        try:
            df = pd.read_excel(uploaded) if uploaded.name.lower().endswith(('.xlsx', '.xls')) else pd.read_csv(uploaded)
            st.session_state.df = df
            st.success("✅ Carregado!")
            
            st.subheader("Mapeamento de Colunas")
            cols = list(df.columns)
            
            st.session_state.column_map = {
                'tarefa': st.selectbox("Tarefa/Nome", cols, index=next((i for i, c in enumerate(cols) if any(k in c.lower() for k in ['tarefa', 'nome', 'task', 'atividade'])), 0)),
                'inicio': st.selectbox("Início", cols, index=next((i for i, c in enumerate(cols) if any(k in c.lower() for k in ['início', 'inicio', 'start', 'data início'])), 0)),
                'fim': st.selectbox("Fim", cols, index=next((i for i, c in enumerate(cols) if any(k in c.lower() for k in ['fim', 'end', 'término', 'data fim'])), 0)),
                'status': st.selectbox("Status", cols, index=next((i for i, c in enumerate(cols) if any(k in c.lower() for k in ['status', 'situação', 'estado'])), 0)),
                'responsavel': st.selectbox("Responsável", cols, index=next((i for i, c in enumerate(cols) if any(k in c.lower() for k in ['respons', 'dono', 'owner', 'responsável'])), 0)),
                'predecessores': st.selectbox("Predecessores (opc)", [""] + cols, index=0),
                'percentual': st.selectbox("% Concluído (opc)", [""] + cols, index=0),
            }
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

# Dashboard
if st.session_state.df is not None:
    df = st.session_state.df
    col_map = st.session_state.column_map
    cp = calcular_caminho_critico(df, col_map)
    
    cols = st.columns(4)
    cols[0].metric("Tarefas", len(df))
    cols[1].metric("Caminho Crítico", len(cp['caminho']))
    cols[2].metric("Atrasadas (aprox)", sum(df[col_map['status']].astype(str).str.contains(r"atrasado|late", case=False, na=False)))
    
    fig = gerar_gantt(df, col_map)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

# Chat
st.subheader("💬 Assistente Inteligente")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Pergunte sobre o projeto..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    if gemini_model is None:
        st.error("Gemini não inicializado — verifique a chave API.")
    else:
        with st.chat_message("assistant"):
            with st.spinner("Gemini analisando..."):
                try:
                    chat = gemini_model.start_chat(history=[
                        {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
                        for m in st.session_state.messages[:-1]
                    ])
                    contexto = gerar_contexto(st.session_state.df, st.session_state.column_map)
                    response = chat.send_message(
                        f"{contexto}\n\nPergunta: {prompt}",
                        generation_config=genai.types.GenerationConfig(temperature=0.65, max_output_tokens=2500)
                    )
                    answer = response.text
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    err = str(e).lower()
                    if "404" in err or "not found" in err:
                        st.error("Modelo não encontrado (404). Verifique se 'gemini-2.5-flash' está disponível na sua conta/região. Tente 'gemini-2.5-flash-lite'.")
                    elif "429" in err:
                        st.error("Limite do free tier atingido. Espere 1-5 minutos.")
                    else:
                        st.error(f"Erro: {str(e)}")

st.caption("GPlan IA 4.0 • Atualizado para Gemini 2.5 Flash • Free Tier • Março 2026")

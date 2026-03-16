"""
GPlan IA 4.0 — Enterprise Edition (Correção de Engenharia)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import networkx as nx
import google.generativeai as genai
import warnings

warnings.filterwarnings("ignore")

# --- CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="GPlan IA 4.0", page_icon="📊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background: #0a0f1c; color: #e2e8f0; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background: #111827; border-right: 1px solid #1f2937; }
    h1, h2, h3 { font-weight: 700; color: #60a5fa; }
    .stMetric { background: #1f2937; border-radius: 16px; padding: 1.5rem; border: 1px solid #334155; }
    .stButton > button { width: 100%; background: linear-gradient(135deg, #1e40af, #3b82f6); border: none; border-radius: 12px; color: white; font-weight: 600; padding: 10px; transition: 0.3s; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(59,130,246,0.3); color: white; }
</style>
""", unsafe_allow_html=True)

# --- ENGINE CORE ---

@st.cache_resource
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key: 
        st.error("Erro: GEMINI_API_KEY não encontrada nos Secrets.")
        return None
    genai.configure(api_key=api_key)
    # Gemini 2.5 Flash ainda não existe em 2024/25, corrigido para 1.5 Flash ou Pro (ou o que estiver disponível)
    return genai.GenerativeModel(
        model_name='gemini-1.5-flash', 
        system_instruction="Você é GPlan IA 4.0, assistente sênior de projetos. Responda em PT-BR com insights técnicos e tabelas Markdown."
    )

def fix_dates(df, col):
    """Função robusta de parsing de data para evitar crash no Plotly"""
    if col not in df.columns:
        return None
    # Converte para datetime forçando erros para NaT
    temp_col = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
    # Tenta formatos alternativos se houver falha crítica
    if temp_col.isna().all():
        temp_col = pd.to_datetime(df[col], errors='coerce', infer_datetime_format=True)
    return temp_col

def calcular_caminho_critico(df, col_map):
    if df is None or df.empty or not col_map.get('predecessores'): return []
    G = nx.DiGraph()
    try:
        for _, row in df.iterrows():
            tarefa = str(row[col_map['tarefa']])
            G.add_node(tarefa)
            preds = str(row.get(col_map['predecessores'], '')).split(',')
            for p in [x.strip() for x in preds if x.strip() and x != 'nan']:
                if p in df[col_map['tarefa']].astype(str).values:
                    G.add_edge(p, tarefa)
        return nx.dag_longest_path(G)
    except:
        return []

# --- ESTADO DA SESSÃO ---
if "df" not in st.session_state: st.session_state.df = None
if "messages" not in st.session_state: st.session_state.messages = []
if "action_trigger" not in st.session_state: st.session_state.action_trigger = None

model = init_gemini()

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configurações")
    uploaded = st.file_uploader("Upload do Cronograma", type=["xlsx", "csv"])
    
    if uploaded:
        if st.session_state.df is None:
            df = pd.read_excel(uploaded) if 'xlsx' in uploaded.name else pd.read_csv(uploaded)
            st.session_state.df = df
        
        cols = list(st.session_state.df.columns)
        st.session_state.column_map = {
            'tarefa': st.selectbox("Coluna Tarefa", cols, index=0),
            'inicio': st.selectbox("Coluna Início", cols, index=1 if len(cols)>1 else 0),
            'fim': st.selectbox("Coluna Fim", cols, index=2 if len(cols)>2 else 0),
            'status': st.selectbox("Coluna Status", cols, index=3 if len(cols)>3 else 0),
            'responsavel': st.selectbox("Responsável", cols, index=0),
            'predecessores': st.selectbox("Predecessores", [""] + cols)
        }

    st.markdown("---")
    st.subheader("🚀 Ações Rápidas")
    # Botões agora setam um trigger para serem processados na main
    if st.button("🚨 Análise de Riscos"): st.session_state.action_trigger = "Faça uma análise de riscos detalhada deste projeto."
    if st.button("📊 Relatório de Métricas"): st.session_state.action_trigger = "Gere um relatório de métricas e performance."
    if st.button("📉 Plano 5W2H"): st.session_state.

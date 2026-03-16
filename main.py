"""
GPlan IA 4.0 — Enterprise Edition (com Google Gemini API gratuita)
Copiloto Master de Gestão de Projetos com Caminho Crítico + Gantt + Baseline
Versão Streamlit Completa (Arquivo Único) - Atualizado para Gemini Free Tier
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import json
from datetime import datetime
import networkx as nx
import numpy as np
from typing import Dict, Any, Optional
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="GPlan IA 4.0 Enterprise - Gemini", page_icon="🧠", layout="wide")

# ========================== THEME PREMIUM (mantido) ==========================
THEME_COLORS = {
    "primary": "#00D9FF", "secondary": "#7C3AED", "success": "#10B981",
    "warning": "#F59E0B", "danger": "#EF4444", "dark_bg": "#0F172A",
    "card_bg": "#1E293B", "border": "#334155"
}

st.markdown(f"""
<style>
    [data-testid="stAppViewContainer"] {{ background: linear-gradient(135deg, {THEME_COLORS['dark_bg']} 0%, #1a1f3a 100%); }}
    .stButton > button {{ background: linear-gradient(135deg, {THEME_COLORS['primary']} 0%, {THEME_COLORS['secondary']} 100%); color: white; }}
</style>
""", unsafe_allow_html=True)

# ========================== CONFIG GEMINI (substitui OpenAI) ==========================
@st.cache_resource
def init_gemini():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY não configurada nos secrets")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.5-flash')  # modelo gratuito mais comum em 2026
    except Exception as e:
        st.error(f"❌ Erro ao inicializar Gemini: {str(e)}")
        st.info("1. Pegue sua chave gratuita em https://aistudio.google.com/app/apikey\n2. Adicione GEMINI_API_KEY nos secrets do app no Streamlit Cloud")
        return None

gemini_model = init_gemini()

# ========================== ESTADO DA APLICAÇÃO ==========================
if "df" not in st.session_state: st.session_state.df = None
if "project_name" not in st.session_state: st.session_state.project_name = "Meu Projeto"
if "column_map" not in st.session_state: st.session_state.column_map = {}
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "🧠 **GPlan IA 4.0 com Gemini Free** carregado!\n\nAgora usando Google Gemini (gratuito) para análises inteligentes."}]

# ========================== FUNÇÕES CORE (mantidas) ==========================
def calcular_caminho_critico(df: pd.DataFrame, map_col: dict) -> Dict:
    if df is None or len(df) == 0:
        return {"caminho_critico": [], "folga": {}}
    
    G = nx.DiGraph()
    for _, row in df.iterrows():
        task = str(row[map_col['tarefa']])
        dur = max(1, int(row.get(map_col.get('duracao', ''), 5)))  # fallback
        G.add_node(task, duration=dur)
        
        preds_str = str(row.get(map_col.get('predecessores', ''), ''))
        preds = [p.strip() for p in preds_str.split(',') if p.strip()]
        for p in preds:
            if p in df[map_col['tarefa']].astype(str).values:
                G.add_edge(p, task)
    
    try:
        critical_path = nx.dag_longest_path(G)
        folga = {task: 0 if task in critical_path else 2 for task in G.nodes()}  # simplificado
        return {"caminho_critico": critical_path, "folga": folga}
    except:
        return {"caminho_critico": [], "folga": {}}

def gerar_gantt(df: pd.DataFrame, map_col: dict):
    df_gantt = df.copy()
    df_gantt['Start'] = pd.to_datetime(df_gantt[map_col['inicio']], errors='coerce')
    df_gantt['Finish'] = pd.to_datetime(df_gantt[map_col['fim']], errors='coerce')
    df_gantt['Task'] = df_gantt[map_col['tarefa']]
    
    fig = px.timeline(df_gantt, x_start="Start", x_end="Finish", y="Task",
                      color=map_col['status'], hover_data=[map_col['responsavel']])
    fig.update_layout(template="plotly_dark", height=600, title="Diagrama de Gantt")
    return fig

def gerar_contexto_inteligente(df: pd.DataFrame, map_col: dict) -> str:
    if df is None or len(df) == 0:
        return "Nenhum projeto carregado ainda."
    
    cp = calcular_caminho_critico(df, map_col)
    metricas = {
        "total_tarefas": len(df),
        "caminho_critico_tamanho": len(cp['caminho_critico']),
        "tarefas_criticas": ', '.join(cp['caminho_critico'][:5]) or "Nenhum detectado"
    }
    
    return f"""
PROJETO ATUAL: {st.session_state.project_name}
MÉTRICAS GERAIS: {json.dumps(metricas, ensure_ascii=False)}
CAMINHO CRÍTICO: {metricas['tarefas_criticas']}
PRIMEIRAS LINHAS DOS DADOS (resumo):
{df.head(10).to_string(index=False)}
Use esses dados para análises precisas de riscos, métricas e planos de ação.
"""

# ========================== SIDEBAR ==========================
with st.sidebar:
    st.title("🧠 GPlan IA 4.0")
    st.caption("Enterprise com Gemini Free")
    
    uploaded = st.file_uploader("Upload Cronograma (Excel/CSV)", type=["xlsx","csv","xls"])
    
    if uploaded:
        try:
            df = pd.read_excel(uploaded) if uploaded.name.endswith(('.xlsx','.xls')) else pd.read_csv(uploaded)
            st.session_state.df = df
            st.success("✅ Projeto carregado!")
            
            st.subheader("🔗 Mapeamento de Colunas")
            cols = list(df.columns)
            defaults = {k: cols.index(v) if v in cols else 0 for k,v in {'tarefa':'Tarefa', 'inicio':'Início', 'fim':'Fim', 'status':'Status', 'responsavel':'Responsável'}.items()}
            
            st.session_state.column_map = {
                'tarefa': st.selectbox("Tarefa / Nome", cols, index=defaults.get('tarefa', 0)),
                'inicio': st.selectbox("Data Início", cols, index=defaults.get('inicio', 0)),
                'fim': st.selectbox("Data Fim", cols, index=defaults.get('fim', 0)),
                'status': st.selectbox("Status", cols, index=defaults.get('status', 0)),
                'responsavel': st.selectbox("Responsável", cols, index=defaults.get('responsavel', 0)),
                'predecessores': st.selectbox("Predecessores (opc)", [""] + cols, index=0),
                'percentual': st.selectbox("% Concluído (opc)", [""] + cols, index=0),
                'baseline_fim': st.selectbox("Baseline Fim (opc)", [""] + cols, index=0),
            }
            
            st.session_state.project_name = st.text_input("Nome do Projeto", st.session_state.project_name)
            
            if st.button("💾 Salvar Projeto (.gplan)"):
                data = {"name": st.session_state.project_name, "df": df.to_json(orient="records"), "map": st.session_state.column_map}
                st.download_button("Baixar", json.dumps(data, ensure_ascii=False), f"{st.session_state.project_name}.gplan", "application/json")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

# ========================== DASHBOARD PRINCIPAL ==========================
if st.session_state.df is not None:
    df = st.session_state.df
    map_col = st.session_state.column_map
    
    st.header(f"📊 {st.session_state.project_name}")
    
    cp = calcular_caminho_critico(df, map_col)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tarefas", len(df))
    col2.metric("Caminho Crítico", len(cp['caminho_critico']))
    col3.metric("Atrasadas (aprox)", len(df[df[map_col['status']].astype(str).str.contains("atrasado|late", case=False, na=False)]))
    col4.metric("Saúde Estimada", "Calculando...")
    
    st.plotly_chart(gerar_gantt(df, map_col), use_container_width=True)

# ========================== CHAT COM GEMINI ==========================
st.subheader("💬 Assistente Inteligente (Gemini Free)")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Pergunte sobre o projeto..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    if not gemini_model:
        st.error("Gemini não inicializado. Verifique a chave API nos secrets.")
    else:
        with st.chat_message("assistant"):
            with st.spinner("Gemini analisando..."):
                try:
                    contexto = gerar_contexto_inteligente(st.session_state.df, st.session_state.column_map)
                    full_prompt = f"{contexto}\n\nPergunta do usuário: {prompt}\n\nResponda em português brasileiro, use tabelas quando útil, seja analítico e proativo em gestão de projetos."
                    
                    # Histórico simples (Gemini nativo não tem chat state built-in como OpenAI, então concatenamos)
                    chat_history = [{"role": "user" if m["role"]=="user" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
                    
                    response = gemini_model.generate_content(
                        chat_history + [{"role": "user", "parts": [full_prompt]}],
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.7,
                            max_output_tokens=1500
                        )
                    )
                    
                    answer = response.text
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "rate limit" in error_msg.lower():
                        st.error("⚠️ Limite do Gemini atingido (rate limit). Espere alguns minutos e tente novamente. O free tier tem ~5-15 req/min e limites diários.")
                    else:
                        st.error(f"❌ Erro no Gemini: {error_msg}")

# ========================== RODAPÉ ==========================
st.divider()
st.caption("GPlan IA 4.0 • Atualizado para Google Gemini API Free Tier • Sem custos com OpenAI • © 2026")

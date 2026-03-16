"""
GPlan IA 4.0 — Enterprise Edition (Gemini 2.5 Flash)
Gantt corrigido com parsing robusto de datas + Ícone Profissional SVG
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

# ====================== VISUAL PREMIUM ======================
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
    
    h1, h2, h3 { font-weight: 700; color: #60a5fa; margin: 0.5rem 0; }
    
    .stMetric {
        background: #1f2937;
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #334155;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
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
    
    .header-svg {
        width: 80px;
        height: 80px;
        margin: 1rem auto 0.5rem;
        display: block;
    }
    
    [data-testid="stChatMessage"] {
        background: #1f2937 !important;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 1.2rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Ícone SVG profissional tech (cérebro abstrato + circuito, sem carinha)
PROFESSIONAL_ICON_SVG = """
<svg class="header-svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#60a5fa"/>
      <stop offset="100%" stop-color="#3b82f6"/>
    </linearGradient>
  </defs>
  <circle cx="50" cy="50" r="38" fill="none" stroke="url(#grad)" stroke-width="5"/>
  <path d="M35 40 Q50 25 65 40 M35 60 Q50 75 65 60" stroke="url(#grad)" stroke-width="4" fill="none"/>
  <path d="M30 50 Q50 40 70 50 Q50 60 30 50" stroke="#60a5fa" stroke-width="3" fill="none" opacity="0.8"/>
  <circle cx="50" cy="50" r="8" fill="#1f2937" stroke="#60a5fa" stroke-width="2"/>
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
        system_instruction="Você é GPlan IA 4.0, assistente sênior de projetos. Responda em PT-BR profissional, detalhado, com tabelas e insights acionáveis."
    )

gemini_model = init_gemini()

# Estado
if "df" not in st.session_state: st.session_state.df = None
if "column_map" not in st.session_state: st.session_state.column_map = {}
if "project_name" not in st.session_state: st.session_state.project_name = "Projeto"
if "messages" not in st.session_state: st.session_state.messages = []

# Funções
def calcular_caminho_critico(df, col_map):
    if df is None or df.empty: return {"caminho": []}
    G = nx.DiGraph()
    for _, row in df.iterrows():
        tarefa = str(row.get(col_map.get('tarefa', ''), ''))
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

def gerar_gantt(df, col_map):
    if df is None or df.empty: return None
    
    start_col = col_map.get('inicio')
    end_col = col_map.get('fim')
    
    if start_col not in df.columns or end_col not in df.columns:
        st.warning("Colunas de início ou fim não encontradas no mapeamento.")
        return None
    
    dfg = df.copy()
    
    # Tentativa 1: parsing automático com dayfirst (prioridade BR)
    dfg['Start'] = pd.to_datetime(dfg[start_col], errors='coerce', dayfirst=True)
    dfg['Finish'] = pd.to_datetime(dfg[end_col], errors='coerce', dayfirst=True)
    
    # Tentativa 2: format explícito dd/mm/yyyy
    mask_start_invalid = dfg['Start'].isna()
    mask_end_invalid = dfg['Finish'].isna()
    if mask_start_invalid.any():
        dfg.loc[mask_start_invalid, 'Start'] = pd.to_datetime(dfg.loc[mask_start_invalid, start_col], format='%d/%m/%Y', errors='coerce')
    if mask_end_invalid.any():
        dfg.loc[mask_end_invalid, 'Finish'] = pd.to_datetime(dfg.loc[mask_end_invalid, end_col], format='%d/%m/%Y', errors='coerce')
    
    # Tentativa 3: formato americano m/d/y (fallback)
    mask_start_invalid = dfg['Start'].isna()
    mask_end_invalid = dfg['Finish'].isna()
    if mask_start_invalid.any():
        dfg.loc[mask_start_invalid, 'Start'] = pd.to_datetime(dfg.loc[mask_start_invalid, start_col], format='%m/%d/%Y', errors='coerce')
    if mask_end_invalid.any():
        dfg.loc[mask_end_invalid, 'Finish'] = pd.to_datetime(dfg.loc[mask_end_invalid, end_col], format='%m/%d/%Y', errors='coerce')
    
    # Remove linhas sem datas válidas
    dfg = dfg.dropna(subset=['Start', 'Finish'])
    
    if dfg.empty:
        st.warning("""
        Nenhuma data válida encontrada nas colunas selecionadas.
        Verifique:
        • Formato deve ser dd/mm/aaaa (ex: 15/06/2025) ou mm/dd/yyyy
        • Sem textos como 'Pendente', 'N/A' ou células vazias nessas colunas
        • Selecione novamente as colunas corretas no mapeamento
        """)
        return None
    
    fig = px.timeline(dfg, x_start="Start", x_end="Finish", y=col_map['tarefa'],
                      color=col_map.get('status'), hover_data=[col_map.get('responsavel')])
    fig.update_layout(
        template="plotly_dark",
        height=520,
        margin=dict(l=0,r=0,t=30,b=0),
        xaxis_title="Período",
        yaxis_title="Tarefas"
    )
    return fig

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
        st.subheader("Diagrama de Gantt")
        fig = gerar_gantt(df, col_map)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Gantt não gerado — verifique colunas de datas")
    
    with c2:
        st.subheader("Distribuição de Status")
        if col_map['status'] in df.columns:
            fig_pie = px.pie(df, names=col_map['status'], color_discrete_sequence=px.colors.sequential.Blues)
            fig_pie.update_layout(template="plotly_dark", height=380)
            st.plotly_chart(fig_pie, use_container_width=True)

# SIDEBAR
with st.sidebar:
    st.markdown(PROFESSIONAL_ICON_SVG, unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; margin-top:-10px;'>GPlan IA</h2>", unsafe_allow_html=True)
    
    uploaded = st.file_uploader("Cronograma", type=["xlsx","csv"])
    
    if uploaded:
        try:
            df = pd.read_excel(uploaded) if 'xlsx' in uploaded.name.lower() else pd.read_csv(uploaded)
            st.session_state.df = df
            st.success("Carregado")
            
            cols = list(df.columns)
            st.session_state.column_map = {
                'tarefa': st.selectbox("Tarefa", cols, index=next((i for i,c in enumerate(cols) if 'tarefa' in c.lower() or 'nome' in c.lower() or 'atividade' in c.lower()), 0)),
                'inicio': st.selectbox("Início", cols, index=next((i for i,c in enumerate(cols) if 'início' in c.lower() or 'inicio' in c.lower() or 'start' in c.lower() or 'data início' in c.lower()), 0)),
                'fim': st.selectbox("Fim", cols, index=next((i for i,c in enumerate(cols) if 'fim' in c.lower() or 'end' in c.lower() or 'término' in c.lower() or 'data fim' in c.lower()), 0)),
                'status': st.selectbox("Status", cols, index=next((i for i,c in enumerate(cols) if 'status' in c.lower() or 'situação' in c.lower() or 'estado' in c.lower()), 0)),
                'responsavel': st.selectbox("Responsável", cols, index=next((i for i,c in enumerate(cols) if 'respons' in c.lower() or 'dono' in c.lower() or 'owner' in c.lower()), 0)),
                'predecessores': st.selectbox("Predecessores", [""] + cols),
            }
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")
    
    if st.session_state.df is not None:
        st.markdown("### Ações Rápidas")
        if st.button("Análise de Riscos"):
            st.session_state.messages.append({"role": "user", "content": "Faça análise completa de riscos do projeto atual."})
            st.rerun()
        if st.button("Relatório Métricas"):
            st.session_state.messages.append({"role": "user", "content": "Gere relatório de métricas, saúde e caminho crítico."})
            st.rerun()
        if st.button("Plano 5W2H"):
            st.session_state.messages.append({"role": "user", "content": "Monte plano 5W2H para recuperar atrasos."})
            st.rerun()
        if st.button("Resumo Executivo"):
            st.session_state.messages.append({"role": "user", "content": "Crie resumo executivo para diretoria."})
            st.rerun()

# MAIN
st.markdown('<div style="text-align:center;">' + PROFESSIONAL_ICON_SVG + '<h1>GPlan IA 4.0</h1></div>', unsafe_allow_html=True)

if st.session_state.df is not None:
    gerar_dashboard(st.session_state.df, st.session_state.column_map)
    st.divider()
    st.subheader("Assistente Inteligente")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Pergunte sobre o projeto..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    if gemini_model and st.session_state.df is not None:
        with st.chat_message("assistant"):
            with st.spinner("Processando..."):
                try:
                    chat = gemini_model.start_chat(history=[
                        {"role": "user" if m["role"]=="user" else "model", "parts": [m["content"]]}
                        for m in st.session_state.messages[:-1]
                    ])
                    contexto = f"Dados resumidos:\n{st.session_state.df.head(8).to_string()}"
                    resp = chat.send_message(f"{contexto}\nPergunta: {prompt}")
                    answer = resp.text
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Erro na IA: {str(e)}")
    else:
        st.warning("Carregue o cronograma para ativar o assistente.")

st.caption("GPlan IA 4.0 • Design Premium • BI Automático • 2026")

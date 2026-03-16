"""
GPlan IA 4.0 — Enterprise Edition (Gemini 2.5 Flash)
Versão Premium Modern + Minimalista + BI Automático + Botões de Ação Rápida
Ícone profissional personalizado (olhando para frente, estilo Grok-like)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

# ====================== VISUAL MODERNO MINIMALISTA ======================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background: #0a0f1c;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: #0a0f1c;
    }
    
    [data-testid="stSidebar"] {
        background: #111827;
        border-right: 1px solid #1f2937;
    }
    
    h1, h2, h3, h4 {
        font-weight: 700;
        color: #60a5fa;
    }
    
    .stMetric {
        background: #1f2937;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #334155;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    .card {
        background: #1f2937;
        border-radius: 16px;
        padding: 24px;
        border: 1px solid #334155;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        border: none;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s;
        padding: 12px 20px;
        margin: 8px 0;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.4);
    }
    
    .action-buttons .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #1e40af, #3b82f6);
    }
    
    .chat-message {
        border-radius: 16px;
        padding: 16px 20px;
        margin: 12px 0;
    }
    
    [data-testid="stChatMessage"] {
        background: #1f2937 !important;
        border: 1px solid #334155;
    }
    
    .header-icon {
        font-size: 64px;
        margin-bottom: -20px;
        text-align: center;
        color: #60a5fa;
    }
    
    .header-title {
        text-align: center;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ====================== GEMINI INIT ======================
@st.cache_resource
def init_gemini():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("Configure GEMINI_API_KEY nos Secrets")
            return None
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction="""Você é o GPlan IA 4.0, assistente sênior de gestão de projetos. 
Responda sempre em português brasileiro impecável, profissional e detalhado. 
Use tabelas Markdown e listas claras. Foque em PMBOK, Scrum e melhores práticas."""
        )
    except:
        return None

gemini_model = init_gemini()

# ====================== ESTADO ======================
if "df" not in st.session_state: st.session_state.df = None
if "project_name" not in st.session_state: st.session_state.project_name = "Novo Projeto"
if "column_map" not in st.session_state: st.session_state.column_map = {}
if "messages" not in st.session_state:
    st.session_state.messages = []

# ====================== FUNÇÕES ======================
def calcular_caminho_critico(df, col_map):
    if df is None or df.empty: return {"caminho": [], "folga": {}}
    G = nx.DiGraph()
    for _, row in df.iterrows():
        tarefa = str(row.get(col_map.get('tarefa'), 'Sem nome'))
        G.add_node(tarefa)
        preds = str(row.get(col_map.get('predecessores', ''), '')).split(',')
        for p in [x.strip() for x in preds if x.strip()]:
            if p in df[col_map.get('tarefa')].astype(str).values:
                G.add_edge(p, tarefa)
    try:
        caminho = nx.dag_longest_path(G)
        return {"caminho": caminho}
    except:
        return {"caminho": []}

def gerar_gantt(df, col_map):
    try:
        dfg = df.copy()
        dfg['Start'] = pd.to_datetime(dfg[col_map['inicio']], errors='coerce')
        dfg['Finish'] = pd.to_datetime(dfg[col_map['fim']], errors='coerce')
        fig = px.timeline(dfg, x_start="Start", x_end="Finish", y=col_map['tarefa'],
                          color=col_map.get('status'), hover_data=[col_map.get('responsavel')])
        fig.update_layout(template="plotly_dark", height=520, margin=dict(l=0,r=0,t=30,b=0))
        return fig
    except:
        return None

def gerar_dashboard(df, col_map):
    if df is None or df.empty: return
    
    cp = calcular_caminho_critico(df, col_map)
    atrasadas = len(df[df[col_map['status']].astype(str).str.contains("atrasado|late|delay|pendente", case=False, na=False)])
    total = len(df)
    saude = round(100 - (atrasadas / total * 100) if total > 0 else 0, 1)
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Tarefas", total)
    col2.metric("Caminho Crítico", len(cp['caminho']))
    col3.metric("Tarefas Atrasadas", atrasadas, delta=f"-{atrasadas}", delta_color="inverse")
    col4.metric("Saúde do Projeto", f"{saude}%", delta=f"{saude-80:+.1f}%")
    
    # Gráficos
    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader("Diagrama de Gantt")
        fig_gantt = gerar_gantt(df, col_map)
        if fig_gantt:
            st.plotly_chart(fig_gantt, use_container_width=True)
    
    with c2:
        st.subheader("Distribuição de Status")
        status_counts = df[col_map['status']].value_counts()
        fig_pie = px.pie(values=status_counts.values, names=status_counts.index, 
                         color_discrete_sequence=px.colors.sequential.Blues_r)
        fig_pie.update_layout(template="plotly_dark", height=380)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Carga por responsável
    st.subheader("Carga por Responsável")
    resp_col = col_map.get('responsavel')
    if resp_col in df.columns:
        carga = df[resp_col].value_counts().head(10)
        fig_bar = px.bar(x=carga.values, y=carga.index, orientation='h',
                         color=carga.values, color_continuous_scale="blues")
        fig_bar.update_layout(template="plotly_dark", height=420)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Caminho crítico
    st.subheader("Caminho Crítico")
    if cp['caminho']:
        st.code("\n".join(cp['caminho']), language="text")
    else:
        st.info("Caminho crítico não detectado (verifique coluna de predecessores)")

# ====================== SIDEBAR ======================
with st.sidebar:
    st.markdown('<div class="header-icon">🧠</div>', unsafe_allow_html=True)
    st.markdown('<h2 class="header-title">GPlan IA</h2>', unsafe_allow_html=True)
    st.caption("Gestão Inteligente de Projetos")
    
    uploaded = st.file_uploader("Upload Cronograma", type=["xlsx", "xls", "csv"])
    
    if uploaded:
        try:
            df = pd.read_excel(uploaded) if uploaded.name.lower().endswith(('.xlsx','.xls')) else pd.read_csv(uploaded)
            st.session_state.df = df
            st.success("✅ Carregado")
            
            st.subheader("Mapeamento")
            cols = list(df.columns)
            st.session_state.column_map = {
                'tarefa': st.selectbox("Tarefa", cols, index=next((i for i,c in enumerate(cols) if 'tarefa' in c.lower() or 'nome' in c.lower()), 0)),
                'inicio': st.selectbox("Início", cols, index=next((i for i,c in enumerate(cols) if any(k in c.lower() for k in ['início','inicio','start'])), 0)),
                'fim': st.selectbox("Fim", cols, index=next((i for i,c in enumerate(cols) if any(k in c.lower() for k in ['fim','end','término'])), 0)),
                'status': st.selectbox("Status", cols, index=next((i for i,c in enumerate(cols) if 'status' in c.lower() or 'situação' in c.lower()), 0)),
                'responsavel': st.selectbox("Responsável", cols, index=next((i for i,c in enumerate(cols) if any(k in c.lower() for k in ['respons','dono','owner'])), 0)),
                'predecessores': st.selectbox("Predecessores", [""] + cols),
            }
            st.session_state.project_name = st.text_input("Nome do Projeto", value=st.session_state.project_name)
        except Exception as e:
            st.error(f"Erro: {e}")
    
    if st.session_state.df is not None:
        st.markdown("### Ações Rápidas")
        st.markdown('<div class="action-buttons">', unsafe_allow_html=True)
        
        if st.button("🚨 Análise de Riscos"):
            st.session_state.messages.append({"role": "user", "content": "Faça uma análise completa e detalhada de riscos do projeto atual, incluindo tarefas críticas, sobrecarga de recursos e recomendações."})
            st.rerun()
        
        if st.button("📊 Relatório de Métricas"):
            st.session_state.messages.append({"role": "user", "content": "Gere um relatório executivo completo com métricas-chave, saúde do projeto, caminho crítico e sugestões de melhoria."})
            st.rerun()
        
        if st.button("📋 Plano de Recuperação 5W2H"):
            st.session_state.messages.append({"role": "user", "content": "Monte um plano de ação 5W2H detalhado para recuperar as tarefas atrasadas e críticas do caminho crítico."})
            st.rerun()
        
        if st.button("📈 Resumo Executivo"):
            st.session_state.messages.append({"role": "user", "content": "Crie um resumo executivo profissional para apresentação à diretoria, incluindo status atual, riscos principais e próximas ações."})
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# ====================== MAIN AREA ======================
st.markdown('<div class="header-icon">🧠</div>', unsafe_allow_html=True)
st.markdown(f'<h1 class="header-title">GPlan IA 4.0 — {st.session_state.project_name}</h1>', unsafe_allow_html=True)

if st.session_state.df is not None:
    st.markdown("### Dashboard Automático de Análise")
    gerar_dashboard(st.session_state.df, st.session_state.column_map)
    
    st.divider()
    st.subheader("💬 Assistente Inteligente")
else:
    st.info("Faça upload do seu cronograma para ativar o dashboard automático e o assistente.")

# Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Pergunte sobre o projeto..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    if gemini_model and st.session_state.df is not None:
        with st.chat_message("assistant"):
            with st.spinner("Analisando..."):
                try:
                    chat = gemini_model.start_chat(history=[
                        {"role": "user" if m["role"]=="user" else "model", "parts": [m["content"]]} 
                        for m in st.session_state.messages[:-1]
                    ])
                    contexto = f"Projeto: {st.session_state.project_name}\nDados resumidos: {st.session_state.df.head(8).to_string()}"
                    resp = chat.send_message(f"{contexto}\nPergunta: {prompt}",
                                             generation_config=genai.types.GenerationConfig(temperature=0.7, max_output_tokens=2200))
                    answer = resp.text
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
    else:
        st.warning("Carregue um cronograma para usar o assistente.")

st.caption("GPlan IA 4.0 • Design Premium • BI Automático • Gemini 2.5 Flash • 2026")

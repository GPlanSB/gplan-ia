"""
GPlan IA 4.0 — Enterprise Edition (Full Fix)
Engenharia de Software: Correção de Parsing, Botões e Sintaxe
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import networkx as nx
import google.generativeai as genai
import warnings

# Silenciar avisos desnecessários
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
        return None
    genai.configure(api_key=api_key)
    # Usando o modelo estável 1.5 Flash para máxima velocidade
    return genai.GenerativeModel(
        model_name='gemini-1.5-flash', 
        system_instruction="Você é GPlan IA 4.0, assistente sênior de projetos. Responda em PT-BR profissional, com tabelas e insights acionáveis."
    )

def fix_dates(df, col):
    """Tratamento robusto de datas para evitar crash no Plotly"""
    if col not in df.columns: return None
    temp = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
    if temp.isna().all():
        temp = pd.to_datetime(df[col], errors='coerce')
    return temp

def calcular_caminho_critico(df, col_map):
    if df is None or df.empty or not col_map.get('predecessores'): return []
    G = nx.DiGraph()
    try:
        for _, row in df.iterrows():
            tarefa = str(row[col_map['tarefa']])
            G.add_node(tarefa)
            preds = str(row.get(col_map['predecessores'], '')).split(',')
            for p in [x.strip() for x in preds if x.strip() and x != 'nan' and x != 'None']:
                if p in df[col_map['tarefa']].astype(str).values:
                    G.add_edge(p, tarefa)
        return nx.dag_longest_path(G)
    except:
        return []

# --- ESTADO DA SESSÃO ---
if "df" not in st.session_state: st.session_state.df = None
if "messages" not in st.session_state: st.session_state.messages = []
if "column_map" not in st.session_state: st.session_state.column_map = {}

gemini_model = init_gemini()

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Painel de Controle")
    uploaded = st.file_uploader("Upload do Cronograma (Excel/CSV)", type=["xlsx", "csv"])
    
    if uploaded:
        # Só carrega se o dataframe ainda estiver vazio
        if st.session_state.df is None:
            try:
                df_input = pd.read_excel(uploaded) if 'xlsx' in uploaded.name else pd.read_csv(uploaded)
                st.session_state.df = df_input
            except Exception as e:
                st.error(f"Erro ao ler arquivo: {e}")
        
        if st.session_state.df is not None:
            cols = list(st.session_state.df.columns)
            st.session_state.column_map = {
                'tarefa': st.selectbox("Tarefa", cols, index=0),
                'inicio': st.selectbox("Início", cols, index=1 if len(cols)>1 else 0),
                'fim': st.selectbox("Fim", cols, index=2 if len(cols)>2 else 0),
                'status': st.selectbox("Status", cols, index=3 if len(cols)>3 else 0),
                'responsavel': st.selectbox("Responsável", cols, index=0),
                'predecessores': st.selectbox("Predecessores", [""] + cols)
            }

    st.markdown("---")
    st.subheader("🚀 Ações Rápidas")
    
    # Lógica de Botões Corrigida
    if st.session_state.df is not None:
        if st.button("🚨 Análise de Riscos"):
            st.session_state.messages.append({"role": "user", "content": "Faça uma análise de riscos detalhada deste projeto."})
            st.rerun()
            
        if st.button("📊 Relatório de Métricas"):
            st.session_state.messages.append({"role": "user", "content": "Gere um relatório de métricas e performance geral."})
            st.rerun()
            
        if st.button("📉 Plano 5W2H"):
            st.session_state.messages.append({"role": "user", "content": "Crie um plano 5W2H para as tarefas pendentes/atrasadas."})
            st.rerun()

# --- MAIN UI ---
st.title("📊 GPlan IA 4.0")

if st.session_state.df is not None:
    df_main = st.session_state.df.copy()
    cmap = st.session_state.column_map
    
    # Processamento de Datas para o Gantt
    df_main['Start'] = fix_dates(df_main, cmap['inicio'])
    df_main['Finish'] = fix_dates(df_main, cmap['fim'])
    
    # Dashboard de Métricas
    col_a, col_b, col_c, col_d = st.columns(4)
    total_t = len(df_main)
    status_col = cmap['status']
    atrasadas_t = len(df_main[df_main[status_col].astype(str).str.contains("Atrasado|Pendente|Late|Atraso", case=False, na=False)])
    caminho_c = calcular_caminho_critico(df_main, cmap)
    saude_n = 100 - int((atrasadas_t / total_t * 100) if total_t > 0 else 0)

    col_a.metric("Total Tarefas", total_t)
    col_b.metric("Caminho Crítico", len(caminho_c))
    col_c.metric("Atrasadas", atrasadas_t, delta=f"-{atrasadas_t}" if atrasadas_t > 0 else "0", delta_color="inverse")
    col_d.metric("Saúde do Projeto", f"{saude_n}%")

    # Gráfico de Gantt
    df_gantt = df_main.dropna(subset=['Start', 'Finish'])
    if not df_gantt.empty:
        fig = px.timeline(
            df_gantt, 
            x_start="Start", x_end="Finish", 
            y=cmap['tarefa'], color=status_col,
            title="Cronograma Visual",
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aguardando mapeamento correto das colunas de data para gerar o Gantt.")

    # --- CHAT INTERFACE ---
    st.divider()
    st.subheader("🤖 Assistente Inteligente")

    # Mostrar histórico
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input do Chat
    prompt = st.chat_input("Pergunte sobre prazos, riscos ou próximos passos...")

    # Se houver uma nova mensagem (via input ou botão de ação rápida)
    if (len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user") or prompt:
        
        # Se veio do chat_input, adiciona agora. Se veio do botão, já está no messages.
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

        # Resposta da IA
        with st.chat_message("assistant"):
            if gemini_model:
                try:
                    # Contexto reduzido para a IA não exceder tokens e focar no importante
                    dados_contexto = df_main[[cmap['tarefa'], status_col]].head(20).to_string()
                    pergunta_final = st.session_state.messages[-1]["content"]
                    
                    full_query = f"Dados do Projeto:\n{dados_contexto}\n\nPergunta: {pergunta_final}"
                    
                    response = gemini_model.generate_content(full_query)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
            else:
                st.error("Configure a GEMINI_API_KEY nos Secrets do Streamlit.")

else:
    st.info("💡 Para começar, faça o upload de uma planilha de cronograma na barra lateral.")

st.caption("GPlan IA 4.0 • Sistema de Gestão Inteligente • 2026")

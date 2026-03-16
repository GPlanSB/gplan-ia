"""
GPlan IA 4.0 — Enterprise Edition (com Google Gemini API gratuita)
Copiloto Master de Gestão de Projetos com Caminho Crítico + Gantt + Baseline
Versão Streamlit Completa - Corrigido para respostas longas e consistentes
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

# Tema visual (mantido simples e funcional)
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #0f172a; color: #e2e8f0; }
    .stButton > button { background: linear-gradient(135deg, #00d9ff, #7c3aed); color: white; border: none; }
    h1, h2, h3 { color: #00d9ff; }
</style>
""", unsafe_allow_html=True)

# Inicialização do Gemini com instruções fortes para respostas detalhadas
@st.cache_resource
def init_gemini():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada nos secrets")
        genai.configure(api_key=api_key)
        
        return genai.GenerativeModel(
            model_name='gemini-1.5-flash',  # ou 'gemini-1.5-flash-002' se disponível
            system_instruction="""Você é o GPlan IA 4.0, um assistente sênior de gestão de projetos extremamente competente.
Sempre responda em português brasileiro impecável, sem erros de digitação ou abreviações.
Seja detalhado, analítico, proativo e estruturado. Use tabelas Markdown para métricas, riscos, planos de ação 5W2H, listas numeradas/ com bullets quando fizer sentido.
Nunca dê respostas curtas, repetitivas ou vagas. Sempre forneça valor real: insights, recomendações práticas, análise baseada em PMBOK/Scrum/Kanban.
Quando houver dados do projeto, priorize fatos quantitativos e sugestões acionáveis."""
        )
    except Exception as e:
        st.error(f"Erro ao inicializar Gemini: {str(e)}\nVerifique se GEMINI_API_KEY está nos secrets.")
        return None

gemini_model = init_gemini()

# Estado da sessão
if "df" not in st.session_state:
    st.session_state.df = None
if "project_name" not in st.session_state:
    st.session_state.project_name = "Projeto Sem Nome"
if "column_map" not in st.session_state:
    st.session_state.column_map = {}
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "🧠 **Bem-vindo ao GPlan IA 4.0** (potencializado por Google Gemini)\n\n"
                                         "Faça upload do seu cronograma (Excel ou CSV) na barra lateral.\n"
                                         "Depois mapeie as colunas e pergunte o que quiser: análise de riscos, caminho crítico, plano de recuperação, resumo executivo, etc."}
    ]

# Função para calcular caminho crítico (simplificada, mas funcional)
def calcular_caminho_critico(df, col_map):
    if df is None or df.empty:
        return {"caminho": [], "folga": {}}
    
    G = nx.DiGraph()
    for _, row in df.iterrows():
        tarefa = str(row.get(col_map.get('tarefa', ''), 'Tarefa sem nome'))
        duracao = max(1, int(row.get(col_map.get('duracao', 5))))
        G.add_node(tarefa, duration=duracao)
        
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

# Gantt simples
def gerar_gantt(df, col_map):
    if df is None or df.empty:
        return None
    try:
        df_g = df.copy()
        df_g['Start'] = pd.to_datetime(df_g[col_map['inicio']], errors='coerce')
        df_g['Finish'] = pd.to_datetime(df_g[col_map['fim']], errors='coerce')
        df_g = df_g.dropna(subset=['Start', 'Finish'])
        if df_g.empty:
            return None
        fig = px.timeline(df_g, x_start="Start", x_end="Finish", y=col_map['tarefa'],
                          color=col_map.get('status', None), hover_data=[col_map.get('responsavel')])
        fig.update_layout(template="plotly_dark", height=500, title="Gantt do Projeto")
        return fig
    except:
        return None

# Contexto resumido (economiza tokens)
def gerar_contexto(df, col_map):
    if df is None or df.empty:
        return "Nenhum cronograma carregado ainda."
    
    cp = calcular_caminho_critico(df, col_map)
    atrasadas = len(df[df[col_map['status']].astype(str).str.contains("atrasado|atraso|late", case=False, na=False)])
    
    return f"""
PROJETO: {st.session_state.project_name}
Total de tarefas: {len(df)}
Atrasadas (aprox): {atrasadas}
Caminho crítico: {', '.join(cp['caminho'][:6]) or 'Não detectado'}
Primeiras 8 linhas (resumo):
{df.head(8).to_string(index=False)}
Analise com base nesses dados quando relevante.
"""

# SIDEBAR
with st.sidebar:
    st.title("🧠 GPlan IA 4.0")
    st.caption("Gemini Free Tier")
    
    uploaded = st.file_uploader("Cronograma (Excel/CSV)", type=["xlsx", "xls", "csv"])
    
    if uploaded is not None:
        try:
            if uploaded.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded)
            else:
                df = pd.read_csv(uploaded)
            st.session_state.df = df
            st.success("✅ Arquivo carregado com sucesso!")
            
            st.subheader("Mapeamento de colunas")
            cols = list(df.columns)
            
            st.session_state.column_map = {
                'tarefa': st.selectbox("Coluna Tarefa/Nome", cols, index=next((i for i, c in enumerate(cols) if 'arefa' in c.lower()), 0)),
                'inicio': st.selectbox("Data Início", cols, index=next((i for i, c in enumerate(cols) if 'início'início' in c.lower()), 0)),
                'fim': st.selectbox("Data Fim", cols, index=next((i for i, c in enumerate(cols) if 'fim' in c.lower()), 0)),
                'status': st.selectbox("Status", cols, index=next((i for i, c in enumerate(cols) if 'status' in c.lower()), 0)),
                'responsavel': st.selectbox("Responsável", cols, index=next((i for i, c in enumerate(cols) if 'respons' in c.lower() or 'dono' in c.lower()), 0)),
                'predecessores': st.selectbox("Predecessores (opcional)", [""] + cols),
                'percentual': st.selectbox("% Concluído (opcional)", [""] + cols),
            }
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {str(e)}")

# Área principal
st.header(f"Projeto: {st.session_state.project_name}")

if st.session_state.df is not None:
    df = st.session_state.df
    col_map = st.session_state.column_map
    
    cp = calcular_caminho_critico(df, col_map)
    
    cols = st.columns(4)
    cols[0].metric("Tarefas", len(df))
    cols[1].metric("Caminho Crítico", len(cp['caminho']))
    cols[2].metric("Atrasadas (aprox)", sum(df[col_map['status']].astype(str).str.contains("atrasado|late", case=False, na=False)))
    cols[3].metric("Saúde estimada", "Em cálculo...")
    
    fig = gerar_gantt(df, col_map)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

# Chat
st.subheader("💬 Assistente Inteligente")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Digite sua pergunta sobre o projeto..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    if gemini_model is None:
        st.error("Gemini não foi inicializado. Verifique a chave API.")
    else:
        with st.chat_message("assistant"):
            with st.spinner("Analisando..."):
                try:
                    chat = gemini_model.start_chat(history=[
                        {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
                        for m in st.session_state.messages[:-1]
                    ])
                    
                    contexto = gerar_contexto(st.session_state.df, st.session_state.column_map)
                    mensagem_completa = f"{contexto}\n\nPergunta do usuário: {prompt}"
                    
                    response = chat.send_message(
                        mensagem_completa,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.65,
                            max_output_tokens=2500,
                            top_p=0.92
                        )
                    )
                    
                    resposta = response.text
                    st.markdown(resposta)
                    st.session_state.messages.append({"role": "assistant", "content": resposta})
                
                except Exception as e:
                    msg_erro = str(e).lower()
                    if "429" in msg_erro or "rate limit" in msg_erro or "quota" in msg_erro:
                        st.error("Limite do tier gratuito atingido (rate limit). Espere 1–5 minutos e tente novamente.")
                    else:
                        st.error(f"Erro ao consultar Gemini: {str(e)}")

st.caption("GPlan IA 4.0 • Google Gemini Free • Corrigido para respostas detalhadas • 2026")

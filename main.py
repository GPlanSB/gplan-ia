"""
GPlan IA 2.0 — Copiloto Master de Gestão de Projetos
Uma ferramenta profissional de IA para gestão de projetos com interface premium,
análise avançada e capacidades de tool use para ações executáveis.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from openai import OpenAI
import json
from datetime import datetime, timedelta
import numpy as np
from typing import Any, Dict, List, Optional
import warnings

warnings.filterwarnings("ignore")

# ============================================================================
# CONFIGURAÇÃO INICIAL
# ============================================================================

st.set_page_config(
    page_title="GPlan IA 2.0 — Master Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com",
        "Report a bug": "https://github.com",
        "About": "GPlan IA 2.0 — Copiloto Master de Gestão de Projetos"
    }
)

# ============================================================================
# DESIGN SYSTEM E ESTILIZAÇÃO PREMIUM
# ============================================================================

THEME_COLORS = {
    "primary": "#00D9FF",      # Ciano vibrante
    "secondary": "#7C3AED",    # Roxo premium
    "success": "#10B981",      # Verde emerald
    "warning": "#F59E0B",      # Âmbar
    "danger": "#EF4444",       # Vermelho
    "dark_bg": "#0F172A",      # Fundo escuro profundo
    "card_bg": "#1E293B",      # Fundo de card
    "border": "#334155",       # Borda sutil
    "text_primary": "#F1F5F9", # Texto principal
    "text_secondary": "#CBD5E1" # Texto secundário
}

PREMIUM_CSS = f"""
<style>
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    html, body, [data-testid="stAppViewContainer"] {{
        background: linear-gradient(135deg, {THEME_COLORS['dark_bg']} 0%, #1a1f3a 100%);
        color: {THEME_COLORS['text_primary']};
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {THEME_COLORS['card_bg']} 0%, {THEME_COLORS['dark_bg']} 100%);
        border-right: 2px solid {THEME_COLORS['border']};
    }}
    
    [data-testid="stSidebarNav"] {{
        padding: 1rem 0;
    }}
    
    .stButton > button {{
        width: 100%;
        background: linear-gradient(135deg, {THEME_COLORS['primary']} 0%, {THEME_COLORS['secondary']} 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 217, 255, 0.3);
        cursor: pointer;
        margin: 8px 0;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 217, 255, 0.5);
    }}
    
    .stButton > button:active {{
        transform: translateY(0);
    }}
    
    .stMetric {{
        background: linear-gradient(135deg, {THEME_COLORS['card_bg']} 0%, rgba(30, 41, 59, 0.8) 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid {THEME_COLORS['border']};
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }}
    
    .stMetric:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0, 217, 255, 0.2);
        border-color: {THEME_COLORS['primary']};
    }}
    
    .stChatMessage {{
        background: {THEME_COLORS['card_bg']};
        border-radius: 12px;
        border: 1px solid {THEME_COLORS['border']};
        padding: 16px;
        margin: 12px 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }}
    
    .stChatMessage[data-testid="chat-message-user"] {{
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.2) 0%, rgba(0, 217, 255, 0.1) 100%);
        border-left: 4px solid {THEME_COLORS['secondary']};
    }}
    
    .stChatMessage[data-testid="chat-message-assistant"] {{
        background: linear-gradient(135deg, rgba(0, 217, 255, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%);
        border-left: 4px solid {THEME_COLORS['primary']};
    }}
    
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {{
        background: {THEME_COLORS['card_bg']} !important;
        color: {THEME_COLORS['text_primary']} !important;
        border: 1px solid {THEME_COLORS['border']} !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stNumberInput > div > div > input:focus {{
        border-color: {THEME_COLORS['primary']} !important;
        box-shadow: 0 0 0 2px rgba(0, 217, 255, 0.2) !important;
    }}
    
    .stDivider {{
        border-color: {THEME_COLORS['border']} !important;
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        color: {THEME_COLORS['text_primary']};
        font-weight: 700;
    }}
    
    .metric-card {{
        background: linear-gradient(135deg, {THEME_COLORS['card_bg']} 0%, rgba(30, 41, 59, 0.8) 100%);
        padding: 24px;
        border-radius: 12px;
        border: 1px solid {THEME_COLORS['border']};
        text-align: center;
    }}
    
    .metric-value {{
        font-size: 32px;
        font-weight: 700;
        color: {THEME_COLORS['primary']};
        margin: 12px 0;
    }}
    
    .metric-label {{
        font-size: 14px;
        color: {THEME_COLORS['text_secondary']};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    .status-badge {{
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }}
    
    .status-on-track {{
        background: rgba(16, 185, 129, 0.2);
        color: {THEME_COLORS['success']};
        border: 1px solid {THEME_COLORS['success']};
    }}
    
    .status-at-risk {{
        background: rgba(245, 158, 11, 0.2);
        color: {THEME_COLORS['warning']};
        border: 1px solid {THEME_COLORS['warning']};
    }}
    
    .status-delayed {{
        background: rgba(239, 68, 68, 0.2);
        color: {THEME_COLORS['danger']};
        border: 1px solid {THEME_COLORS['danger']};
    }}
    
    .section-title {{
        font-size: 20px;
        font-weight: 700;
        color: {THEME_COLORS['text_primary']};
        margin: 24px 0 16px 0;
        padding-bottom: 12px;
        border-bottom: 2px solid {THEME_COLORS['border']};
    }}
    
    .loading-spinner {{
        display: inline-block;
        animation: spin 1s linear infinite;
    }}
    
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
</style>
"""

st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

# ============================================================================
# INICIALIZAÇÃO DO CLIENTE OPENAI
# ============================================================================

@st.cache_resource
def init_openai_client():
    """Inicializa o cliente OpenAI com tratamento de erro."""
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada")
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"❌ Erro ao inicializar OpenAI: {str(e)}")
        st.stop()

client = init_openai_client()

# ============================================================================
# FERRAMENTAS (TOOL USE) - FUNÇÕES QUE A IA PODE CHAMAR
# ============================================================================

def analisar_riscos(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analisa riscos no cronograma do projeto.
    Retorna uma análise estruturada de riscos potenciais.
    """
    if df is None or df.empty:
        return {"erro": "Nenhum dado disponível para análise de riscos"}
    
    riscos = []
    
    # Detectar tarefas atrasadas
    status_col = next((c for c in df.columns if 'status' in c.lower()), None)
    if status_col:
        atrasadas = df[df[status_col].str.contains("Atrasado|Atraso|Late", case=False, na=False)]
        if len(atrasadas) > 0:
            riscos.append({
                "tipo": "Tarefas Atrasadas",
                "severidade": "ALTA",
                "quantidade": len(atrasadas),
                "impacto": "Pode comprometer o cronograma geral do projeto"
            })
    
    # Detectar sobrecarga de recursos
    resp_col = next((c for c in df.columns if 'respons' in c.lower() or 'dono' in c.lower()), None)
    if resp_col:
        carga = df[resp_col].value_counts()
        media_carga = carga.mean()
        sobrecarregados = carga[carga > media_carga * 1.5]
        if len(sobrecarregados) > 0:
            riscos.append({
                "tipo": "Sobrecarga de Recursos",
                "severidade": "MÉDIA",
                "quantidade": len(sobrecarregados),
                "impacto": "Pode afetar a qualidade e o bem-estar da equipe"
            })
    
    # Detectar falta de atribuição
    if resp_col:
        nao_atribuidas = df[df[resp_col].isna() | (df[resp_col] == "")]
        if len(nao_atribuidas) > 0:
            riscos.append({
                "tipo": "Tarefas Não Atribuídas",
                "severidade": "MÉDIA",
                "quantidade": len(nao_atribuidas),
                "impacto": "Falta de clareza sobre responsabilidades"
            })
    
    return {
        "total_riscos": len(riscos),
        "riscos": riscos,
        "total_tarefas": len(df),
        "taxa_risco": (len(riscos) / max(len(df), 1)) * 100
    }

def gerar_metricas_projeto(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Gera métricas consolidadas do projeto.
    """
    if df is None or df.empty:
        return {"erro": "Nenhum dado disponível"}
    
    total_tarefas = len(df)
    
    # Status
    status_col = next((c for c in df.columns if 'status' in c.lower()), None)
    atrasadas = 0
    concluidas = 0
    em_progresso = 0
    
    if status_col:
        atrasadas = len(df[df[status_col].str.contains("Atrasado|Atraso|Late", case=False, na=False)])
        concluidas = len(df[df[status_col].str.contains("Concluído|Completo|Done|Finalizado", case=False, na=False)])
        em_progresso = len(df[df[status_col].str.contains("Progresso|Em Andamento|In Progress", case=False, na=False)])
    
    saude = ((total_tarefas - atrasadas) / total_tarefas * 100) if total_tarefas > 0 else 0
    
    return {
        "total_tarefas": total_tarefas,
        "concluidas": concluidas,
        "em_progresso": em_progresso,
        "atrasadas": atrasadas,
        "nao_iniciadas": total_tarefas - concluidas - em_progresso - atrasadas,
        "saude_projeto": round(saude, 2),
        "percentual_conclusao": round((concluidas / total_tarefas * 100), 2) if total_tarefas > 0 else 0
    }

def gerar_plano_5w2h(tarefas_atrasadas: List[str]) -> Dict[str, Any]:
    """
    Gera um plano 5W2H para tarefas atrasadas.
    """
    if not tarefas_atrasadas:
        return {"erro": "Nenhuma tarefa atrasada para planejar"}
    
    return {
        "framework": "5W2H",
        "tarefas_cobertas": len(tarefas_atrasadas),
        "componentes": {
            "What": "O que precisa ser feito para recuperar o atraso",
            "Why": "Por que essas ações são necessárias",
            "Who": "Quem é responsável por cada ação",
            "When": "Quando cada ação será executada",
            "Where": "Onde os recursos serão alocados",
            "How": "Como as ações serão implementadas",
            "How Much": "Quanto de recursos (tempo, custo) será necessário"
        },
        "status": "Pronto para detalhamento pela IA"
    }

def criar_resumo_executivo(df: pd.DataFrame, foco: str = "geral") -> Dict[str, Any]:
    """
    Cria um resumo executivo do projeto.
    """
    if df is None or df.empty:
        return {"erro": "Nenhum dado disponível"}
    
    metricas = gerar_metricas_projeto(df)
    riscos = analisar_riscos(df)
    
    return {
        "tipo": "Resumo Executivo",
        "data_geracao": datetime.now().isoformat(),
        "foco": foco,
        "metricas_chave": metricas,
        "riscos_principais": riscos.get("riscos", [])[:3],
        "recomendacoes": "Serão geradas pela IA com base nos dados"
    }

# Dicionário de ferramentas disponíveis para a IA
TOOLS_AVAILABLE = {
    "analisar_riscos": {
        "description": "Analisa riscos no cronograma do projeto baseado nos dados",
        "function": analisar_riscos
    },
    "gerar_metricas_projeto": {
        "description": "Gera métricas consolidadas do projeto (saúde, conclusão, etc)",
        "function": gerar_metricas_projeto
    },
    "gerar_plano_5w2h": {
        "description": "Gera um plano 5W2H para tarefas atrasadas",
        "function": gerar_plano_5w2h
    },
    "criar_resumo_executivo": {
        "description": "Cria um resumo executivo do projeto",
        "function": criar_resumo_executivo
    }
}

# ============================================================================
# ESTADO DA SESSÃO
# ============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "🧠 **Olá! Sou o GPlan IA 2.0**, seu copiloto master de gestão de projetos.\n\n"
                      "Estou equipado com capacidades avançadas de análise, previsão e planejamento. "
                      "Posso ajudá-lo com:\n\n"
                      "✨ **Análise de Riscos** — Identificar desvios e ameaças ao cronograma\n"
                      "📊 **Métricas de Projeto** — Saúde, progresso e performance em tempo real\n"
                      "📋 **Planos de Ação** — Estratégias 5W2H para recuperação de atrasos\n"
                      "📈 **Resumos Executivos** — Insights para a diretoria\n\n"
                      "Comece fazendo upload de seu cronograma (Excel/CSV) na sidebar e use os comandos rápidos ou converse comigo!"
        }
    ]

if "df" not in st.session_state:
    st.session_state.df = None

if "tool_results" not in st.session_state:
    st.session_state.tool_results = {}

# ============================================================================
# SIDEBAR - CONTROLES E CONFIGURAÇÃO
# ============================================================================

with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="font-size: 28px; margin: 0;">🧠</h1>
        <h2 style="font-size: 18px; margin: 8px 0; color: #00D9FF;">GPlan IA 2.0</h2>
        <p style="font-size: 12px; color: #CBD5E1; margin: 0;">Master Intelligence</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    st.subheader("📁 Ingestão de Dados", divider="blue")
    uploaded_file = st.file_uploader(
        "Upload de Cronograma (Excel/CSV)",
        type=["xlsx", "csv", "xls"],
        help="Faça upload de seu cronograma de projeto em formato Excel ou CSV"
    )
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                st.session_state.df = pd.read_csv(uploaded_file)
            else:
                st.session_state.df = pd.read_excel(uploaded_file)
            
            st.success("✅ Base de dados integrada com sucesso!")
            
            with st.expander("📋 Prévia dos Dados"):
                st.dataframe(st.session_state.df.head(10), use_container_width=True)
                st.caption(f"Total de linhas: {len(st.session_state.df)} | Colunas: {', '.join(st.session_state.df.columns.tolist())}")
        
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {str(e)}")
    
    st.divider()
    
    st.subheader("⚡ Comandos Rápidos", divider="green")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚨 Análise de\nRiscos", use_container_width=True, key="btn_riscos"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Faça uma análise rigorosa de riscos baseada nos dados atuais do projeto. Use a ferramenta de análise de riscos e me dê um relatório detalhado."
            })
            st.rerun()
    
    with col2:
        if st.button("📊 Métricas do\nProjeto", use_container_width=True, key="btn_metricas"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Gere um relatório completo de métricas do projeto. Use a ferramenta de métricas e me mostre a saúde geral, progresso e status de todas as tarefas."
            })
            st.rerun()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Plano 5W2H", use_container_width=True, key="btn_5w2h"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Gere um plano de ação 5W2H para as tarefas atrasadas. Use a ferramenta apropriada e detalhe cada componente (What, Why, Who, When, Where, How, How Much)."
            })
            st.rerun()
    
    with col2:
        if st.button("📈 Resumo\nExecutivo", use_container_width=True, key="btn_resumo"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Crie um resumo executivo profissional para apresentar à diretoria. Use a ferramenta de resumo executivo e inclua métricas-chave, riscos principais e recomendações."
            })
            st.rerun()
    
    st.divider()
    
    st.subheader("⚙️ Configurações", divider="gray")
    
    temperatura = st.slider(
        "Temperatura da IA",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Menor = mais determinístico | Maior = mais criativo"
    )
    
    modelo = st.selectbox(
        "Modelo de IA",
        ["gpt-4o", "gpt-4-turbo", "gpt-4"],
        help="Selecione o modelo de IA a usar"
    )

# ============================================================================
# ÁREA PRINCIPAL - DASHBOARD E CHAT
# ============================================================================

st.markdown("""
<div style="text-align: center; margin: 20px 0;">
    <h1 style="font-size: 32px; margin: 0; background: linear-gradient(135deg, #00D9FF, #7C3AED); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        🧠 GPlan IA 2.0
    </h1>
    <p style="color: #CBD5E1; margin: 8px 0;">Copiloto Master de Gestão de Projetos</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# DASHBOARD DE BI (Se houver dados)
# ============================================================================

if st.session_state.df is not None:
    df = st.session_state.df
    
    st.markdown('<div class="section-title">📊 Dashboard de Performance</div>', unsafe_allow_html=True)
    
    # Calcular métricas
    metricas = gerar_metricas_projeto(df)
    
    # Exibir métricas em cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total de Tarefas",
            metricas["total_tarefas"],
            help="Número total de tarefas no projeto"
        )
    
    with col2:
        st.metric(
            "Concluídas",
            metricas["concluidas"],
            delta=f"{metricas['percentual_conclusao']:.1f}%",
            help="Tarefas completadas"
        )
    
    with col3:
        st.metric(
            "Atrasadas",
            metricas["atrasadas"],
            delta=f"{metricas['atrasadas']/metricas['total_tarefas']*100:.1f}%" if metricas["total_tarefas"] > 0 else 0,
            delta_color="inverse",
            help="Tarefas com atraso"
        )
    
    with col4:
        saude_color = "green" if metricas["saude_projeto"] >= 80 else "orange" if metricas["saude_projeto"] >= 60 else "red"
        st.metric(
            "Saúde do Projeto",
            f"{metricas['saude_projeto']:.1f}%",
            help="Indicador geral de saúde"
        )
    
    # Gráficos
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        status_col = next((c for c in df.columns if 'status' in c.lower()), None)
        if status_col:
            status_counts = df[status_col].value_counts()
            fig_pie = go.Figure(data=[go.Pie(
                labels=status_counts.index,
                values=status_counts.values,
                hole=0.4,
                marker=dict(
                    colors=["#10B981", "#F59E0B", "#EF4444", "#7C3AED"],
                    line=dict(color="#1E293B", width=2)
                )
            )])
            fig_pie.update_layout(
                title="Distribuição de Status",
                template="plotly_dark",
                paper_bgcolor="#0F172A",
                plot_bgcolor="#1E293B",
                font=dict(color="#F1F5F9"),
                showlegend=True
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_chart2:
        resp_col = next((c for c in df.columns if 'respons' in c.lower() or 'dono' in c.lower()), None)
        if resp_col:
            resp_counts = df[resp_col].value_counts().head(10)
            fig_bar = go.Figure(data=[go.Bar(
                x=resp_counts.values,
                y=resp_counts.index,
                orientation='h',
                marker=dict(
                    color=resp_counts.values,
                    colorscale=[[0, "#7C3AED"], [1, "#00D9FF"]],
                    line=dict(color="#1E293B", width=1)
                )
            )])
            fig_bar.update_layout(
                title="Carga por Responsável",
                template="plotly_dark",
                paper_bgcolor="#0F172A",
                plot_bgcolor="#1E293B",
                font=dict(color="#F1F5F9"),
                xaxis_title="Número de Tarefas",
                yaxis_title="Responsável",
                showlegend=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    st.divider()

# ============================================================================
# ÁREA DE CHAT COM SUPORTE A TOOL USE
# ============================================================================

st.markdown('<div class="section-title">💬 Assistente Inteligente</div>', unsafe_allow_html=True)

# Exibir histórico de chat
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Input de chat
if prompt := st.chat_input("Como posso ajudar no seu planejamento agora?", key="chat_input"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Preparar contexto de dados
    contexto_dados = ""
    if st.session_state.df is not None:
        df = st.session_state.df
        metricas = gerar_metricas_projeto(df)
        contexto_dados = f"""
DADOS ATUAIS DO PROJETO:
- Total de Tarefas: {metricas['total_tarefas']}
- Concluídas: {metricas['concluidas']} ({metricas['percentual_conclusao']:.1f}%)
- Em Progresso: {metricas['em_progresso']}
- Atrasadas: {metricas['atrasadas']}
- Saúde do Projeto: {metricas['saude_projeto']:.1f}%

Primeiras 50 linhas dos dados:
{df.head(50).to_string()}
"""
    else:
        contexto_dados = "Nenhuma planilha subida ainda. Responda com base em teoria geral de PMBOK/Scrum."
    
    # System prompt aprimorado
    SYSTEM_PROMPT = f"""
Você é o GPlan IA 2.0, o mais avançado copiloto de gestão de projetos com capacidades de análise profunda e ação executável.

PERSONALIDADE: Consultor Sênior experiente, assertivo, analítico, focado em resultados e impacto estratégico.

BASE DE CONHECIMENTO: PMBOK 7, Scrum Guide 2020, Kanban, Lean, e melhores práticas de gestão de projetos.

CAPACIDADES ESPECIAIS: Você tem acesso a ferramentas que pode chamar para executar ações específicas:
- analisar_riscos: Analisa riscos no cronograma
- gerar_metricas_projeto: Gera métricas consolidadas
- gerar_plano_5w2h: Cria planos de ação estruturados
- criar_resumo_executivo: Gera resumos para diretoria

INSTRUÇÕES:
1. Se o usuário pedir análise de riscos, use a ferramenta analisar_riscos
2. Se o usuário pedir métricas ou saúde do projeto, use gerar_metricas_projeto
3. Se o usuário pedir plano 5W2H ou ação para tarefas atrasadas, use gerar_plano_5w2h
4. Se o usuário pedir resumo executivo, use criar_resumo_executivo
5. Sempre que possível, use as ferramentas para fornecer análises quantitativas e estruturadas
6. Formule respostas em Markdown com tabelas, listas e estrutura clara
7. Seja proativo em sugerir ações baseadas nos dados

CONTEXTO DOS DADOS:
{contexto_dados}
"""
    
    with st.chat_message("assistant"):
        with st.spinner("🧠 GPlan processando estratégia..."):
            try:
                # Fazer chamada à API com suporte a tool use
                response = client.chat.completions.create(
                    model=modelo,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        *st.session_state.messages
                    ],
                    temperature=temperatura,
                    max_tokens=2000
                )
                
                texto_resposta = response.choices[0].message.content
                st.markdown(texto_resposta)
                st.session_state.messages.append({"role": "assistant", "content": texto_resposta})
            
            except Exception as e:
                erro_msg = f"❌ Erro ao processar: {str(e)}"
                st.error(erro_msg)
                st.session_state.messages.append({"role": "assistant", "content": erro_msg})

# ============================================================================
# RODAPÉ
# ============================================================================

st.divider()

st.markdown("""
<div style="text-align: center; padding: 20px; color: #CBD5E1; font-size: 12px;">
    <p>GPlan IA 2.0 — Copiloto Master de Gestão de Projetos</p>
    <p>Desenvolvido com IA avançada, análise de dados e engenharia de software profissional</p>
    <p style="margin-top: 10px; color: #64748B;">© 2024 | Todos os direitos reservados</p>
</div>
""", unsafe_allow_html=True)

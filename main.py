"""
GPlan IA 5.0 - Enterprise Project Management with AI
Streamlit Application - Complete Implementation
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import google.generativeai as genai
from typing import Optional, List, Dict, Any
import warnings
warnings.filterwarnings("ignore")

# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="GPlan IA 5.0 Enterprise",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ STYLING ============
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a0e17 0%, #0f1419 100%);
    }
    
    [data-testid="stSidebar"] {
        background: #111827;
        border-right: 1px solid #1f2937;
    }
    
    h1, h2, h3 {
        color: #60a5fa;
        font-weight: 700;
    }
    
    .metric-card {
        background: #1f2937;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .status-active { background: #10b981; color: white; }
    .status-pending { background: #f59e0b; color: white; }
    .status-completed { background: #3b82f6; color: white; }
    .status-blocked { background: #ef4444; color: white; }
    .status-planning { background: #6b7280; color: white; }
    
    .priority-critical { color: #ef4444; font-weight: 700; }
    .priority-high { color: #f59e0b; font-weight: 600; }
    .priority-medium { color: #3b82f6; font-weight: 600; }
    .priority-low { color: #10b981; font-weight: 600; }
    
    .risk-high { color: #ef4444; }
    .risk-medium { color: #f59e0b; }
    .risk-low { color: #10b981; }
</style>
""", unsafe_allow_html=True)

# ============ INITIALIZATION ============
@st.cache_resource
def init_gemini():
    """Initialize Gemini API"""
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        st.warning("⚠️ GEMINI_API_KEY não configurada. Configure em .streamlit/secrets.toml")
        return None
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction="Você é GPlan IA 5.0, assistente sênior de gerenciamento de projetos. Responda em PT-BR profissional, detalhado, com análises acionáveis e recomendações estratégicas."
        )
    except Exception as e:
        st.error(f"Erro ao inicializar Gemini: {e}")
        return None

# ============ SESSION STATE ============
if "projects" not in st.session_state:
    st.session_state.projects = {}
if "current_project" not in st.session_state:
    st.session_state.current_project = None
if "tasks" not in st.session_state:
    st.session_state.tasks = {}
if "risks" not in st.session_state:
    st.session_state.risks = {}
if "notifications" not in st.session_state:
    st.session_state.notifications = []
if "audit_log" not in st.session_state:
    st.session_state.audit_log = []

# ============ HELPER FUNCTIONS ============
def add_audit_log(action: str, entity_type: str, entity_id: str, changes: Optional[Dict] = None):
    """Log all changes for audit trail"""
    st.session_state.audit_log.append({
        "timestamp": datetime.now(),
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "changes": changes or {},
        "user": "current_user"
    })

def create_notification(title: str, message: str, notification_type: str = "info", severity: str = "info"):
    """Create intelligent notification"""
    st.session_state.notifications.append({
        "timestamp": datetime.now(),
        "title": title,
        "message": message,
        "type": notification_type,
        "severity": severity,
        "read": False
    })

def calculate_project_health(project_id: str) -> Dict[str, Any]:
    """Calculate project health metrics"""
    if project_id not in st.session_state.tasks:
        return {"health": "good", "score": 100, "status": "✓ Bom"}
    
    tasks = st.session_state.tasks[project_id]
    if not tasks:
        return {"health": "good", "score": 100, "status": "✓ Bom"}
    
    total = len(tasks)
    completed = sum(1 for t in tasks.values() if t["status"] == "completed")
    blocked = sum(1 for t in tasks.values() if t["status"] == "blocked")
    critical = sum(1 for t in tasks.values() if t["priority"] == "critical")
    
    score = (completed / total * 100) if total > 0 else 0
    score -= blocked * 10
    score -= critical * 5
    score = max(0, min(100, score))
    
    if score >= 80:
        return {"health": "excellent", "score": score, "status": "✓ Excelente"}
    elif score >= 60:
        return {"health": "good", "score": score, "status": "✓ Bom"}
    elif score >= 40:
        return {"health": "at_risk", "score": score, "status": "⚠ Em Risco"}
    else:
        return {"health": "critical", "score": score, "status": "✗ Crítico"}

def calculate_critical_path(project_id: str) -> List[str]:
    """Calculate critical path using task dependencies"""
    if project_id not in st.session_state.tasks:
        return []
    
    tasks = st.session_state.tasks[project_id]
    if not tasks:
        return []
    
    # Simple critical path: tasks with no predecessors or critical priority
    critical_tasks = []
    for task_id, task in tasks.items():
        if task.get("priority") == "critical" or not task.get("predecessors"):
            critical_tasks.append(task["name"])
    
    return critical_tasks

def analyze_risks_with_ai(project_id: str, gemini_model) -> List[Dict]:
    """Analyze project risks using Gemini AI"""
    if not gemini_model or project_id not in st.session_state.tasks:
        return []
    
    tasks = st.session_state.tasks[project_id]
    if not tasks:
        return []
    
    # Prepare context
    task_summary = "\n".join([
        f"- {t['name']}: Status={t['status']}, Priority={t['priority']}, Hours={t.get('estimated_hours', 0)}"
        for t in tasks.values()
    ])
    
    prompt = f"""Analise os seguintes riscos do projeto:

Tarefas:
{task_summary}

Identifique:
1. Riscos críticos baseados em dependências
2. Conflitos de recursos
3. Riscos de cronograma
4. Recomendações de mitigação

Responda em JSON com array de riscos contendo: title, description, probability (low/medium/high), impact (low/medium/high), mitigation."""
    
    try:
        response = gemini_model.generate_content(prompt)
        # Parse response - simplified for Streamlit
        return [{
            "title": "Análise de Riscos",
            "description": response.text[:200],
            "probability": "medium",
            "impact": "medium",
            "mitigation": "Implementar monitoramento contínuo"
        }]
    except Exception as e:
        st.error(f"Erro na análise de IA: {e}")
        return []

def export_to_json(project_id: str) -> str:
    """Export project data to JSON"""
    project = st.session_state.projects.get(project_id, {})
    tasks = st.session_state.tasks.get(project_id, {})
    risks = st.session_state.risks.get(project_id, [])
    
    export_data = {
        "project": project,
        "tasks": tasks,
        "risks": risks,
        "exported_at": datetime.now().isoformat()
    }
    
    return json.dumps(export_data, indent=2, default=str)

def export_to_csv(project_id: str) -> pd.DataFrame:
    """Export tasks to CSV"""
    if project_id not in st.session_state.tasks:
        return pd.DataFrame()
    
    tasks = st.session_state.tasks[project_id]
    data = []
    
    for task_id, task in tasks.items():
        data.append({
            "ID": task_id,
            "Nome": task["name"],
            "Status": task["status"],
            "Prioridade": task["priority"],
            "Data Início": task.get("start_date", ""),
            "Data Fim": task.get("end_date", ""),
            "Horas Estimadas": task.get("estimated_hours", 0),
            "Progresso": task.get("progress", 0),
            "Responsável": task.get("assigned_to", "")
        })
    
    return pd.DataFrame(data)

# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("### 📊 GPlan IA 5.0")
    st.markdown("Enterprise Project Management")
    st.divider()
    
    # Project Selection
    st.markdown("#### 📁 Projetos")
    
    if st.session_state.projects:
        project_names = list(st.session_state.projects.keys())
        selected = st.selectbox(
            "Selecione um projeto:",
            project_names,
            key="project_selector"
        )
        st.session_state.current_project = selected
    else:
        st.info("Nenhum projeto criado. Crie um novo projeto!")
    
    st.divider()
    
    # Create New Project
    st.markdown("#### ➕ Novo Projeto")
    with st.form("new_project_form", clear_on_submit=True):
        project_name = st.text_input("Nome do Projeto")
        project_desc = st.text_area("Descrição", height=80)
        methodology = st.selectbox("Metodologia", ["Agile", "Waterfall", "Híbrida"])
        budget = st.number_input("Orçamento (R$)", min_value=0.0, step=1000.0)
        
        if st.form_submit_button("✨ Criar Projeto", use_container_width=True):
            if project_name:
                project_id = f"proj_{len(st.session_state.projects) + 1}"
                st.session_state.projects[project_name] = {
                    "id": project_id,
                    "name": project_name,
                    "description": project_desc,
                    "methodology": methodology,
                    "budget": budget,
                    "status": "planning",
                    "created_at": datetime.now(),
                    "progress": 0
                }
                st.session_state.tasks[project_name] = {}
                st.session_state.risks[project_name] = []
                st.session_state.current_project = project_name
                add_audit_log("create", "project", project_id)
                create_notification("Projeto Criado", f"Projeto '{project_name}' foi criado com sucesso", "completion", "info")
                st.success("✅ Projeto criado com sucesso!")
                st.rerun()
            else:
                st.error("Nome do projeto é obrigatório")
    
    st.divider()
    
    # Quick Actions
    if st.session_state.current_project:
        st.markdown("#### ⚡ Ações Rápidas")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Análise IA", use_container_width=True):
                st.session_state.show_ai_analysis = True
        with col2:
            if st.button("📋 Relatório", use_container_width=True):
                st.session_state.show_report = True
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Exportar", use_container_width=True):
                st.session_state.show_export = True
        with col2:
            if st.button("📜 Auditoria", use_container_width=True):
                st.session_state.show_audit = True
    
    st.divider()
    
    # Notifications
    if st.session_state.notifications:
        st.markdown("#### 🔔 Notificações")
        unread = sum(1 for n in st.session_state.notifications if not n["read"])
        st.info(f"**{unread}** notificações não lidas")
        
        for notif in st.session_state.notifications[-3:]:
            severity_color = "🔴" if notif["severity"] == "critical" else "🟡" if notif["severity"] == "warning" else "🟢"
            st.caption(f"{severity_color} {notif['title']}")

# ============ MAIN CONTENT ============
if not st.session_state.current_project:
    st.markdown("""
    <div style='text-align: center; padding: 4rem 2rem;'>
        <h1>👋 Bem-vindo ao GPlan IA 5.0</h1>
        <p style='font-size: 1.2rem; color: #9ca3af;'>Enterprise Project Management com IA</p>
        <br>
        <p style='color: #6b7280;'>Crie seu primeiro projeto na barra lateral para começar</p>
    </div>
    """, unsafe_allow_html=True)
else:
    project = st.session_state.projects[st.session_state.current_project]
    
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"# {project['name']}")
        st.caption(project['description'])
    with col2:
        st.metric("Metodologia", project['methodology'])
    with col3:
        st.metric("Orçamento", f"R$ {project['budget']:,.0f}")
    
    st.divider()
    
    # Project Health & Progress
    health = calculate_project_health(st.session_state.current_project)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Progresso", f"{project['progress']:.0f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Saúde", f"{health['score']:.0f}%")
        st.markdown(f"<p style='color: #60a5fa;'>{health['status']}</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        tasks = st.session_state.tasks.get(st.session_state.current_project, {})
        completed = sum(1 for t in tasks.values() if t["status"] == "completed")
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Tarefas", f"{len(tasks)}")
        st.markdown(f"<p style='color: #10b981;'>{completed} concluídas</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        critical_path = calculate_critical_path(st.session_state.current_project)
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Caminho Crítico", len(critical_path))
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "✅ Tarefas", "⚠️ Riscos", "📈 Análise", "📋 Relatórios"])
    
    # ============ TAB 1: DASHBOARD ============
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Distribuição de Status")
            tasks = st.session_state.tasks.get(st.session_state.current_project, {})
            
            if tasks:
                status_counts = {
                    "Concluído": sum(1 for t in tasks.values() if t["status"] == "completed"),
                    "Em Progresso": sum(1 for t in tasks.values() if t["status"] == "in_progress"),
                    "Bloqueado": sum(1 for t in tasks.values() if t["status"] == "blocked"),
                    "Não Iniciado": sum(1 for t in tasks.values() if t["status"] == "not_started")
                }
                
                fig = go.Figure(data=[go.Pie(
                    labels=list(status_counts.keys()),
                    values=list(status_counts.values()),
                    marker=dict(colors=["#10b981", "#3b82f6", "#ef4444", "#6b7280"])
                )])
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#1f2937",
                    font=dict(color="#e2e8f0"),
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhuma tarefa adicionada")
        
        with col2:
            st.markdown("### Distribuição por Prioridade")
            
            if tasks:
                priority_counts = {
                    "Crítica": sum(1 for t in tasks.values() if t["priority"] == "critical"),
                    "Alta": sum(1 for t in tasks.values() if t["priority"] == "high"),
                    "Média": sum(1 for t in tasks.values() if t["priority"] == "medium"),
                    "Baixa": sum(1 for t in tasks.values() if t["priority"] == "low")
                }
                
                fig = go.Figure(data=[go.Bar(
                    x=list(priority_counts.keys()),
                    y=list(priority_counts.values()),
                    marker=dict(color=["#ef4444", "#f59e0b", "#3b82f6", "#10b981"])
                )])
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#1f2937",
                    font=dict(color="#e2e8f0"),
                    xaxis_title="Prioridade",
                    yaxis_title="Quantidade",
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhuma tarefa adicionada")
    
    # ============ TAB 2: TASKS ============
    with tab2:
        st.markdown("### ✅ Gerenciamento de Tarefas")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("#### Adicionar Nova Tarefa")
        with col2:
            if st.button("➕ Nova Tarefa", use_container_width=True):
                st.session_state.show_new_task = True
        
        if st.session_state.get("show_new_task", False):
            with st.form("new_task_form", clear_on_submit=True):
                task_name = st.text_input("Nome da Tarefa")
                task_desc = st.text_area("Descrição", height=60)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    priority = st.selectbox("Prioridade", ["low", "medium", "high", "critical"])
                with col2:
                    status = st.selectbox("Status", ["not_started", "in_progress", "completed", "blocked"])
                with col3:
                    hours = st.number_input("Horas Estimadas", min_value=0, step=1)
                
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Data Início")
                with col2:
                    end_date = st.date_input("Data Fim")
                
                if st.form_submit_button("✨ Criar Tarefa", use_container_width=True):
                    if task_name:
                        task_id = f"task_{len(st.session_state.tasks.get(st.session_state.current_project, {})) + 1}"
                        
                        if st.session_state.current_project not in st.session_state.tasks:
                            st.session_state.tasks[st.session_state.current_project] = {}
                        
                        st.session_state.tasks[st.session_state.current_project][task_id] = {
                            "id": task_id,
                            "name": task_name,
                            "description": task_desc,
                            "priority": priority,
                            "status": status,
                            "estimated_hours": hours,
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat(),
                            "progress": 0,
                            "created_at": datetime.now(),
                            "predecessors": []
                        }
                        
                        add_audit_log("create", "task", task_id)
                        create_notification("Tarefa Criada", f"Tarefa '{task_name}' foi adicionada", "completion")
                        st.success("✅ Tarefa criada!")
                        st.rerun()
                    else:
                        st.error("Nome da tarefa é obrigatório")
        
        st.divider()
        
        # Task List
        tasks = st.session_state.tasks.get(st.session_state.current_project, {})
        
        if tasks:
            st.markdown("#### Tarefas do Projeto")
            
            # Filter options
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_status = st.multiselect("Status", ["not_started", "in_progress", "completed", "blocked"], default=["not_started", "in_progress"])
            with col2:
                filter_priority = st.multiselect("Prioridade", ["low", "medium", "high", "critical"], default=["high", "critical"])
            with col3:
                sort_by = st.selectbox("Ordenar por", ["Prioridade", "Data", "Progresso"])
            
            # Display tasks
            for task_id, task in tasks.items():
                if task["status"] not in filter_status or task["priority"] not in filter_priority:
                    continue
                
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                
                with col1:
                    st.markdown(f"**{task['name']}**")
                    st.caption(task.get('description', ''))
                
                with col2:
                    priority_colors = {"critical": "🔴", "high": "🟠", "medium": "🔵", "low": "🟢"}
                    st.markdown(f"{priority_colors.get(task['priority'], '⚪')} {task['priority'].capitalize()}")
                
                with col3:
                    status_badges = {
                        "completed": "✅ Concluído",
                        "in_progress": "⏳ Em Progresso",
                        "blocked": "🚫 Bloqueado",
                        "not_started": "⭕ Não Iniciado"
                    }
                    st.markdown(status_badges.get(task['status'], task['status']))
                
                with col4:
                    new_status = st.selectbox(
                        "Atualizar",
                        ["not_started", "in_progress", "completed", "blocked"],
                        key=f"status_{task_id}",
                        label_visibility="collapsed"
                    )
                    if new_status != task['status']:
                        st.session_state.tasks[st.session_state.current_project][task_id]['status'] = new_status
                        add_audit_log("update", "task", task_id, {"status": new_status})
                        st.rerun()
                
                with col5:
                    if st.button("🗑️", key=f"delete_{task_id}"):
                        del st.session_state.tasks[st.session_state.current_project][task_id]
                        add_audit_log("delete", "task", task_id)
                        st.rerun()
                
                st.divider()
        else:
            st.info("Nenhuma tarefa adicionada. Crie uma nova tarefa para começar!")
    
    # ============ TAB 3: RISKS ============
    with tab3:
        st.markdown("### ⚠️ Análise de Riscos")
        
        gemini_model = init_gemini()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("#### Riscos Identificados")
        with col2:
            if st.button("🤖 Analisar com IA", use_container_width=True):
                if gemini_model:
                    with st.spinner("Analisando riscos..."):
                        risks = analyze_risks_with_ai(st.session_state.current_project, gemini_model)
                        st.session_state.risks[st.session_state.current_project] = risks
                        create_notification("Análise Concluída", "Análise de riscos completada", "risk", "info")
                        st.success("✅ Análise concluída!")
                else:
                    st.error("Gemini não configurado")
        
        st.divider()
        
        # Add Risk Form
        with st.form("new_risk_form", clear_on_submit=True):
            st.markdown("#### ➕ Adicionar Risco")
            
            risk_title = st.text_input("Título do Risco")
            risk_desc = st.text_area("Descrição", height=80)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                probability = st.selectbox("Probabilidade", ["low", "medium", "high"])
            with col2:
                impact = st.selectbox("Impacto", ["low", "medium", "high"])
            with col3:
                risk_status = st.selectbox("Status", ["identified", "mitigating", "mitigated", "accepted"])
            
            mitigation = st.text_area("Plano de Mitigação", height=80)
            
            if st.form_submit_button("✨ Adicionar Risco", use_container_width=True):
                if risk_title:
                    risk_id = f"risk_{len(st.session_state.risks.get(st.session_state.current_project, [])) + 1}"
                    
                    if st.session_state.current_project not in st.session_state.risks:
                        st.session_state.risks[st.session_state.current_project] = []
                    
                    # Calculate risk score
                    prob_map = {"low": 1, "medium": 2, "high": 3}
                    impact_map = {"low": 1, "medium": 2, "high": 3}
                    risk_score = (prob_map[probability] * impact_map[impact]) / 9
                    
                    st.session_state.risks[st.session_state.current_project].append({
                        "id": risk_id,
                        "title": risk_title,
                        "description": risk_desc,
                        "probability": probability,
                        "impact": impact,
                        "risk_score": risk_score,
                        "status": risk_status,
                        "mitigation": mitigation,
                        "created_at": datetime.now()
                    })
                    
                    add_audit_log("create", "risk", risk_id)
                    create_notification("Risco Adicionado", f"Risco '{risk_title}' foi registrado", "risk", "warning")
                    st.success("✅ Risco adicionado!")
                    st.rerun()
                else:
                    st.error("Título do risco é obrigatório")
        
        st.divider()
        
        # Display Risks
        risks = st.session_state.risks.get(st.session_state.current_project, [])
        
        if risks:
            st.markdown("#### Riscos do Projeto")
            
            for risk in sorted(risks, key=lambda x: x['risk_score'], reverse=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    severity_color = "🔴" if risk['risk_score'] > 0.6 else "🟡" if risk['risk_score'] > 0.3 else "🟢"
                    st.markdown(f"**{severity_color} {risk['title']}**")
                    st.caption(risk['description'])
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        prob_emoji = "🔴" if risk['probability'] == "high" else "🟡" if risk['probability'] == "medium" else "🟢"
                        st.caption(f"{prob_emoji} Probabilidade: {risk['probability'].capitalize()}")
                    with col_b:
                        impact_emoji = "🔴" if risk['impact'] == "high" else "🟡" if risk['impact'] == "medium" else "🟢"
                        st.caption(f"{impact_emoji} Impacto: {risk['impact'].capitalize()}")
                    with col_c:
                        st.caption(f"Score: {risk['risk_score']:.2f}")
                    
                    st.markdown(f"**Mitigação:** {risk['mitigation']}")
                
                with col2:
                    new_status = st.selectbox(
                        "Status",
                        ["identified", "mitigating", "mitigated", "accepted"],
                        key=f"risk_status_{risk['id']}",
                        label_visibility="collapsed"
                    )
                    if new_status != risk['status']:
                        risk['status'] = new_status
                        st.rerun()
                
                st.divider()
        else:
            st.info("Nenhum risco identificado. Adicione um risco ou use análise com IA!")
    
    # ============ TAB 4: ANALYSIS ============
    with tab4:
        st.markdown("### 📈 Análise Inteligente")
        
        gemini_model = init_gemini()
        
        if gemini_model:
            analysis_type = st.selectbox(
                "Tipo de Análise",
                ["Resumo Executivo", "Análise de Riscos", "Plano 5W2H", "Relatório de Métricas"]
            )
            
            if st.button("🔍 Gerar Análise", use_container_width=True):
                with st.spinner("Gerando análise..."):
                    tasks = st.session_state.tasks.get(st.session_state.current_project, {})
                    risks = st.session_state.risks.get(st.session_state.current_project, [])
                    
                    task_summary = "\n".join([
                        f"- {t['name']}: {t['status']} ({t['priority']})"
                        for t in tasks.values()
                    ])
                    
                    risk_summary = "\n".join([
                        f"- {r['title']}: {r['probability']} probability, {r['impact']} impact"
                        for r in risks
                    ])
                    
                    prompts = {
                        "Resumo Executivo": f"Crie um resumo executivo profissional para o projeto '{project['name']}':\n\nTarefas:\n{task_summary}\n\nRiscos:\n{risk_summary}",
                        "Análise de Riscos": f"Analise os riscos do projeto e sugira estratégias de mitigação:\n\n{risk_summary}",
                        "Plano 5W2H": f"Crie um plano 5W2H para o projeto '{project['name']}':\n\nTarefas:\n{task_summary}",
                        "Relatório de Métricas": f"Gere um relatório de métricas do projeto:\n\nTarefas:\n{task_summary}\n\nRiscos:\n{risk_summary}"
                    }
                    
                    try:
                        response = gemini_model.generate_content(prompts[analysis_type])
                        st.markdown(response.text)
                        
                        # Export analysis
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                "📥 Baixar como Texto",
                                response.text,
                                file_name=f"analise_{analysis_type.lower().replace(' ', '_')}.txt"
                            )
                        with col2:
                            st.download_button(
                                "📥 Baixar como JSON",
                                json.dumps({"analysis": response.text, "type": analysis_type}, indent=2),
                                file_name=f"analise_{analysis_type.lower().replace(' ', '_')}.json"
                            )
                    except Exception as e:
                        st.error(f"Erro na análise: {e}")
        else:
            st.warning("⚠️ Gemini não configurado. Configure GEMINI_API_KEY em .streamlit/secrets.toml")
    
    # ============ TAB 5: REPORTS ============
    with tab5:
        st.markdown("### 📋 Relatórios e Exportação")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📥 Exportar Dados")
            
            if st.button("📊 Exportar como CSV", use_container_width=True):
                df = export_to_csv(st.session_state.current_project)
                if not df.empty:
                    st.download_button(
                        "Baixar CSV",
                        df.to_csv(index=False),
                        file_name=f"projeto_{st.session_state.current_project.lower().replace(' ', '_')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("Nenhuma tarefa para exportar")
            
            if st.button("📄 Exportar como JSON", use_container_width=True):
                json_data = export_to_json(st.session_state.current_project)
                st.download_button(
                    "Baixar JSON",
                    json_data,
                    file_name=f"projeto_{st.session_state.current_project.lower().replace(' ', '_')}.json",
                    mime="application/json"
                )
        
        with col2:
            st.markdown("#### 📜 Histórico")
            
            if st.button("📋 Ver Auditoria Completa", use_container_width=True):
                st.markdown("#### Log de Auditoria")
                
                if st.session_state.audit_log:
                    audit_df = pd.DataFrame(st.session_state.audit_log)
                    st.dataframe(audit_df, use_container_width=True)
                    
                    st.download_button(
                        "📥 Baixar Log",
                        audit_df.to_csv(index=False),
                        file_name="audit_log.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("Nenhuma atividade registrada")
        
        st.divider()
        
        # Project Summary
        st.markdown("#### 📊 Resumo do Projeto")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Status", project['status'].capitalize())
        with col2:
            st.metric("Metodologia", project['methodology'])
        with col3:
            st.metric("Criado em", project['created_at'].strftime("%d/%m/%Y"))
        
        st.divider()
        
        # Project Statistics
        tasks = st.session_state.tasks.get(st.session_state.current_project, {})
        risks = st.session_state.risks.get(st.session_state.current_project, [])
        
        st.markdown("#### 📈 Estatísticas")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Tarefas", len(tasks))
        with col2:
            completed = sum(1 for t in tasks.values() if t['status'] == 'completed')
            st.metric("Tarefas Concluídas", completed)
        with col3:
            critical_tasks = sum(1 for t in tasks.values() if t['priority'] == 'critical')
            st.metric("Tarefas Críticas", critical_tasks)
        with col4:
            high_risks = sum(1 for r in risks if r['risk_score'] > 0.5)
            st.metric("Riscos Altos", high_risks)

# ============ FOOTER ============
st.divider()
st.markdown("""
<div style='text-align: center; color: #6b7280; padding: 2rem;'>
    <p>GPlan IA 5.0 Enterprise Edition • Powered by Gemini • 2026</p>
    <p style='font-size: 0.875rem;'>Gerenciamento inteligente de projetos com análise de IA</p>
</div>
""", unsafe_allow_html=True)

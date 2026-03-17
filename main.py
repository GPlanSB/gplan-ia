"""
GPlan IA 5.0 - AI Project Management Assistant
Conversational Chatbot for Project Management
"""

import os
import json
import pickle
from datetime import datetime
from typing import Optional, List, Dict, Any
import google.generativeai as genai
from pathlib import Path

# ============ CONFIGURATION ============
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=API_KEY)

# ============ DATA STORAGE ============
DATA_DIR = Path("gplan_data")
DATA_DIR.mkdir(exist_ok=True)

PROJECTS_FILE = DATA_DIR / "projects.json"
CONVERSATIONS_FILE = DATA_DIR / "conversations.pkl"
AUDIT_LOG_FILE = DATA_DIR / "audit_log.json"

# ============ INITIALIZE DATA ============
def load_projects() -> Dict:
    """Load projects from file"""
    if PROJECTS_FILE.exists():
        with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_projects(projects: Dict):
    """Save projects to file"""
    with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(projects, f, indent=2, ensure_ascii=False, default=str)

def load_conversations() -> List:
    """Load conversation history"""
    if CONVERSATIONS_FILE.exists():
        with open(CONVERSATIONS_FILE, 'rb') as f:
            return pickle.load(f)
    return []

def save_conversations(conversations: List):
    """Save conversation history"""
    with open(CONVERSATIONS_FILE, 'wb') as f:
        pickle.dump(conversations, f)

def load_audit_log() -> List:
    """Load audit log"""
    if AUDIT_LOG_FILE.exists():
        with open(AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_audit_log(audit_log: List):
    """Save audit log"""
    with open(AUDIT_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(audit_log, f, indent=2, ensure_ascii=False, default=str)

def add_audit_entry(action: str, details: str, project_id: Optional[str] = None):
    """Add entry to audit log"""
    audit_log = load_audit_log()
    audit_log.append({
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details,
        "project_id": project_id
    })
    save_audit_log(audit_log)

# ============ SYSTEM PROMPT ============
SYSTEM_PROMPT = """Você é GPlan IA 5.0, um assistente sênior de gerenciamento de projetos com expertise em:

✓ Planejamento estratégico de projetos
✓ Análise de riscos e mitigação
✓ Alocação de recursos e equipes
✓ Cronogramas e timelines
✓ Metodologias (Agile, Waterfall, Híbrida)
✓ Métricas e KPIs
✓ Relatórios executivos
✓ Comunicação com stakeholders

SUAS RESPONSABILIDADES:
1. Ajudar a criar e estruturar projetos
2. Analisar tarefas e dependências
3. Identificar e mitigar riscos
4. Calcular cronogramas críticos
5. Alocar recursos eficientemente
6. Gerar insights e recomendações
7. Criar relatórios profissionais
8. Responder dúvidas sobre gerenciamento

DADOS DISPONÍVEIS:
Você tem acesso a todos os projetos, tarefas, riscos e histórico. Sempre que o usuário mencionar um projeto, tarefa ou risco, use os dados reais para fornecer análises precisas.

ESTILO DE COMUNICAÇÃO:
- Profissional mas acessível
- Direto e acionável
- Com dados e números quando possível
- Proativo em sugerir melhorias
- Estruturado em listas quando apropriado
- Sempre em português brasileiro

QUANDO O USUÁRIO PEDIR:
- "Criar projeto": Colete nome, descrição, metodologia, orçamento, datas
- "Adicionar tarefa": Colete nome, prioridade, estimativa, dependências
- "Analisar riscos": Identifique riscos, calcule scores, sugira mitigações
- "Relatório": Gere insights baseado nos dados reais
- "Status": Forneça visão geral do projeto com métricas
- "Recomendações": Sugira ações baseadas em análise de dados

FORMATO DE RESPOSTA:
Use markdown para estruturar respostas:
- **Negrito** para títulos
- - Listas para pontos
- > Citações para destaques
- `Código` para dados estruturados

NUNCA:
- Minta sobre dados que não tem
- Crie dados fictícios sem avisar
- Ignore o contexto do projeto
- Seja genérico demais
"""

# ============ PROJECT MANAGEMENT FUNCTIONS ============
def create_project(name: str, description: str, methodology: str, budget: float, start_date: str, end_date: str) -> Dict:
    """Create a new project"""
    projects = load_projects()
    project_id = f"proj_{len(projects) + 1}_{int(datetime.now().timestamp())}"
    
    project = {
        "id": project_id,
        "name": name,
        "description": description,
        "methodology": methodology,
        "budget": budget,
        "start_date": start_date,
        "end_date": end_date,
        "status": "planning",
        "created_at": datetime.now().isoformat(),
        "tasks": {},
        "risks": [],
        "resources": [],
        "metrics": {
            "progress": 0,
            "health": "good",
            "completed_tasks": 0,
            "total_tasks": 0
        }
    }
    
    projects[project_id] = project
    save_projects(projects)
    add_audit_entry("CREATE_PROJECT", f"Projeto '{name}' criado", project_id)
    
    return project

def add_task(project_id: str, name: str, description: str, priority: str, estimated_hours: float, dependencies: List[str] = None) -> Dict:
    """Add task to project"""
    projects = load_projects()
    
    if project_id not in projects:
        return {"error": f"Projeto {project_id} não encontrado"}
    
    task_id = f"task_{len(projects[project_id]['tasks']) + 1}"
    
    task = {
        "id": task_id,
        "name": name,
        "description": description,
        "priority": priority,
        "status": "not_started",
        "estimated_hours": estimated_hours,
        "actual_hours": 0,
        "progress": 0,
        "dependencies": dependencies or [],
        "created_at": datetime.now().isoformat()
    }
    
    projects[project_id]["tasks"][task_id] = task
    projects[project_id]["metrics"]["total_tasks"] += 1
    
    save_projects(projects)
    add_audit_entry("ADD_TASK", f"Tarefa '{name}' adicionada", project_id)
    
    return task

def add_risk(project_id: str, title: str, description: str, probability: str, impact: str, mitigation: str) -> Dict:
    """Add risk to project"""
    projects = load_projects()
    
    if project_id not in projects:
        return {"error": f"Projeto {project_id} não encontrado"}
    
    risk_id = f"risk_{len(projects[project_id]['risks']) + 1}"
    
    # Calculate risk score
    prob_map = {"low": 1, "medium": 2, "high": 3}
    impact_map = {"low": 1, "medium": 2, "high": 3}
    risk_score = (prob_map.get(probability, 1) * impact_map.get(impact, 1)) / 9
    
    risk = {
        "id": risk_id,
        "title": title,
        "description": description,
        "probability": probability,
        "impact": impact,
        "risk_score": risk_score,
        "mitigation": mitigation,
        "status": "identified",
        "created_at": datetime.now().isoformat()
    }
    
    projects[project_id]["risks"].append(risk)
    save_projects(projects)
    add_audit_entry("ADD_RISK", f"Risco '{title}' identificado", project_id)
    
    return risk

def get_project_summary(project_id: str) -> Dict:
    """Get comprehensive project summary"""
    projects = load_projects()
    
    if project_id not in projects:
        return {"error": f"Projeto {project_id} não encontrado"}
    
    project = projects[project_id]
    tasks = project.get("tasks", {})
    risks = project.get("risks", [])
    
    # Calculate metrics
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks.values() if t["status"] == "completed")
    in_progress = sum(1 for t in tasks.values() if t["status"] == "in_progress")
    blocked = sum(1 for t in tasks.values() if t["status"] == "blocked")
    
    critical_tasks = sum(1 for t in tasks.values() if t["priority"] == "critical")
    high_risks = sum(1 for r in risks if r["risk_score"] > 0.5)
    
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Calculate health
    health_score = progress - (blocked * 10) - (critical_tasks * 5)
    health_score = max(0, min(100, health_score))
    
    if health_score >= 80:
        health = "excelente"
    elif health_score >= 60:
        health = "bom"
    elif health_score >= 40:
        health = "em_risco"
    else:
        health = "crítico"
    
    return {
        "project": project,
        "metrics": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress": in_progress,
            "blocked": blocked,
            "critical_tasks": critical_tasks,
            "progress": progress,
            "health": health,
            "health_score": health_score,
            "high_risks": high_risks,
            "total_risks": len(risks)
        },
        "tasks": tasks,
        "risks": risks
    }

def list_projects() -> List[Dict]:
    """List all projects"""
    projects = load_projects()
    project_list = []
    
    for project_id, project in projects.items():
        summary = get_project_summary(project_id)
        if "error" not in summary:
            project_list.append({
                "id": project_id,
                "name": project["name"],
                "status": project["status"],
                "methodology": project["methodology"],
                "progress": summary["metrics"]["progress"],
                "health": summary["metrics"]["health"]
            })
    
    return project_list

def update_task_status(project_id: str, task_id: str, status: str) -> Dict:
    """Update task status"""
    projects = load_projects()
    
    if project_id not in projects:
        return {"error": f"Projeto {project_id} não encontrado"}
    
    if task_id not in projects[project_id]["tasks"]:
        return {"error": f"Tarefa {task_id} não encontrada"}
    
    old_status = projects[project_id]["tasks"][task_id]["status"]
    projects[project_id]["tasks"][task_id]["status"] = status
    
    if status == "completed":
        projects[project_id]["tasks"][task_id]["progress"] = 100
        projects[project_id]["metrics"]["completed_tasks"] += 1
    
    save_projects(projects)
    add_audit_entry("UPDATE_TASK", f"Status alterado de {old_status} para {status}", project_id)
    
    return projects[project_id]["tasks"][task_id]

# ============ AI ANALYSIS FUNCTIONS ============
def analyze_with_ai(prompt: str, context: Optional[Dict] = None) -> str:
    """Use Gemini to analyze and provide insights"""
    try:
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=SYSTEM_PROMPT
        )
        
        # Build context message
        full_prompt = prompt
        if context:
            context_str = json.dumps(context, indent=2, ensure_ascii=False, default=str)
            full_prompt = f"Contexto dos dados do projeto:\n```json\n{context_str}\n```\n\nPergunta do usuário: {prompt}"
        
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Erro ao analisar: {str(e)}"

# ============ CONVERSATION MANAGEMENT ============
class ProjectAssistant:
    def __init__(self):
        self.conversation_history = []
        self.current_project = None
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=SYSTEM_PROMPT
        )
    
    def set_current_project(self, project_id: str):
        """Set the current project context"""
        projects = load_projects()
        if project_id in projects:
            self.current_project = project_id
            return f"✓ Projeto '{projects[project_id]['name']}' selecionado"
        return f"✗ Projeto {project_id} não encontrado"
    
    def get_context_prompt(self) -> str:
        """Build context prompt with current project data"""
        if not self.current_project:
            return ""
        
        summary = get_project_summary(self.current_project)
        if "error" in summary:
            return ""
        
        context = f"""
CONTEXTO ATUAL DO PROJETO:
Projeto: {summary['project']['name']}
Status: {summary['project']['status']}
Metodologia: {summary['project']['methodology']}

MÉTRICAS:
- Progresso: {summary['metrics']['progress']:.1f}%
- Saúde: {summary['metrics']['health']}
- Tarefas: {summary['metrics']['completed_tasks']}/{summary['metrics']['total_tasks']} concluídas
- Tarefas Críticas: {summary['metrics']['critical_tasks']}
- Riscos Altos: {summary['metrics']['high_risks']}/{summary['metrics']['total_risks']}

TAREFAS PRINCIPAIS:
{self._format_tasks(summary['tasks'])}

RISCOS IDENTIFICADOS:
{self._format_risks(summary['risks'])}
"""
        return context
    
    def _format_tasks(self, tasks: Dict) -> str:
        """Format tasks for context"""
        if not tasks:
            return "Nenhuma tarefa adicionada"
        
        formatted = []
        for task_id, task in list(tasks.items())[:5]:  # Show top 5
            formatted.append(f"- {task['name']} ({task['priority']}) - {task['status']}")
        
        return "\n".join(formatted)
    
    def _format_risks(self, risks: List) -> str:
        """Format risks for context"""
        if not risks:
            return "Nenhum risco identificado"
        
        formatted = []
        for risk in sorted(risks, key=lambda x: x['risk_score'], reverse=True)[:5]:
            formatted.append(f"- {risk['title']} (Score: {risk['risk_score']:.2f}) - {risk['status']}")
        
        return "\n".join(formatted)
    
    def chat(self, user_message: str) -> str:
        """Process user message and return AI response"""
        # Add context if project is selected
        context_prompt = self.get_context_prompt()
        
        # Build full message with context
        if context_prompt:
            full_message = f"{context_prompt}\n\nMensagem do usuário: {user_message}"
        else:
            full_message = user_message
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Get AI response
        try:
            response = self.model.generate_content(full_message)
            ai_response = response.text
            
            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Save conversation
            save_conversations(self.conversation_history)
            
            return ai_response
        except Exception as e:
            error_msg = f"Erro ao processar mensagem: {str(e)}"
            return error_msg
    
    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        save_conversations([])

# ============ COMMAND PARSER ============
def parse_command(user_input: str, assistant: ProjectAssistant) -> Optional[str]:
    """Parse special commands"""
    lower_input = user_input.lower().strip()
    
    # List projects
    if lower_input in ["/projetos", "/projects", "/listar", "/list"]:
        projects = list_projects()
        if not projects:
            return "Nenhum projeto criado ainda."
        
        result = "📊 **Projetos Disponíveis:**\n\n"
        for p in projects:
            result += f"- **{p['name']}** (ID: {p['id']})\n"
            result += f"  Status: {p['status']} | Progresso: {p['progress']:.0f}% | Saúde: {p['health']}\n"
        return result
    
    # Show current project
    if lower_input in ["/projeto", "/current", "/atual"]:
        if assistant.current_project:
            summary = get_project_summary(assistant.current_project)
            if "error" not in summary:
                p = summary['project']
                m = summary['metrics']
                return f"""📌 **Projeto Atual: {p['name']}**

Status: {p['status']}
Metodologia: {p['methodology']}
Orçamento: R$ {p['budget']:,.2f}

**Métricas:**
- Progresso: {m['progress']:.1f}%
- Saúde: {m['health']}
- Tarefas: {m['completed_tasks']}/{m['total_tasks']} concluídas
- Riscos Altos: {m['high_risks']}
"""
        return "Nenhum projeto selecionado. Use /selecionar <id>"
    
    # Select project
    if lower_input.startswith("/selecionar ") or lower_input.startswith("/select "):
        project_id = user_input.split()[-1]
        return assistant.set_current_project(project_id)
    
    # Clear history
    if lower_input in ["/limpar", "/clear", "/reset"]:
        assistant.clear_history()
        return "✓ Histórico de conversa limpo"
    
    # Show help
    if lower_input in ["/ajuda", "/help", "/?"]:
        return """📖 **Comandos Disponíveis:**

**/projetos** - Listar todos os projetos
**/projeto** - Mostrar projeto atual
**/selecionar <id>** - Selecionar um projeto
**/limpar** - Limpar histórico de conversa
**/auditoria** - Ver log de auditoria
**/ajuda** - Mostrar esta mensagem
**/sair** - Sair da aplicação

**Exemplos de conversa:**
- "Criar um novo projeto de desenvolvimento mobile"
- "Adicionar tarefa de design da interface"
- "Analisar riscos do projeto"
- "Qual é o status do projeto?"
- "Recomendar ações para melhorar a saúde"
"""
    
    # Show audit log
    if lower_input in ["/auditoria", "/audit", "/log"]:
        audit_log = load_audit_log()
        if not audit_log:
            return "Nenhuma atividade registrada"
        
        result = "📜 **Log de Auditoria (últimas 10 ações):**\n\n"
        for entry in audit_log[-10:]:
            result += f"- **{entry['action']}** ({entry['timestamp']})\n"
            result += f"  {entry['details']}\n"
        return result
    
    return None

# ============ MAIN APPLICATION ============
def main():
    """Main application loop"""
    print("\n" + "="*70)
    print("  GPlan IA 5.0 - AI Project Management Assistant")
    print("="*70)
    print("\n👋 Bem-vindo! Sou seu assistente de gerenciamento de projetos.")
    print("📝 Digite /ajuda para ver os comandos disponíveis.")
    print("💬 Você pode conversar comigo naturalmente sobre seus projetos.\n")
    
    assistant = ProjectAssistant()
    
    while True:
        try:
            user_input = input("Você: ").strip()
            
            if not user_input:
                continue
            
            # Check for exit
            if user_input.lower() in ["/sair", "/exit", "sair", "exit", "quit"]:
                print("\n✓ Até logo! Seus projetos foram salvos.")
                break
            
            # Try to parse as command
            command_response = parse_command(user_input, assistant)
            if command_response:
                print(f"\nAssistente: {command_response}\n")
                continue
            
            # Regular conversation
            print("\n⏳ Processando...\n")
            response = assistant.chat(user_input)
            print(f"Assistente: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\n✓ Aplicação encerrada.")
            break
        except Exception as e:
            print(f"\n❌ Erro: {str(e)}\n")

if __name__ == "__main__":
    main()



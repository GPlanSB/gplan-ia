from services.gemini_service import GeminiService
from core.memory import Memory

class OrionAgent:

    def __init__(self):
        self.gemini = GeminiService()
        self.memory = Memory()

    def chat(self, user_input):
        context = self.memory.get_context()

        prompt = f"""
        Você é um HEAD de operações especialista em projetos, PCP, estoque, suprimentos e finanças.

        Contexto:
        {context}

        Usuário: {user_input}
        """

        response = self.gemini.generate(prompt)
        self.memory.add(user_input, response)

        return response

    def generate_plan(self, name, type_, deadline):
        prompt = f"""
        Crie um planejamento completo para:

        Projeto: {name}
        Tipo: {type_}
        Prazo: {deadline}

        Inclua cronograma, tarefas, riscos e sugestões operacionais.
        """

        return self.gemini.generate(prompt)

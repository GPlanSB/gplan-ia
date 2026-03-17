class Memory:

    def __init__(self):
        self.history = []

    def add(self, user, ai):
        self.history.append((user, ai))

    def get_context(self):
        context = ""
        for u, a in self.history[-5:]:
            context += f"Usuário: {u}\nORION: {a}\n"
        return context

class ContextAgent:
    def __init__(self, id, system_prompt, kb):
        self.id = id
        self.system_prompt = system_prompt
        self.kb = kb
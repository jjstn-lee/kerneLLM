class ReasoningAgent:
    def __init__(self, id, system_prompt, authorized_agents):
        self.id = id
        self.system_prompt = system_prompt
        # list of agents that the ReasoningAgent is authorized to interact with
        self.authorized_agents = authorized_agents
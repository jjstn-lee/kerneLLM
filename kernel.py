from dotenv import load_dotenv
from pathlib import Path
import os

from langchain.messages import HumanMessage

# need to override path bce of Claude Code :/
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path, override=True)

print("ANTHROPIC_API_KEY:", os.environ.get("ANTHROPIC_API_KEY"))

from agents.context_agents.spotify import SpotifyAgent


def read_config(config):
    open(config)
    return None
    
def run(agent):
    
    return None


# def create()


if __name__ == "__main__":
    spotify_agent = SpotifyAgent()
    print("🎵 Fetching your Spotify overview…\n")
    spotify_agent.agent.invoke(
        {"messages": [HumanMessage(content="What are my top tracks?")]}

    )
    
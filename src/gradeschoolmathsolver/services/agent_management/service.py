"""
Agent Management Service
Manages RAG bot configurations and tracks their performance
"""
import json
import os
from typing import List, Optional
from gradeschoolmathsolver.models import AgentConfig


class AgentManagementService:
    """Service for managing RAG bots"""

    def __init__(self, config_dir: str = "data/agents"):
        self.config_dir = config_dir
        self._ensure_directory()

    def _ensure_directory(self):
        """Ensure the configuration directory exists"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def _get_config_path(self, agent_name: str) -> str:
        """Get the config file path for an agent"""
        return os.path.join(self.config_dir, f"{agent_name}.json")

    def create_agent(self, config: AgentConfig) -> bool:
        """
        Create a new agent configuration

        Args:
            config: AgentConfig object

        Returns:
            True if successful, False if agent already exists
        """
        config_path = self._get_config_path(config.name)

        if os.path.exists(config_path):
            return False

        try:
            with open(config_path, 'w') as f:
                json.dump(config.model_dump(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error creating agent: {e}")
            return False

    def get_agent(self, agent_name: str) -> Optional[AgentConfig]:
        """
        Get agent configuration by name

        Args:
            agent_name: Name of the agent

        Returns:
            AgentConfig object or None if not found
        """
        config_path = self._get_config_path(agent_name)

        if not os.path.exists(config_path):
            return None

        try:
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
            return AgentConfig(**config_dict)
        except Exception as e:
            print(f"Error loading agent config: {e}")
            return None

    def list_agents(self) -> List[str]:
        """
        List all available agents

        Returns:
            List of agent names
        """
        if not os.path.exists(self.config_dir):
            return []

        agents = []
        for filename in os.listdir(self.config_dir):
            if filename.endswith('.json'):
                agent_name = filename[:-5]  # Remove .json extension
                agents.append(agent_name)

        return agents

    def update_agent(self, config: AgentConfig) -> bool:
        """
        Update an existing agent configuration

        Args:
            config: Updated AgentConfig object

        Returns:
            True if successful, False if agent doesn't exist
        """
        config_path = self._get_config_path(config.name)

        if not os.path.exists(config_path):
            return False

        try:
            with open(config_path, 'w') as f:
                json.dump(config.model_dump(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error updating agent: {e}")
            return False

    def delete_agent(self, agent_name: str) -> bool:
        """
        Delete an agent configuration

        Args:
            agent_name: Name of the agent to delete

        Returns:
            True if successful
        """
        config_path = self._get_config_path(agent_name)

        if not os.path.exists(config_path):
            return False

        try:
            os.remove(config_path)
            return True
        except Exception as e:
            print(f"Error deleting agent: {e}")
            return False

    def create_default_agents(self):
        """Create default agent configurations"""
        default_agents = [
            AgentConfig(
                name="basic_agent",
                use_classification=False,
                use_rag=False,
                rag_top_k=5,
                include_incorrect_history=True
            ),
            AgentConfig(
                name="classifier_agent",
                use_classification=True,
                use_rag=False,
                rag_top_k=5,
                include_incorrect_history=True
            ),
            AgentConfig(
                name="rag_agent",
                use_classification=True,
                use_rag=True,
                rag_top_k=5,
                include_incorrect_history=True
            ),
            AgentConfig(
                name="rag_correct_only",
                use_classification=True,
                use_rag=True,
                rag_top_k=3,
                include_incorrect_history=False
            )
        ]

        for agent in default_agents:
            if not self.get_agent(agent.name):
                self.create_agent(agent)
                print(f"Created default agent: {agent.name}")


if __name__ == "__main__":
    # Test the service
    service = AgentManagementService()

    # Create default agents
    service.create_default_agents()

    # List all agents
    agents = service.list_agents()
    print(f"Available agents: {agents}")

    # Get agent details
    for agent_name in agents:
        config = service.get_agent(agent_name)
        if config:
            print(f"\n{agent_name}:")
            print(f"  Classification: {config.use_classification}")
            print(f"  RAG: {config.use_rag}")
            print(f"  RAG Top-K: {config.rag_top_k}")

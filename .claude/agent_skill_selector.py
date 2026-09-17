"""
Claude Agent & Skill Selector

Dynamically load and execute BRD agents and skills from the registry.
Used by Claude to select which agent and skill to use.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class AgentSkillSelector:
    """Load and select agents and skills from registry."""
    
    def __init__(self):
        """Initialize selector and load registry."""
        registry_path = Path(__file__).parent / "skills.registry.json"
        with open(registry_path) as f:
            self.registry = json.load(f)
        self.skills = self.registry["skills"]
        self.agents = self.registry["agents"]
        self.workflows = self.registry["workflows"]
    
    def list_agents(self) -> Dict[str, Dict[str, str]]:
        """Return all available agents."""
        return self.agents
    
    def list_skills(self) -> Dict[str, Dict[str, Any]]:
        """Return all available skills."""
        return self.skills
    
    def get_agent(self, agent_num: int) -> Dict[str, Any]:
        """Get specific agent info."""
        return self.agents.get(str(agent_num))
    
    def get_skill(self, skill_name: str) -> Dict[str, Any]:
        """Get specific skill info."""
        return self.skills.get(skill_name)
    
    def get_agent_skills(self, agent_num: int) -> List[str]:
        """Get skills for specific agent."""
        agent = self.get_agent(agent_num)
        if agent:
            return agent.get("skills", [])
        return []
    
    def get_agents_by_skill(self, skill_name: str) -> List[int]:
        """Get all agents that use a skill."""
        skill = self.get_skill(skill_name)
        if skill:
            agents = skill.get("agents")
            if isinstance(agents, list):
                return agents
            return [skill.get("agent")]
        return []
    
    def select_agent(self, agent_num: int) -> str:
        """Select an agent (returns agent name)."""
        agent = self.get_agent(agent_num)
        if agent:
            return f"Agent {agent_num}: {agent['name']} ({agent['model']})"
        return f"Invalid agent {agent_num}"
    
    def select_skill(self, skill_name: str) -> str:
        """Select a skill (returns skill name)."""
        skill = self.get_skill(skill_name)
        if skill:
            return f"Skill: {skill['name']} ({skill['model']})"
        return f"Invalid skill {skill_name}"
    
    def select_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Select a workflow."""
        return self.workflows.get(workflow_name)
    
    def recommend_agents(self, task_type: str) -> List[int]:
        """Recommend agents based on task type."""
        recommendations = {
            "full-brd": [1, 2, 3, 4, 5, 6, 7, 8, 9],
            "discover": [1],
            "journeys": [2],
            "rules": [3],
            "gaps": [4],
            "synthesis": [5],
            "acceptance": [6],
            "risks": [7],
            "summary": [8],
            "knowledge-base": [9],
            "analysis": [1, 3, 4],
            "documents": [1, 5]
        }
        return recommendations.get(task_type, [])
    
    def print_agents_table(self):
        """Print formatted agent list."""
        print("\n" + "="*70)
        print("AVAILABLE AGENTS")
        print("="*70)
        for agent_id, agent_info in sorted(self.agents.items()):
            agent_num = int(agent_id)
            print(f"\n{agent_num}. {agent_info['name']}")
            print(f"   Model: {agent_info['model']}")
            print(f"   Complexity: {agent_info['complexity']}")
            print(f"   Description: {agent_info['description']}")
            print(f"   Skills: {', '.join(agent_info['skills'])}")
    
    def print_skills_table(self):
        """Print formatted skills list."""
        print("\n" + "="*70)
        print("AVAILABLE SKILLS")
        print("="*70)
        for skill_id, skill_info in sorted(self.skills.items()):
            print(f"\n{skill_info['name']} ({skill_id})")
            print(f"   Model: {skill_info['model']}")
            print(f"   Complexity: {skill_info['complexity']}")
            print(f"   Description: {skill_info['description']}")
            print(f"   Agents: {skill_info.get('agents', skill_info.get('agent', []))}")
    
    def get_best_agent_for_task(self, task: str) -> Dict[str, Any]:
        """Recommend best agent(s) for a task."""
        task_lower = task.lower()
        
        if any(word in task_lower for word in ["brd", "complete", "full", "all"]):
            return {"agents": [1,2,3,4,5,6,7,8,9], "workflow": "full-pipeline"}
        elif any(word in task_lower for word in ["discover", "scan", "catalog"]):
            return {"agents": [1], "workflow": "focused-analysis"}
        elif any(word in task_lower for word in ["journey", "flow", "process"]):
            return {"agents": [2], "workflow": "focused-analysis"}
        elif any(word in task_lower for word in ["rule", "business", "constraint"]):
            return {"agents": [3], "workflow": "focused-analysis"}
        elif any(word in task_lower for word in ["gap", "compare", "missing"]):
            return {"agents": [4], "workflow": "focused-analysis"}
        elif any(word in task_lower for word in ["accept", "test", "scenario"]):
            return {"agents": [6], "workflow": "focused-analysis"}
        elif any(word in task_lower for word in ["risk", "depend", "impact"]):
            return {"agents": [7], "workflow": "focused-analysis"}
        elif any(word in task_lower for word in ["summary", "executive"]):
            return {"agents": [8], "workflow": "focused-analysis"}
        elif any(word in task_lower for word in ["document", "spec", "include"]):
            return {"agents": [1,3,4,5], "workflow": "document-enriched"}
        else:
            return {"agents": [1,2,3,4,5,6,7,8,9], "workflow": "full-pipeline"}


def main():
    """Demo the selector."""
    selector = AgentSkillSelector()
    
    print("\n🤖 Claude BRD Agent & Skill Selector\n")
    
    # Show all agents
    selector.print_agents_table()
    
    # Show all skills
    selector.print_skills_table()
    
    # Demo recommendations
    print("\n" + "="*70)
    print("TASK RECOMMENDATIONS")
    print("="*70)
    
    tasks = [
        "Generate a complete BRD",
        "Extract business rules from the payment module",
        "Identify gaps in the implementation",
        "Assess technical risks",
        "Map user journeys"
    ]
    
    for task in tasks:
        recommendation = selector.get_best_agent_for_task(task)
        print(f"\nTask: {task}")
        print(f"  Agents: {recommendation['agents']}")
        print(f"  Workflow: {recommendation['workflow']}")
    
    print("\n✅ Selector ready for Claude to use!\n")


if __name__ == "__main__":
    main()

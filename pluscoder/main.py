#!/usr/bin/env python3
import asyncio
from pluscoder.setup import setup
from pluscoder.type import AgentState, TokenUsage
from pluscoder.workflow import run_workflow

# Run the workflow

def main():
    if not setup():
        return
    
    state = {
        "return_to_user": False,
        "messages": [], 
        "context_files": [],
        "orchestrator_state": AgentState.default(),
        "domain_stakeholder_state": AgentState.default(),
        "planning_state": AgentState.default(),
        "developer_state": AgentState.default(),
        "domain_expert_state": AgentState.default(),
        "accumulated_token_usage": TokenUsage.default(),
        "current_agent_deflections": 0,
        "max_agent_deflections": 3,
        }
    
    asyncio.run(run_workflow(state))

if __name__ == "__main__":
    main()

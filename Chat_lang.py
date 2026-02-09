import os
import re
import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from src.agent.config import AgentConfig
from src.agent.mcp_manager import MCPManager

# LangChain + MCP adapters
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_anthropic import ChatAnthropic  # or any LC model
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.agents import create_tool_calling_agent, AgentExecutor

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class SkillsAgentLC:
    """
    LangChain equivalent of your Claude SkillsAgent.

    - Loads AgentConfig from env
    - Spawns MCP servers via MultiServerMCPClient (STDIO)
    - Loads .claude/skills/*/SKILL.md and injects into prompt
    - Runs interactive chat loop
    - Filters verbose skill content from output (optional)
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

        # Load configuration
        self.config = AgentConfig.from_env()

        # MCP: build langchain MCP client config
        self.mcp_client_config = MCPManager.get_langchain_mcp_client_config(self.config)

        # Skills: load skill docs
        self.skills_text = self._load_skills_text()

        # Prompt
        self.system_prompt = self._build_system_prompt()

        # Runtime objects (init async)
        self.mcp_client: Optional[MultiServerMCPClient] = None
        self.tools = []
        self.agent_executor: Optional[AgentExecutor] = None

        # Log status
        try:
            server_status = MCPManager.format_server_status(self.config)
        except Exception:
            server_status = "✓ MCP server status available"
        logger.info(f"SkillsAgentLC initialized: {server_status}")

    async def init_async(self):
        """Async initialization to fetch MCP tools and build LC agent."""
        self.mcp_client = MultiServerMCPClient(self.mcp_client_config)
        self.tools = await self.mcp_client.get_tools()

        # Choose your model (Anthropic shown; can be OpenAI etc.)
        # Requires env like ANTHROPIC_API_KEY.
        model = ChatAnthropic(
            model=os.getenv("LC_MODEL", "claude-3-5-sonnet-latest"),
            temperature=float(os.getenv("LC_TEMPERATURE", "0.2")),
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                MessagesPlaceholder("messages"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(model, self.tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=self.verbose)

        logger.info(f"Tools available: {len(self.tools)} MCP tools")

    def get_welcome_message(self) -> str:
        enabled = []
        try:
            enabled = MCPManager.get_enabled_server_names(self.config)
        except Exception:
            enabled = list(self.mcp_client_config.keys())

        services = []
        if "confluence" in enabled:
            services.append("✅ Confluence - Search, create, update and manage documentation")
        if "servicenow" in enabled:
            services.append("✅ ServiceNow - Search and manage customer contact tickets")

        services_text = "\n".join(services) if services else "⚠️  No services configured"

        return f"""
================================================
🤖 Multi-Service AI Assistant (LangChain + MCP)
================================================

{MCPManager.format_server_status(self.config) if hasattr(MCPManager, "format_server_status") else ""}

Available Services:
{services_text}

💡 How it works:
- Skills are loaded from .claude/skills/*/SKILL.md (project-local)
- MCP tools are connected over STDIO and called by the agent
- Type 'quit' or 'exit' to end the conversation
================================================
""".strip()

    def _build_system_prompt(self) -> str:
        # Keep your “skills-first” behavior in the prompt itself.
        # LangChain won't auto-load Skills like Claude SDK; we provide them explicitly.
        base = (
            "You are an AI assistant with access to multiple services through MCP tools.\n\n"
            "CRITICAL WORKFLOW REQUIREMENT:\n"
            "When the user asks about a service (Confluence/ServiceNow/etc), first consult the relevant SKILL instructions below.\n"
            "Then call MCP tools as required and provide the final answer.\n\n"
        )

        if self.skills_text:
            base += "=== SKILLS (Project) ===\n" + self.skills_text + "\n\n"

        # Optional: you can add your existing minimal system prompt rules here
        return base

    def _load_skills_text(self) -> str:
        """
        Read .claude/skills/**/SKILL.md and concatenate.

        Matches your Claude SDK skills approach but in LangChain prompt form.
        """
        root = Path(os.getcwd())
        skills_dir = root / ".claude" / "skills"
        if not skills_dir.exists():
            return ""

        parts: List[str] = []
        for skill_md in skills_dir.glob("**/SKILL.md"):
            try:
                text = skill_md.read_text(encoding="utf-8", errors="ignore")
                # prefix with skill folder name for clarity
                skill_name = skill_md.parent.name
                parts.append(f"\n---\n# Skill: {skill_name}\n{text}\n")
            except Exception as e:
                logger.warning(f"Failed to read skill file {skill_md}: {e}")

        return "\n".join(parts).strip()

    def _is_skill_content(self, text: str) -> bool:
        """
        Your original heuristic preserved.
        Helps avoid dumping full SKILL.md contents back to console.
        """
        if not text:
            return False

        t = text.strip()

        # YAML front matter marker
        if t.startswith("---"):
            return True

        # common skill headers/markers
        if "# Confluence Integration" in t or "# Available Tools" in t:
            return True

        # long content that looks like a skill dump
        if len(t) > 500 and ("## Quick Start" in t or "###" in t):
            return True

        return False

    async def chat(self):
        if self.agent_executor is None:
            await self.init_async()

        print(self.get_welcome_message())

        messages = []  # conversation memory for agent prompt

        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in {"quit", "exit", "bye"}:
                    print("\nGoodbye! 👋")
                    break

                messages.append(HumanMessage(content=user_input))

                # LangChain agent invoke
                result = await self.agent_executor.ainvoke({"messages": messages})

                # AgentExecutor typically returns {"output": "..."} (plus metadata)
                output = result.get("output", "")

                # Optional: filter verbose skill dumps
                if self._is_skill_content(output):
                    # If it tries to return skill content, just suppress it
                    output = "(Skill content omitted)"

                print("\nAssistant:", output, "\n")

                # Save assistant response into conversation
                messages.append(SystemMessage(content=output))

            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye! 👋")
                break
            except Exception as e:
                logger.error(f"Error in chat loop: {e}", exc_info=True)
                print(f"\n❌ Error: {e}\n")


async def main():
    agent = SkillsAgentLC(verbose=True)
    await agent.chat()


if __name__ == "__main__":
    asyncio.run(main())

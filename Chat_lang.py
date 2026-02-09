import os
import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from src.agent.config import AgentConfig
from src.agent.mcp_manager import MCPManager

from langchain.agents import create_agent  # LangChain v1 API
from langchain_mcp_adapters.client import MultiServerMCPClient

# Choose ONE model provider:
from langchain_anthropic import ChatAnthropic  # if you're using Anthropic

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


class SkillsAgentLangChain:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.config = AgentConfig.from_env()

        # MCP client config: {"confluence": {"transport": "stdio", "command": "...", "args": [...]}, ...}
        self.mcp_client_config = MCPManager.get_langchain_mcp_client_config(self.config)

        # Load skills text from .claude/skills/**/SKILL.md
        self.skills_text = self._load_skills_text()

        # Build system prompt (your “skills-first” behavior)
        self.system_prompt = self._build_system_prompt()

        self.mcp_client: Optional[MultiServerMCPClient] = None
        self.tools = []
        self.agent = None

        logger.info(MCPManager.format_server_status(self.config))

    async def init_async(self):
        # 1) Connect MCP tools (stdio)
        self.mcp_client = MultiServerMCPClient(self.mcp_client_config)
        self.tools = await self.mcp_client.get_tools()
        logger.info("Loaded %s MCP tools", len(self.tools))

        # 2) Create model instance (recommended approach in v1 docs)
        model = ChatAnthropic(
            model=os.getenv("LC_MODEL", "claude-3-5-sonnet-latest"),
            temperature=float(os.getenv("LC_TEMPERATURE", "0.2")),
        )

        # 3) Build agent (LangChain v1)
        # create_agent runs a loop internally: model -> tools -> model ... until done
        self.agent = create_agent(
            model=model,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )

    def get_welcome_message(self) -> str:
        enabled = MCPManager.get_enabled_server_names(self.config)

        services = []
        if "confluence" in enabled:
            services.append("✅ Confluence - Search, create, update, manage documentation")
        if "servicenow" in enabled:
            services.append("✅ ServiceNow - Search and manage tickets")

        services_text = "\n".join(services) if services else "⚠️  No services configured"

        return f"""
================================================
🤖 Multi-Service AI Assistant (LangChain v1 + MCP)
================================================
{MCPManager.format_server_status(self.config)}

Available Services:
{services_text}

How it works:
- Skills loaded from .claude/skills/**/SKILL.md (project-local)
- MCP tools connected over STDIO
- Type 'quit' or 'exit' to end
================================================
""".strip()

    async def chat(self):
        if self.agent is None:
            await self.init_async()

        print(self.get_welcome_message())

        # LangChain v1 agents use a state with "messages"
        # We'll keep a running chat history.
        messages: List[dict] = []

        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in {"quit", "exit", "bye"}:
                    print("\nGoodbye! 👋")
                    break

                messages.append({"role": "user", "content": user_input})

                # Invoke agent
                result = self.agent.invoke({"messages": messages})

                # result is typically a dict with updated state
                # In v1 docs, the agent is graph-based and returns state including messages. 1
                updated_messages = result.get("messages", [])
                messages = updated_messages if updated_messages else messages

                # Print last assistant message (if present)
                assistant_text = self._extract_last_assistant_text(messages) or ""
                if self._is_skill_content(assistant_text):
                    assistant_text = "(Skill content omitted)"

                print("\nAssistant:", assistant_text, "\n")

            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye! 👋")
                break
            except Exception as e:
                logger.exception("Error in chat loop")
                print(f"\n❌ Error: {e}\n")

    def _extract_last_assistant_text(self, messages: List[dict]) -> Optional[str]:
        for m in reversed(messages):
            if m.get("role") == "assistant":
                c = m.get("content")
                if isinstance(c, str):
                    return c
                # Some providers use content blocks; try best-effort flatten
                if isinstance(c, list):
                    texts = []
                    for blk in c:
                        if isinstance(blk, dict) and "text" in blk:
                            texts.append(blk["text"])
                    return "\n".join(texts).strip() if texts else None
        return None

    def _build_system_prompt(self) -> str:
        base = (
            "You are an AI assistant with access to multiple services through MCP tools.\n\n"
            "CRITICAL WORKFLOW REQUIREMENT:\n"
            "When the user asks about a service (Confluence/ServiceNow/etc), FIRST follow the relevant SKILL instructions below.\n"
            "Then call MCP tools as required and provide the final answer.\n\n"
        )
        if self.skills_text:
            base += "=== SKILLS (Project) ===\n" + self.skills_text + "\n\n"
        return base

    def _load_skills_text(self) -> str:
        root = Path(os.getcwd())
        skills_dir = root / ".claude" / "skills"
        if not skills_dir.exists():
            return ""

        parts: List[str] = []
        for skill_md in skills_dir.glob("**/SKILL.md"):
            try:
                text = skill_md.read_text(encoding="utf-8", errors="ignore")
                skill_name = skill_md.parent.name
                parts.append(f"\n---\n# Skill: {skill_name}\n{text}\n")
            except Exception as e:
                logger.warning("Failed reading %s: %s", skill_md, e)

        return "\n".join(parts).strip()

    def _is_skill_content(self, text: str) -> bool:
        if not text:
            return False
        t = text.strip()
        if t.startswith("---"):
            return True
        if "# Confluence Integration" in t or "# Available Tools" in t:
            return True
        if len(t) > 500 and ("## Quick Start" in t or "###" in t):
            return True
        return False


async def main():
    agent = SkillsAgentLangChain(verbose=True)
    await agent.chat()


if __name__ == "__main__":
    asyncio.run(main())

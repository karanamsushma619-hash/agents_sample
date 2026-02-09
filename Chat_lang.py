import os
import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.client import MultiServerMCPClient

from src.agent.config import AgentConfig
from src.agent.mcp_manager import MCPManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


class SkillsAgentLangChain:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.config = AgentConfig.from_env()

        # MCP STDIO config like:
        # {"confluence": {"transport":"stdio","command":"python","args":["-m","mcp_servers.tools.confluence_tools"]}}
        self.mcp_client_config = MCPManager.get_langchain_mcp_client_config(self.config)

        # Load skills (optional)
        self.skills_text = self._load_skills_text()
        self.system_prompt = self._build_system_prompt()

        # 1) Connect MCP client (stdio)
        self.mcp_client = MultiServerMCPClient(self.mcp_client_config)

        # IMPORTANT: tools load is async in adapter → run it once here
        self.tools = asyncio.run(self.mcp_client.get_tools())
        logger.info("Loaded %d MCP tools", len(self.tools))

        # 2) Model
        self.model = ChatAnthropic(
            model=os.getenv("LC_MODEL", "claude-3-5-sonnet-latest"),
            temperature=float(os.getenv("LC_TEMPERATURE", "0.2")),
        )

        # 3) Agent (LangChain v1)
        # create_agent returns an “agent graph / runnable” that you call with .invoke(...) 0
        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )

        if self.agent is None:
            raise RuntimeError("create_agent returned None. Check your LangChain install / imports.")

        logger.info(MCPManager.format_server_status(self.config))

    def chat(self):
        print(self.get_welcome_message())
        messages: List[Dict[str, Any]] = []

        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in {"quit", "exit", "bye"}:
                    print("\nGoodbye! 👋")
                    break

                # v1 agent state expects messages in state update 1
                messages.append({"role": "user", "content": user_input})

                result = self.agent.invoke({"messages": messages})  # SYNC invoke
                messages = result.get("messages", messages)

                assistant_text = self._extract_last_assistant_text(messages) or ""
                if self._is_skill_content(assistant_text):
                    # optional: don’t print the huge skill md blob
                    assistant_text = "(Skill content omitted)"

                print("\nAssistant:", assistant_text, "\n")

            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye! 👋")
                break
            except Exception as e:
                logger.exception("Error in chat loop")
                print(f"\n❌ Error: {e}\n")

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
            services.append("✅ ServiceNow - Search and manage tickets")

        return (
            "=============================================\n"
            "🤖 Multi-Service AI Assistant (LangChain v1)\n"
            "=============================================\n"
            f"{MCPManager.format_server_status(self.config)}\n\n"
            "Available Services:\n"
            + ("\n".join(services) if services else "⚠️  No services configured")
            + "\n\n💡 How it works:\n"
            "- Skills are loaded from .claude/skills/**/SKILL.md (project-local)\n"
            "- MCP tools are connected over STDIO and called by the agent\n"
            "- Type 'quit' or 'exit' to end the conversation\n"
            "---------------------------------------------\n"
        )

    def _build_system_prompt(self) -> str:
        base = (
            "You are an AI assistant with access to MCP tools.\n"
            "Follow SKILL instructions when present, then use tools.\n"
        )
        if self.skills_text:
            base += "\n=== SKILLS ===\n" + self.skills_text + "\n"
        return base

    def _load_skills_text(self) -> str:
        skills_dir = Path(os.getcwd()) / ".claude" / "skills"
        if not skills_dir.exists():
            return ""
        parts = []
        for p in skills_dir.glob("**/SKILL.md"):
            try:
                parts.append(f"\n---\n# {p.parent.name}\n{p.read_text(encoding='utf-8', errors='ignore')}\n")
            except Exception:
                pass
        return "\n".join(parts).strip()

    def _extract_last_assistant_text(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        for m in reversed(messages):
            if m.get("role") == "assistant":
                c = m.get("content")
                if isinstance(c, str):
                    return c
                if isinstance(c, list):
                    # best-effort flatten
                    texts = []
                    for blk in c:
                        if isinstance(blk, dict) and "text" in blk:
                            texts.append(blk["text"])
                    return "\n".join(texts).strip() if texts else None
        return None

    def _is_skill_content(self, text: str) -> bool:
        if not text:
            return False
        t = text.strip()
        return t.startswith("---") or ("# Confluence Integration" in t) or (len(t) > 700 and "##" in t)


def main():
    agent = SkillsAgentLangChain(verbose=True)
    agent.chat()


if __name__ == "__main__":
    main()

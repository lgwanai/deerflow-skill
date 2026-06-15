#!/usr/bin/env python3
"""DeerFlow CLI — interactive Agent shell.

Usage:
    deerflow                           # interactive chat (--standard)
    deerflow --flash [prompt]          # flash mode (interactive if no prompt)
    deerflow --pro [prompt]            # pro mode with todo planning
    deerflow --ultra [prompt]          # ultra mode with subagents
    deerflow -c "prompt" [--flash|--pro|--ultra]
    deerflow -o result.md -c "prompt"  # write output to file
    deerflow -h | --help

Interactive commands:
    /help, /h       show help
    /clear, /c      clear conversation (new thread)
    /save <file>    save last response to file
    /tools          list available tools
    /mode <name>    switch mode (flash, standard, pro, ultra)
    /exit, /quit    quit
"""

import cmd
import logging
import os
import sys
import uuid
import warnings
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(SKILL_ROOT))
os.environ["DEER_FLOW_CONFIG_PATH"] = str(SKILL_ROOT / "config.yaml")

warnings.filterwarnings("ignore")
logging.getLogger("deerflow").setLevel(logging.CRITICAL)

from lib.config import resolve_and_validate_config
from lib.errors import format_error, STREAMING_ERRORS
from lib.modes import get_mode_config
from lib.stream import stream_and_print
from lib.tools import log_available_tools, log_mcp_status, check_mcp_tool_availability
from lib.subagent import log_subagent_config

BANNER = r"""
╔══════════════════════════════════════════════╗
║               DeerFlow Agent                ║
║         Open-source AI Agent Shell           ║
╚══════════════════════════════════════════════╝

Type /help for commands, /exit to quit.
"""

MODE_LABELS = {
    "flash": "⚡ FLASH",
    "standard": "🧠 STANDARD",
    "pro": "📋 PRO",
    "ultra": "🚀 ULTRA",
}


def _import_client():
    from deerflow.client import DeerFlowClient

    return DeerFlowClient


def _log_tools(client_kwargs: dict) -> None:
    try:
        from deerflow.tools import get_available_tools
        from deerflow.mcp.cache import get_cached_mcp_tools
        from deerflow.config.extensions_config import ExtensionsConfig

        model_name = client_kwargs.get("model_name")
        subagent_enabled = client_kwargs.get("subagent_enabled", False)
        tools = get_available_tools(model_name=model_name, subagent_enabled=subagent_enabled)
        log_available_tools(tools)

        mcp_tools = get_cached_mcp_tools()
        extensions_config = ExtensionsConfig.from_file()
        servers = extensions_config.get_enabled_mcp_servers()
        log_mcp_status(servers, mcp_tools)
        check_mcp_tool_availability(servers, mcp_tools)
    except Exception:
        pass


class DeerFlowCLI(cmd.Cmd):
    """Interactive DeerFlow agent shell.

    Supports multi-turn conversations with context tracking,
    mode switching, file output, and tool introspection.
    """

    intro = BANNER
    prompt = "\n🐱> "

    def __init__(self, mode: str = "standard", output_file: str | None = None):
        super().__init__()
        self.mode = mode
        self.output_file = output_file
        self.last_response = ""
        self.turn_count = 0

        self.config_path = resolve_and_validate_config()
        self.client_kwargs = get_mode_config(mode)
        self.DeerFlowClient = _import_client()

        self.thread_id = str(uuid.uuid4())

        self._create_client()
        self._print_mode()
        if self.client_kwargs.get("subagent_enabled"):
            log_subagent_config()
        _log_tools(self.client_kwargs)

    def _create_client(self) -> None:
        self.client = self.DeerFlowClient(
            config_path=str(self.config_path), **self.client_kwargs
        )

    def _print_mode(self) -> None:
        label = MODE_LABELS.get(self.mode, self.mode.upper())
        print(f"\n[Mode: {label}]", file=sys.stderr)

    def _run(self, prompt: str) -> str:
        try:
            from langgraph.errors import GraphRecursionError
        except ImportError:
            class GraphRecursionError(Exception):
                pass

        try:
            result = stream_and_print(self.client, prompt, self.thread_id)
            self.turn_count += 1
            self.last_response = result
            return result

        except GraphRecursionError:
            print(f"\n{STREAMING_ERRORS['recursion']}", file=sys.stderr)
            return ""

        except KeyboardInterrupt:
            print("\n[Interrupted]", file=sys.stderr)
            return ""

        except Exception as e:
            error_msg = str(e).strip()
            if "timeout" in error_msg.lower() or "subagent" in error_msg.lower():
                from lib.subagent import is_subagent_timeout, format_subagent_timeout_error
                if is_subagent_timeout(e):
                    print(format_subagent_timeout_error(e, 900), file=sys.stderr)
                    return ""
            print(format_error(e), file=sys.stderr)
            return ""

    # ── cmd.Cmd hooks ──────────────────────────────────────────────

    def emptyline(self) -> bool:
        return False

    def default(self, line: str) -> bool:
        if not line.strip():
            return False
        print(file=sys.stderr)
        self._run(line)
        print()
        return False

    def precmd(self, line: str) -> str:
        if line.startswith("/"):
            return line
        return line

    # ── Commands ────────────────────────────────────────────────────

    def do_exit(self, arg: str) -> bool:
        """Exit the DeerFlow shell."""
        print("\nGoodbye!")
        return True

    def do_quit(self, arg: str) -> bool:
        """Exit the DeerFlow shell."""
        return self.do_exit(arg)

    def do_help(self, arg: str) -> None:
        """Show help information."""
        print("""
DeerFlow CLI — Interactive AI Agent Shell
─────────────────────────────────────────

Commands:
  /help, /h          Show this help
  /clear, /c         Start a new conversation (new thread)
  /save <file>       Save last response to file
  /tools             List available tools
  /mode <name>       Switch mode (flash, standard, pro, ultra)
  /exit, /quit       Exit the shell

Type anything else to chat with the agent.
""")

    def do_h(self, arg: str) -> None:
        self.do_help(arg)

    def do_clear(self, arg: str) -> None:
        """Start a new conversation."""
        self.thread_id = str(uuid.uuid4())
        self.turn_count = 0
        self.last_response = ""
        self._create_client()
        print("[New conversation started]", file=sys.stderr)

    def do_c(self, arg: str) -> None:
        self.do_clear(arg)

    def do_save(self, arg: str) -> None:
        """Save last response to a file."""
        if not arg.strip():
            print("Usage: /save <filename>", file=sys.stderr)
            return
        path = Path(arg.strip())
        try:
            path.write_text(self.last_response, encoding="utf-8")
            print(f"[Saved {len(self.last_response)} chars to {path}]", file=sys.stderr)
        except OSError as e:
            print(f"[Error saving file: {e}]", file=sys.stderr)

    def do_tools(self, arg: str) -> None:
        """List available tools."""
        try:
            from deerflow.tools import get_available_tools
            model_name = self.client_kwargs.get("model_name")
            subagent_enabled = self.client_kwargs.get("subagent_enabled", False)
            tools = get_available_tools(model_name=model_name, subagent_enabled=subagent_enabled)
            print(file=sys.stderr)
            log_available_tools(tools)
        except Exception as e:
            print(f"[Error: {e}]", file=sys.stderr)

    def do_mode(self, arg: str) -> None:
        """Switch agent mode."""
        valid = {"flash", "standard", "pro", "ultra"}
        new_mode = arg.strip().lower()
        if new_mode not in valid:
            print(f"Invalid mode. Choose: {', '.join(valid)}", file=sys.stderr)
            return
        self.mode = new_mode
        self.client_kwargs = get_mode_config(new_mode)
        self._create_client()
        self._print_mode()
        if self.client_kwargs.get("subagent_enabled"):
            log_subagent_config()
        _log_tools(self.client_kwargs)
        print("[Mode changed, new conversation]", file=sys.stderr)


# ── Argument parsing ───────────────────────────────────────────────

def parse_args() -> tuple[str, str | None, str | None]:
    """Parse CLI arguments.

    Returns:
        (mode, prompt_or_None, output_file_or_None)
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="deerflow",
        description="DeerFlow Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  deerflow                           interactive chat (standard mode)
  deerflow --flash                   interactive chat (flash mode)
  deerflow -c "What is Python?"      one-shot execution
  deerflow --pro -c "Plan a project" one-shot with pro mode
  deerflow -o result.md -c "..."     write output to file""",
    )
    parser.add_argument(
        "-c", "--command",
        help="Run a single command (non-interactive)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Write output to file",
    )
    parser.add_argument(
        "--flash", action="store_true", default=False,
        help="Flash mode (no thinking, no planning)",
    )
    parser.add_argument(
        "--pro", action="store_true", default=False,
        help="Pro mode (thinking + planning)",
    )
    parser.add_argument(
        "--ultra", action="store_true", default=False,
        help="Ultra mode (thinking + planning + subagents)",
    )

    args = parser.parse_args()

    mode = "standard"
    if args.flash:
        mode = "flash"
    elif args.pro:
        mode = "pro"
    elif args.ultra:
        mode = "ultra"

    return mode, args.command, args.output


def main() -> None:
    mode, command, output_file = parse_args()

    if command:
        # ── one-shot mode ───────────────────────────────────
        cli = DeerFlowCLI(mode=mode, output_file=output_file)
        result = cli._run(command)
        if output_file:
            Path(output_file).write_text(result, encoding="utf-8")
            print(f"\n[Output saved to {output_file}]", file=sys.stderr)
    else:
        # ── interactive mode ────────────────────────────────
        try:
            cli = DeerFlowCLI(mode=mode, output_file=output_file)
            cli.cmdloop()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()

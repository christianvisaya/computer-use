"""CLI entrypoint for computer-use."""

import argparse
import sys

from termcolor import colored

from computer_use import agent, workspace


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="computer-use",
        description="AI-powered GUI automation. Give it an instruction, watch it work.",
    )
    parser.add_argument(
        "--instruction",
        required=True,
        help="Natural-language instruction to execute",
    )
    parser.add_argument(
        "--workspace",
        default=None,
        help="Path to workspace directory (default: ./computer-use-workspace)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=50,
        help="Maximum screenshot→action loops (default: 50)",
    )
    parser.add_argument(
        "--wait-after-action",
        type=float,
        default=1.0,
        help="Seconds to wait after each action before next screenshot (default: 1.0)",
    )
    args = parser.parse_args()

    # Load workspace config
    try:
        config = workspace.load_workspace(args.workspace)
    except Exception as e:
        print(colored(f"Failed to load workspace: {e}", "red"))
        sys.exit(1)

    # Validate required config
    try:
        workspace.validate_config(config)
    except ValueError as e:
        print(colored(f"Configuration error: {e}", "red"))
        sys.exit(1)

    print(colored(f"[computer-use] provider={config['ai_provider']} model={_get_model(config)}", "blue"))
    print(colored(f"[computer-use] instruction: {args.instruction}", "blue"))
    print()

    # Run the agent loop
    try:
        agent.run(
            instruction=args.instruction,
            config=config,
            max_steps=args.max_steps,
            wait_after_action=args.wait_after_action,
        )
    except KeyboardInterrupt:
        print(colored("\nInterrupted by user.", "yellow"))
        sys.exit(130)


def _get_model(config: dict) -> str:
    provider = config["ai_provider"]
    if provider == "minimax":
        return config.get("minimax_model", "")
    elif provider == "ollama":
        return config.get("ollama_model", "")
    elif provider == "openai":
        return config.get("openai_model", "")
    return ""


if __name__ == "__main__":
    main()

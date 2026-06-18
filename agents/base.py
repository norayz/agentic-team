"""
Agent harness — the loop every agent runs.
No framework. Direct Anthropic SDK.
"""
import os
import json
import logging
import time
from typing import Any
import anthropic

logger = logging.getLogger(__name__)
client = anthropic.AnthropicBedrock(
    aws_region=os.environ.get("AWS_REGION", "eu-central-1"),
)


def run_agent(
    issue_number: int,
    agent_name: str,
    model: str,
    tools: list[dict],
    system_prompt: str,
    tool_executor: callable,
    max_iterations: int = 30,
) -> str:
    """
    Core agent loop. Runs until end_turn or max_iterations.

    tool_executor: callable(tool_name, tool_input) -> str
    Returns the final text response.
    """
    # Build initial context from the issue
    from tools.github_issues import get_issue, get_comments
    issue = get_issue(issue_number)
    comments = get_comments(issue_number)

    history = [
        {
            "role": "user",
            "content": (
                f"Issue #{issue_number}: {issue['title']}\n\n"
                f"Body:\n{issue['body']}\n\n"
                f"Current labels: {', '.join(issue['labels'])}\n\n"
                f"Comments ({len(comments)}):\n" +
                "\n".join(f"  [{c['author']}] {c['body']}" for c in comments[-10:])
            )
        }
    ]

    logger.info(f"[{agent_name}] Starting on issue #{issue_number} with model {model}")

    consecutive_errors: dict[str, int] = {}

    for iteration in range(max_iterations):
        # Trim context window: keep first message + last 16 if history too long
        if len(history) > 20:
            history = [history[0]] + history[-16:]

        # Retry with exponential backoff on transient API errors
        for attempt in range(3):
            try:
                response = client.messages.create(
                    model=model,
                    max_tokens=16384,
                    system=system_prompt,
                    tools=tools,
                    messages=history,
                )
                break
            except (anthropic.RateLimitError, anthropic.InternalServerError) as e:
                if attempt < 2:
                    delay = 2 ** (attempt + 1)  # 2, 4 seconds
                    logger.warning(f"[{agent_name}] API error (attempt {attempt + 1}/3), retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"[{agent_name}] API error after 3 attempts, giving up: {e}")
                    raise

        # Append assistant response
        history.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Extract final text
            for block in response.content:
                if hasattr(block, "text"):
                    logger.info(f"[{agent_name}] Completed issue #{issue_number}")
                    return block.text
            return ""

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"[{agent_name}] Calling tool: {block.name}")
                    try:
                        result = tool_executor(block.name, block.input)
                        consecutive_errors.pop(block.name, None)
                    except Exception as e:
                        result = f"Error: {e}"
                        logger.error(f"[{agent_name}] Tool {block.name} failed: {e}")
                        consecutive_errors[block.name] = consecutive_errors.get(block.name, 0) + 1
                        if consecutive_errors[block.name] >= 3:
                            result += " — This tool has failed 3 times in a row. Do NOT retry it. Work around the issue or skip this step and proceed."
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    })
            history.append({"role": "user", "content": tool_results})
        else:
            logger.warning(f"[{agent_name}] Unexpected stop_reason: {response.stop_reason}")
            break

    logger.warning(f"[{agent_name}] Reached max iterations ({max_iterations})")
    return ""

"""
LLM powered file system assistant.

The model never touches the disk itself. It only asks for a tool by name
with some arguments, and this script validates the arguments, runs the
matching function from fs_tools.py and sends the result back.

Usage:
    python llm_file_assistant.py                       # interactive chat
    python llm_file_assistant.py "Find resumes mentioning Python"
"""

import getpass
import json
import os
import sys
import time
from typing import Any

from openai import APIStatusError, OpenAI
from pydantic import BaseModel, Field, ValidationError

import fs_tools

MODEL_NAME = os.environ.get("OPENROUTER_MODEL", "openrouter/free")
RATE_LIMIT_RETRIES = 4
MAX_TOOL_ROUNDS = 20  # some models call one tool per turn, so searching 10 resumes takes 10+ rounds
MAX_TOOL_RESULT_CHARS = 8000  # keeps one huge resume from eating the context window

SYSTEM_PROMPT = (
    "You are a file system assistant that helps the user work with resume files. "
    "Resumes are stored in the 'resumes' folder. Save any file you create, such as "
    "summaries, inside the 'output' folder. "
    "Always use the tools to look at real files, never guess what a file contains. "
    "If you do not know which files exist, call list_files first. "
    "When a tool returns an error, tell the user what went wrong in plain language."
)


# ---------- tool argument schemas ----------

class ReadFileInput(BaseModel):
    filepath: str = Field(description="Path to a .txt, .pdf or .docx file, e.g. resumes/resume_john_doe.pdf")


class ListFilesInput(BaseModel):
    directory: str = Field(description="Folder to list, e.g. resumes")
    extension: str | None = Field(
        default=None,
        description="Optional file extension filter such as .pdf or .txt",
    )


class WriteFileInput(BaseModel):
    filepath: str = Field(description="Where to save the file, e.g. output/john_doe_summary.txt")
    content: str = Field(description="Full text to write into the file")


class SearchInFileInput(BaseModel):
    filepath: str = Field(description="Path of the file to search")
    keyword: str = Field(description="Word or phrase to look for. Case is ignored")


# name -> (python function, input schema, description shown to the model)
TOOL_REGISTRY = {
    "read_file": (
        fs_tools.read_file,
        ReadFileInput,
        "Read a resume file (.txt, .pdf, .docx) and return its text content and metadata.",
    ),
    "list_files": (
        fs_tools.list_files,
        ListFilesInput,
        "List files in a folder with name, size and modified date. Can filter by extension.",
    ),
    "write_file": (
        fs_tools.write_file,
        WriteFileInput,
        "Write text content to a file. Missing folders are created automatically.",
    ),
    "search_in_file": (
        fs_tools.search_in_file,
        SearchInFileInput,
        "Search a file for a keyword (case-insensitive) and return matches with surrounding text.",
    ),
}


def build_tool_definitions() -> list[dict]:
    definitions = []
    for name, (_, schema, description) in TOOL_REGISTRY.items():
        definitions.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": schema.model_json_schema(),
                },
            }
        )
    return definitions


def execute_tool(tool_name: str, raw_arguments: str) -> Any:
    """Validate the model's arguments and run the tool.

    Any problem is returned as an error dict instead of raised, so the model
    gets a chance to read the error and try again.
    """
    if tool_name not in TOOL_REGISTRY:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    function, schema, _ = TOOL_REGISTRY[tool_name]

    try:
        arguments = schema.model_validate_json(raw_arguments or "{}")
    except ValidationError as exc:
        return {"success": False, "error": f"Invalid arguments: {exc.errors()[0]['msg']}"}

    try:
        return function(**arguments.model_dump())
    except (OSError, ValueError) as exc:
        return {"success": False, "error": str(exc)}


def result_to_message_content(result: Any) -> str:
    text = json.dumps(result, default=str)
    if len(text) > MAX_TOOL_RESULT_CHARS:
        text = text[:MAX_TOOL_RESULT_CHARS] + '... [truncated]'
    return text


# ---------- the agent loop ----------

def get_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        api_key = getpass.getpass("Enter your OpenRouter API key: ")

    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)


def explain_api_error(status_code: int) -> str:
    hints = {
        401: "Check that your OpenRouter API key is correct.",
        402: "This model needs credits. Pick a free model with OPENROUTER_MODEL.",
        429: "The model is rate limited right now. Wait a bit or try another model.",
    }
    return hints.get(status_code, "Try again or switch to a different model.")


def create_completion(client: OpenAI, messages: list, tools: list):
    """One model call. Free models hit rate limits often, so wait and retry on 429."""
    for attempt in range(RATE_LIMIT_RETRIES):
        try:
            return client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0,
            )
        except APIStatusError as exc:
            out_of_retries = attempt == RATE_LIMIT_RETRIES - 1
            if exc.status_code != 429 or out_of_retries:
                raise
            wait_seconds = 10 * (attempt + 1)
            print(f"  rate limited, retrying in {wait_seconds}s")
            time.sleep(wait_seconds)


def run_assistant(client: OpenAI, messages: list, verbose: bool = True) -> str:
    """Keep calling the model until it stops asking for tools, then return its answer.

    messages is modified in place so a chat session keeps its history.
    """
    tools = build_tool_definitions()

    for round_number in range(1, MAX_TOOL_ROUNDS + 1):
        try:
            response = create_completion(client, messages, tools)
        except APIStatusError as exc:
            # 402 means no credits, 429 means a free model is still busy after retrying
            return f"The model request failed ({exc.status_code}). {explain_api_error(exc.status_code)}"
        assistant_message = response.choices[0].message
        messages.append(assistant_message)

        if not assistant_message.tool_calls:
            return assistant_message.content or ""

        # the model can ask for several tools in one turn, so answer every one of them
        for tool_call in assistant_message.tool_calls:
            name = tool_call.function.name
            raw_arguments = tool_call.function.arguments

            if verbose:
                print(f"  [round {round_number}] calling {name}({raw_arguments})")

            result = execute_tool(name, raw_arguments)

            if verbose and isinstance(result, dict) and result.get("success") is False:
                print(f"    tool error: {result.get('error')}")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_to_message_content(result),
                }
            )

    return "I stopped because I hit the tool call limit. Try a more specific request."


def new_conversation() -> list:
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def chat_loop(client: OpenAI) -> None:
    print("File assistant ready. Type 'exit' to quit.\n")
    messages = new_conversation()

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue

        messages.append({"role": "user", "content": question})
        answer = run_assistant(client, messages)
        print(f"\nAssistant: {answer}\n")


def main() -> None:
    client = get_client()

    if len(sys.argv) > 1:
        messages = new_conversation()
        messages.append({"role": "user", "content": " ".join(sys.argv[1:])})
        print(run_assistant(client, messages))
    else:
        chat_loop(client)


if __name__ == "__main__":
    main()

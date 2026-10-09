# LLM-Powered File System Assistant

A small command line assistant that lets an LLM work with resume files. You ask in plain English, the model decides which file tool to call, Python runs it, and the result goes back to the model so it can answer.

It uses OpenRouter through the OpenAI compatible SDK, Pydantic to validate tool arguments, and a hand written tool calling loop (no agent framework).

## How it works

```
User question -> LLM picks a tool -> Python runs it -> result goes back to LLM -> final answer
```

The model never reads the disk itself. It only sees the tool names, descriptions and argument schemas. `llm_file_assistant.py` checks the arguments with Pydantic and then calls the real function in `fs_tools.py`.

## Project layout

```
fs_tools.py              the four file tools (no LLM needed to use them)
llm_file_assistant.py    connects the tools to an LLM and runs the chat loop
make_sample_data.py      creates the 8 dummy resumes
test_fs_tools.py         checks for the tools
resumes/                 sample resumes (3 PDF, 3 DOCX, 2 TXT)
output/                  summaries written by the assistant end up here
requirements.txt
```

## Tools

| Tool | What it does |
|---|---|
| `read_file(filepath)` | Reads a .txt, .pdf or .docx file. Returns the text and metadata (type, size, modified date, word count, page count for PDFs). Returns `success: False` with an error message instead of crashing. |
| `list_files(directory, extension=None)` | Lists files with name, size and modified date. The extension filter accepts `.pdf` or `pdf`. |
| `write_file(filepath, content)` | Writes text to a file and creates missing folders. Returns a success or failure dict. |
| `search_in_file(filepath, keyword)` | Case-insensitive search. Every match comes with about 60 characters of text on each side. |

## Setup

You need Python 3.10 or newer and a free OpenRouter API key from https://openrouter.ai/keys

```bash
python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
python make_sample_data.py       # only needed if the resumes folder is empty
```

Set your key as an environment variable. If you skip this, the script asks for it when it starts.

```bash
export OPENROUTER_API_KEY="your-key-here"
```

The default model is `openrouter/free`, which lets OpenRouter pick any free model that fits the request. Free models are sometimes rate limited, so if you get a 429 error, wait a minute or set `OPENROUTER_MODEL` to another model. It must support tool calling. `openai/gpt-4o-mini` also works if your account has credits.

```bash
export OPENROUTER_MODEL="your-model-id"
```

## Usage

Chat mode:

```bash
python llm_file_assistant.py
```

Single question:

```bash
python llm_file_assistant.py "Find resumes mentioning Python experience"
```

Example queries:

- Read all resumes in the resumes folder
- Find resumes mentioning Python experience
- Create a summary file for resume_john_doe.pdf
- Which PDF resumes mention Docker?
- List the docx files and tell me which one was modified most recently

Each tool call is printed as it happens, so you can follow what the model is doing.

## Testing the tools

The tool tests do not need an API key.

```bash
python test_fs_tools.py
```

## Design notes

- Tool errors come back to the model as a dict with `success: False`, so it can explain the problem or try something else.
- The loop stops after 20 rounds so a confused model cannot call tools forever.
- Tool output is cut at 8000 characters before it is sent to the model.
- The model can request several tools in one turn, and every request gets a reply.
- `list_files` raises on a bad directory and the assistant turns that into an error dict. The other three tools return the error dict themselves.

## Limitations

- Scanned PDFs that are only images have no text layer, so `read_file` returns almost nothing for them. OCR is not included.
- Tools accept any path on your machine. For a real deployment you would limit them to specific folders.
- Old `.doc` files are not supported.

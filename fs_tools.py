"""
File system tools for the resume assistant.

Each function here is plain Python and can be tested without any LLM.
llm_file_assistant.py wraps them as tools the model is allowed to call.
"""

import os
from datetime import datetime

from docx import Document
from pypdf import PdfReader

SUPPORTED_TYPES = (".txt", ".pdf", ".docx")
CONTEXT_CHARS = 60  # how much text to show on each side of a search match


def _iso_time(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def _read_txt(filepath: str) -> tuple[str, dict]:
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.read(), {}


def _read_pdf(filepath: str) -> tuple[str, dict]:
    reader = PdfReader(filepath)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages), {"page_count": len(reader.pages)}


def _read_docx(filepath: str) -> tuple[str, dict]:
    document = Document(filepath)
    paragraphs = [p.text for p in document.paragraphs]
    return "\n".join(paragraphs), {"paragraph_count": len(paragraphs)}


# maps an extension to the function that knows how to read it
READERS = {
    ".txt": _read_txt,
    ".pdf": _read_pdf,
    ".docx": _read_docx,
}


def read_file(filepath: str) -> dict:
    """Read a resume (.txt, .pdf or .docx) and return its text plus metadata.

    Never raises. On failure the dict has success=False and an error message.
    """
    if not os.path.isfile(filepath):
        return {"success": False, "filepath": filepath, "error": "File not found"}

    extension = os.path.splitext(filepath)[1].lower()
    reader = READERS.get(extension)
    if reader is None:
        return {
            "success": False,
            "filepath": filepath,
            "error": f"Unsupported file type '{extension}'. Supported: {', '.join(SUPPORTED_TYPES)}",
        }

    try:
        content, extra_metadata = reader(filepath)
    except Exception as exc:
        # corrupt pdfs and docx files raise all sorts of exceptions, so catch broadly
        return {"success": False, "filepath": filepath, "error": f"Could not read file: {exc}"}

    stats = os.stat(filepath)
    metadata = {
        "file_name": os.path.basename(filepath),
        "file_type": extension,
        "size_bytes": stats.st_size,
        "modified": _iso_time(stats.st_mtime),
        "char_count": len(content),
        "word_count": len(content.split()),
    }
    metadata.update(extra_metadata)

    return {"success": True, "filepath": filepath, "content": content, "metadata": metadata}


def list_files(directory: str, extension: str = None) -> list:
    """List the files in a directory with name, size and modified date.

    extension is optional and can be written as '.pdf' or 'pdf'.
    Raises FileNotFoundError or NotADirectoryError for a bad directory,
    the caller decides how to report that.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"Not a directory: {directory}")

    if extension:
        extension = extension.lower()
        if not extension.startswith("."):
            extension = "." + extension

    results = []
    for name in sorted(os.listdir(directory)):
        full_path = os.path.join(directory, name)
        if not os.path.isfile(full_path):
            continue
        if extension and not name.lower().endswith(extension):
            continue

        stats = os.stat(full_path)
        results.append(
            {
                "name": name,
                "path": full_path,
                "size_bytes": stats.st_size,
                "modified": _iso_time(stats.st_mtime),
            }
        )
    return results


def write_file(filepath: str, content: str) -> dict:
    """Write text to a file, creating any missing parent folders."""
    try:
        parent = os.path.dirname(filepath)
        if parent:
            os.makedirs(parent, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "success": True,
            "filepath": filepath,
            "bytes_written": len(content.encode("utf-8")),
        }
    except OSError as exc:
        return {"success": False, "filepath": filepath, "error": str(exc)}


def search_in_file(filepath: str, keyword: str) -> dict:
    """Case-insensitive keyword search. Each match comes with surrounding text."""
    if not keyword or not keyword.strip():
        return {"success": False, "filepath": filepath, "error": "Keyword cannot be empty"}

    file_result = read_file(filepath)
    if not file_result["success"]:
        return file_result

    text = file_result["content"]
    lowered_text = text.lower()
    lowered_keyword = keyword.lower()

    matches = []
    start = 0
    while True:
        index = lowered_text.find(lowered_keyword, start)
        if index == -1:
            break

        context_start = max(0, index - CONTEXT_CHARS)
        context_end = min(len(text), index + len(keyword) + CONTEXT_CHARS)
        snippet = text[context_start:context_end].replace("\n", " ")
        matches.append({"position": index, "context": snippet})

        start = index + len(lowered_keyword)

    return {
        "success": True,
        "filepath": filepath,
        "keyword": keyword,
        "match_count": len(matches),
        "matches": matches,
    }

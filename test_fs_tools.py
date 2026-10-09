"""
Quick checks for fs_tools.py. Run with:  python test_fs_tools.py
No API key needed.
"""

import os
import shutil

import fs_tools

TEST_OUTPUT_DIR = "test_output_tmp"


def test_list_files():
    all_files = fs_tools.list_files("resumes")
    pdfs = fs_tools.list_files("resumes", ".pdf")
    pdfs_no_dot = fs_tools.list_files("resumes", "PDF")

    assert len(all_files) == 8
    assert len(pdfs) == 3
    assert len(pdfs_no_dot) == 3
    assert set(all_files[0]) == {"name", "path", "size_bytes", "modified"}


def test_list_files_bad_directory():
    try:
        fs_tools.list_files("no_such_folder")
    except FileNotFoundError:
        return
    raise AssertionError("expected FileNotFoundError")


def test_read_each_format():
    for name in ("resume_amit_verma.txt", "resume_john_doe.pdf", "resume_priya_sharma.docx"):
        result = fs_tools.read_file(os.path.join("resumes", name))
        assert result["success"], result
        assert len(result["content"]) > 100
        assert result["metadata"]["file_name"] == name


def test_read_errors():
    missing = fs_tools.read_file("resumes/ghost.pdf")
    wrong_type = fs_tools.read_file("make_sample_data.py")

    assert missing["success"] is False
    assert wrong_type["success"] is False
    assert "Unsupported" in wrong_type["error"]


def test_search_is_case_insensitive():
    lower = fs_tools.search_in_file("resumes/resume_john_doe.pdf", "python")
    upper = fs_tools.search_in_file("resumes/resume_john_doe.pdf", "PYTHON")

    assert lower["match_count"] >= 2
    assert lower["match_count"] == upper["match_count"]
    assert "ython" in lower["matches"][0]["context"]


def test_search_no_match_and_empty_keyword():
    nothing = fs_tools.search_in_file("resumes/resume_anita_roy.docx", "kubernetes")
    empty = fs_tools.search_in_file("resumes/resume_anita_roy.docx", "  ")

    assert nothing["success"] and nothing["match_count"] == 0
    assert empty["success"] is False


def test_write_creates_directories():
    path = os.path.join(TEST_OUTPUT_DIR, "nested", "note.txt")
    result = fs_tools.write_file(path, "hello")

    assert result["success"]
    assert fs_tools.read_file(path)["content"] == "hello"


if __name__ == "__main__":
    try:
        tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
        for test in tests:
            test()
            print("passed:", test.__name__)
    finally:
        shutil.rmtree(TEST_OUTPUT_DIR, ignore_errors=True)

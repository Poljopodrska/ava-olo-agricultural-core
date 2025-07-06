import os
import datetime

README_NAME = "README.md"
EXCLUDE = {".git", "venv", "__pycache__", ".DS_Store", README_NAME}
ROOT = os.path.dirname(os.path.abspath(__file__))


def get_file_info(filepath):
    """Return file size (KB), last modified timestamp, and docstring if .py"""
    size_kb = os.path.getsize(filepath) / 1024
    last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M')

    docstring = ""
    if filepath.endswith(".py"):
        try:
            with open(filepath, encoding="utf-8") as f:
                lines = f.readlines()
                if lines and (lines[0].strip().startswith('"""') or lines[0].strip().startswith("'''")):
                    docstring = lines[0].strip().strip('"""').strip("'''").strip()
        except Exception:
            pass

    return f"({size_kb:.1f} KB, {last_modified})", docstring


def write_readme():
    with open(os.path.join(ROOT, README_NAME), "w", encoding="utf-8") as f:
        f.write("# 🧠 AVA Pinecone RAG Project\n\n")
        f.write("This is an AI-driven retrieval system using Pinecone and LangChain, connected to a PostgreSQL backend.\n\n")
        f.write("## 📁 Project Structure\n\n")
        for dirpath, dirnames, filenames in os.walk(ROOT):
            # Skip excluded dirs
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE]
            depth = dirpath.replace(ROOT, "").count(os.sep)
            indent = "  " * depth
            if depth > 0:
                f.write(f"{indent}- 📂 {os.path.basename(dirpath)}\n")

            for file in filenames:
                if file in EXCLUDE:
                    continue
                filepath = os.path.join(dirpath, file)
                relpath = os.path.relpath(filepath, ROOT)
                size_time, docstring = get_file_info(filepath)
                file_indent = "  " * (depth + 1)
                f.write(f"{file_indent}- 📄 `{file}` {size_time}\n")
                if docstring:
                    f.write(f"{file_indent}  - 🧾 _{docstring}_\n")
        f.write("\n---\n\n🛠️ _This README was auto-generated. Run `python generate_readme.py` to update._\n")


if __name__ == "__main__":
    write_readme()
    print("✅ README.md updated with file structure, sizes, timestamps, and docstrings.")

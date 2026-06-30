from pathlib import Path

from rag_pipeline.env import load_dotenv


def test_load_dotenv_reads_values(tmp_path: Path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("GROQ_API_KEY=test-value\n", encoding="utf-8")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    load_dotenv(env_file)

    assert __import__("os").environ["GROQ_API_KEY"] == "test-value"


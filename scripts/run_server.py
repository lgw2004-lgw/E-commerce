"""Start the editable upstream DB-GPT app without changing global Python settings."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT / "DB-GPT")
os.environ.setdefault("DBGPT_HOME", str(ROOT / "data" / "dbgpt-home"))
os.environ.setdefault("DBGPT_LOG_DIR", str(ROOT / "logs"))
os.environ.setdefault("DBGPTS_HOME", str(ROOT / "data" / "dbgpts"))
os.environ.setdefault("DBGPTS_REPO_HOME", str(ROOT / "data" / "dbgpts" / "repos"))
os.environ.setdefault("DBGPT_LANG", "zh")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ["ECOMMERCE_META_DB"] = (ROOT / "data" / "metadata" / "dbgpt.db").as_posix()
os.environ["ECOMMERCE_VECTOR_DIR"] = (ROOT / "data" / "vectors").as_posix()
secret = ROOT / "data" / "local-encryption-key.txt"
if not secret.is_file():
    raise SystemExit("Run scripts/init_data.py before starting the server.")
os.environ["ECOMMERCE_ENCRYPT_KEY"] = secret.read_text(encoding="utf-8").strip()
os.environ["ENCRYPT_KEY"] = os.environ["ECOMMERCE_ENCRYPT_KEY"]

env_file = ROOT / ".env"
if env_file.is_file():
    from dotenv import load_dotenv
    load_dotenv(env_file, override=False)

config = ROOT / "configs" / ("online-model.toml" if "--online" in sys.argv else "local.toml")
if not config.is_file():
    raise SystemExit(f"Missing configuration: {config}")

if __name__ == "__main__":
    # Register project adapters before DB-GPT parses provider-specific config.
    import bailian_models  # noqa: F401
    import grok_models  # noqa: F401

    from dbgpt_app.dbgpt_server import run_webserver
    run_webserver(str(config))

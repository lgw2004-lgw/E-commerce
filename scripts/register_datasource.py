"""Register the synthetic SQLite datasource without requiring an embedding model."""
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
metadata = ROOT / "data/metadata/dbgpt.db"
source = ROOT / "data/ecommerce.db"
if not metadata.is_file() or not source.is_file():
    raise SystemExit("Start DB-GPT and initialize the sample database first.")
with sqlite3.connect(metadata, timeout=30) as con:
    if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='connect_config'").fetchone():
        raise SystemExit("DB-GPT metadata initialization has not finished yet.")
    existing = con.execute("SELECT db_path FROM connect_config WHERE db_name=?", ("ecommerce_demo",)).fetchone()
    if existing:
        if Path(existing[0]).resolve() != source.resolve():
            raise SystemExit("An ecommerce_demo datasource already points elsewhere; preserved.")
        print("Datasource ecommerce_demo is already registered.")
    else:
        con.execute("""INSERT INTO connect_config
          (db_type,db_name,db_path,db_host,db_port,db_user,db_pwd,comment,user_id,gmt_created,gmt_modified)
          VALUES (?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))""",
          ("sqlite", "ecommerce_demo", source.as_posix(), "", "0", "", "",
           "电商模拟数据：客户、商品、订单、明细、退款。金额以分存储。paid/completed计入销售额。", ""))
        print("Registered datasource ecommerce_demo. Schema embeddings are deferred until a model is configured.")

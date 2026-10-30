"""Translate the shipped sample datasource comments without touching user text."""
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'data/metadata/dbgpt.db'
replacements = [
    ('Walmart_Sales', 'Default Walmart Sales example database', '默认沃尔玛销售示例数据库'),
    ('ecommerce_demo', '电商模拟数据：客户、商品、订单、明细、退款。金额以分存储。paid/completed计入销售额。',
     '电商模拟数据：客户、商品、订单、明细和退款。金额以分存储，已支付（paid）和已完成（completed）的订单计入销售额。'),
]
with sqlite3.connect(path) as connection:
    pending = [(new, name, old) for name, old, new in replacements
               if connection.execute('SELECT 1 FROM connect_config WHERE db_name=? AND comment=?', (name, old)).fetchone()]
    if pending:
        backup = ROOT / 'work/chinese-ui-backup/dbgpt-before-chinese.db'
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            with sqlite3.connect(backup) as target:
                connection.backup(target)
        connection.executemany('UPDATE connect_config SET comment=? WHERE db_name=? AND comment=?', pending)
    print(f'已更新 {len(pending)} 条内置示例数据库说明。')

"""Generate reproducible synthetic commerce data. Existing databases are preserved."""
from __future__ import annotations

import json
from pathlib import Path
import random
import secrets
import shutil
import sqlite3
from datetime import date, timedelta

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "ecommerce.db"

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE customers (
 customer_id INTEGER PRIMARY KEY, customer_name TEXT NOT NULL,
 province TEXT NOT NULL, registered_at TEXT NOT NULL);
CREATE TABLE products (
 product_id INTEGER PRIMARY KEY, product_name TEXT NOT NULL,
 category TEXT NOT NULL, price_cents INTEGER NOT NULL CHECK(price_cents>0));
CREATE TABLE orders (
 order_id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers,
 ordered_at TEXT NOT NULL, status TEXT NOT NULL
 CHECK(status IN ('paid','completed','cancelled','pending')),
 channel TEXT NOT NULL, order_amount_cents INTEGER NOT NULL CHECK(order_amount_cents>=0));
CREATE TABLE order_items (
 item_id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders,
 product_id INTEGER NOT NULL REFERENCES products, quantity INTEGER NOT NULL CHECK(quantity>0),
 unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents>0),
 line_amount_cents INTEGER NOT NULL CHECK(line_amount_cents=quantity*unit_price_cents));
CREATE TABLE refunds (
 refund_id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders,
 refund_amount_cents INTEGER NOT NULL CHECK(refund_amount_cents>0),
 refunded_at TEXT NOT NULL, reason TEXT NOT NULL);
CREATE INDEX idx_orders_date ON orders(ordered_at);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_items_order ON order_items(order_id);
CREATE INDEX idx_refunds_order ON refunds(order_id);
CREATE VIEW v_daily_sales AS
 SELECT ordered_at AS sales_date, COUNT(*) AS paid_order_count,
 ROUND(SUM(order_amount_cents)/100.0,2) AS gross_sales_yuan
 FROM orders WHERE status IN ('paid','completed') GROUP BY ordered_at;
CREATE VIEW v_product_sales AS
 SELECT p.product_id,p.product_name,p.category,SUM(i.quantity) AS units_sold,
 ROUND(SUM(i.line_amount_cents)/100.0,2) AS gross_sales_yuan
 FROM order_items i JOIN orders o ON i.order_id=o.order_id
 JOIN products p ON p.product_id=i.product_id
 WHERE o.status IN ('paid','completed') GROUP BY p.product_id,p.product_name,p.category;
"""

QUESTIONS = [
 ("已支付及已完成订单的总销售额是多少元？", "SELECT ROUND(SUM(order_amount_cents)/100.0,2) AS gross_sales_yuan FROM orders WHERE status IN ('paid','completed')"),
 ("每天的支付订单数和销售额是多少？", "SELECT * FROM v_daily_sales ORDER BY sales_date"),
 ("销售额最高的前5个商品是什么？", "SELECT product_name,gross_sales_yuan FROM v_product_sales ORDER BY gross_sales_yuan DESC,product_id LIMIT 5"),
 ("各渠道的支付订单数和销售额是多少？", "SELECT channel,COUNT(*) AS order_count,ROUND(SUM(order_amount_cents)/100.0,2) AS sales_yuan FROM orders WHERE status IN ('paid','completed') GROUP BY channel ORDER BY sales_yuan DESC,channel"),
 ("已支付及已完成订单的平均客单价是多少元？", "SELECT ROUND(AVG(order_amount_cents)/100.0,2) AS average_order_yuan FROM orders WHERE status IN ('paid','completed')"),
 ("各省份客户贡献的销售额是多少？", "SELECT c.province,ROUND(SUM(o.order_amount_cents)/100.0,2) AS sales_yuan FROM orders o JOIN customers c ON c.customer_id=o.customer_id WHERE o.status IN ('paid','completed') GROUP BY c.province ORDER BY sales_yuan DESC,c.province"),
 ("各商品类目的销量和销售额是多少？", "SELECT category,SUM(units_sold) AS units_sold,ROUND(SUM(gross_sales_yuan),2) AS sales_yuan FROM v_product_sales GROUP BY category ORDER BY sales_yuan DESC,category"),
 ("退款总额是多少元？", "SELECT ROUND(SUM(refund_amount_cents)/100.0,2) AS refunds_yuan FROM refunds"),
 ("扣除退款后的净销售额是多少元？", "SELECT ROUND(((SELECT SUM(order_amount_cents) FROM orders WHERE status IN ('paid','completed'))-COALESCE((SELECT SUM(refund_amount_cents) FROM refunds),0))/100.0,2) AS net_sales_yuan"),
 ("消费金额最高的前10位客户是谁？", "SELECT c.customer_id,c.customer_name,ROUND(SUM(o.order_amount_cents)/100.0,2) AS spending_yuan FROM orders o JOIN customers c ON c.customer_id=o.customer_id WHERE o.status IN ('paid','completed') GROUP BY c.customer_id,c.customer_name ORDER BY spending_yuan DESC,c.customer_id LIMIT 10"),
 ("各订单状态分别有多少订单？", "SELECT status,COUNT(*) AS order_count FROM orders GROUP BY status ORDER BY status"),
 ("有至少两笔已支付或已完成订单的客户有多少？", "SELECT COUNT(*) AS repeat_customers FROM (SELECT customer_id FROM orders WHERE status IN ('paid','completed') GROUP BY customer_id HAVING COUNT(*)>=2)"),
]


def main():
    for folder in ("data/metadata", "data/vectors", "logs", "work"):
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    # Editable source installs do not materialize wheel-only pilot templates.
    # Provision upstream Alembic files into our separate metadata directory.
    template = ROOT / "DB-GPT/pilot/meta_data"
    for relative in ("alembic.ini", "alembic/env.py", "alembic/script.py.mako", "alembic/README"):
        source = template / relative
        target = ROOT / "data/metadata" / relative
        if source.is_file() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    secret = ROOT / "data/local-encryption-key.txt"
    if not secret.exists():
        secret.write_text(secrets.token_urlsafe(32), encoding="utf-8")
    if not DB_PATH.exists():
        rng = random.Random(20261025)
        with sqlite3.connect(DB_PATH) as con:
            con.executescript(SCHEMA)
            provinces = ["浙江", "江苏", "广东", "上海", "北京", "四川"]
            for cid in range(1, 301):
                con.execute("INSERT INTO customers VALUES (?,?,?,?)", (cid, f"示例客户{cid:04d}", rng.choice(provinces), "2026-01-01"))
            categories = {"数码": ["无线耳机", "机械键盘", "充电器", "移动电源", "鼠标"],
                          "家居": ["台灯", "保温杯", "收纳盒", "靠垫", "加湿器"],
                          "服饰": ["短袖", "运动裤", "卫衣", "帆布鞋", "帽子"],
                          "食品": ["咖啡豆", "坚果礼盒", "麦片", "茶叶", "饼干"]}
            products = []
            for category, names in categories.items():
                for name in names:
                    pid = len(products) + 1
                    price = rng.randrange(19, 500) * 100
                    products.append((pid, name, category, price))
            con.executemany("INSERT INTO products VALUES (?,?,?,?)", products)
            item_id = refund_id = 0
            for oid in range(1, 1501):
                cid = rng.randint(1, 300)
                ordered = date(2026, 7, 1) + timedelta(days=rng.randrange(117))
                status = rng.choices(["paid", "completed", "cancelled", "pending"], [20, 65, 10, 5])[0]
                channel = rng.choice(["APP", "小程序", "网页", "直播"])
                lines = []
                for product in rng.sample(products, rng.randint(1, 4)):
                    quantity = rng.randint(1, 3)
                    item_id += 1
                    lines.append((item_id, oid, product[0], quantity, product[3], quantity * product[3]))
                total = sum(line[5] for line in lines)
                con.execute("INSERT INTO orders VALUES (?,?,?,?,?,?)", (oid, cid, ordered.isoformat(), status, channel, total))
                con.executemany("INSERT INTO order_items VALUES (?,?,?,?,?,?)", lines)
                if status in ("paid", "completed") and rng.random() < 0.08:
                    refund_id += 1
                    refunded = min(ordered + timedelta(days=rng.randint(1, 7)), date(2026, 10, 25))
                    con.execute("INSERT INTO refunds VALUES (?,?,?,?,?)", (refund_id, oid, rng.randint(1, total), refunded.isoformat(), rng.choice(["商品退货", "差价退款", "物流问题"])))
        print(f"Created synthetic database: {DB_PATH}")
    else:
        print(f"Preserved existing database: {DB_PATH}")

    with sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True) as con:
        con.row_factory = sqlite3.Row
        assert not con.execute("PRAGMA foreign_key_check").fetchall(), "Broken foreign keys"
        assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert con.execute("SELECT COUNT(*) FROM orders o WHERE order_amount_cents != (SELECT SUM(line_amount_cents) FROM order_items i WHERE i.order_id=o.order_id)").fetchone()[0] == 0
        cases = [{"id": n, "question": question, "reference_sql": sql, "expected_rows": [dict(row) for row in con.execute(sql)]} for n, (question, sql) in enumerate(QUESTIONS, 1)]
        (ROOT / "data/benchmark.json").write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
        summary = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ("customers", "products", "orders", "order_items", "refunds")}
        summary["benchmark_cases"] = len(cases)
        (ROOT / "data/dataset-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

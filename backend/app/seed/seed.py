"""种子脚本 (v4, 电商运营): 业务 mock 数据 + 异常 SKU + 政策知识库。

用法 (容器内): python -m app.seed.seed
依赖: postgres / milvus / model_server / ollama 就绪。确定性 (random seed=42), 幂等(已有数据则跳过)。
"""
from __future__ import annotations

import glob
import os
import random
from datetime import datetime, timedelta, timezone

from app.db.engine import SessionLocal
from app.db.models import (
    Campaign,
    Customer,
    Inventory,
    Order,
    OrderItem,
    Persona,
    Product,
    Return,
    SupportTicket,
    Connector,
    IndexAttempt,
    SourceType,
)
from app.ingestion.indexer import index_raw_docs
from app.ingestion.parser import parse_file

random.seed(42)
NOW = datetime(2026, 6, 25, tzinfo=timezone.utc)

ANOMALY_SKU = "NX-AIR-FRYER-001"
CATEGORIES = ["kitchen", "home", "electronics", "outdoor", "beauty", "toys"]

SYSTEM_PROMPT = (
    "你是 Nexora 电商运营助手 (Ops Agent)。你能结合知识库政策与订单/库存/退货/工单等业务数据, "
    "分析异常商品、判断退款、创建工单并通知运营组。回答要给出依据 (政策用 [n] 标注), "
    "涉及退款>$200、暂停广告等高风险操作时需走人工审批。"
)

SEED_DIR = os.path.dirname(__file__)
DOCS_GLOB = os.path.join(SEED_DIR, "docs", "*.md")


def _dt(days_ago: float) -> datetime:
    return NOW - timedelta(days=days_ago)


def seed_persona(db) -> None:
    if db.query(Persona).filter(Persona.name == "运营助手").first():
        print("persona 已存在, 跳过")
        return
    db.add(
        Persona(
            name="运营助手",
            description="电商运营多工具 Agent (演示)",
            system_prompt=SYSTEM_PROMPT,
            tools=[
                "query_sales_data", "query_inventory", "query_returns",
                "query_support_tickets", "retrieve_policy", "create_ops_ticket",
                "send_slack_message", "pause_campaign", "evaluate_refund", "approve_refund_mock",
            ],
        )
    )
    db.commit()
    print("已创建 persona: 运营助手")


def seed_business(db) -> None:
    if db.query(Product).count() > 0:
        print("业务数据已存在, 跳过")
        return

    # ---- products (200, 含异常 SKU) ----
    products: list[Product] = []
    anomaly = Product(sku=ANOMALY_SKU, name="Nexora 空气炸锅 Pro", category="kitchen",
                      price=259.0, status="active")
    products.append(anomaly)
    for i in range(1, 200):
        products.append(Product(
            sku=f"NX-{i:04d}",
            name=f"商品 {i}",
            category=random.choice(CATEGORIES),
            price=round(random.uniform(9, 400), 2),
            status="active",
        ))
    db.add_all(products)
    db.flush()
    pid = {p.sku: p.id for p in products}

    # ---- customers (1000) ----
    customers = [
        Customer(name=f"客户{i}", email=f"user{i}@example.com",
                 tier=random.choice(["standard", "standard", "vip"]))
        for i in range(1, 1001)
    ]
    db.add_all(customers)
    db.flush()
    cust_ids = [c.id for c in customers]

    # ---- inventory (每个 product) ----
    inv = []
    for p in products:
        stock = 12 if p.sku == ANOMALY_SKU else random.randint(20, 500)
        inv.append(Inventory(sku=p.sku, stock=stock, safety_stock=30))
    db.add_all(inv)

    # ---- campaigns (50, 异常 SKU 在投) ----
    camps = [Campaign(name=f"{ANOMALY_SKU} 夏促", sku=ANOMALY_SKU, channel="search",
                      status="active", daily_budget=800.0)]
    for i in range(1, 50):
        sku = f"NX-{random.randint(1,199):04d}"
        camps.append(Campaign(name=f"活动{i}", sku=sku, channel=random.choice(["search", "social"]),
                              status=random.choice(["active", "active", "paused"]),
                              daily_budget=round(random.uniform(100, 1000), 2)))
    db.add_all(camps)

    # ---- orders + order_items (普通: 5000 单, ~12000 项) ----
    order_id = 0
    orders: list[Order] = []
    items: list[OrderItem] = []
    skus = [p.sku for p in products if p.sku != ANOMALY_SKU]
    for _ in range(5000):
        order_id += 1
        created = _dt(random.uniform(0, 30))
        n = random.randint(1, 3)
        total = 0.0
        chosen = random.sample(skus, n)
        o = Order(id=order_id, customer_id=random.choice(cust_ids), status="paid",
                  total=0.0, created_at=created)
        for sku in chosen:
            prod = next(p for p in products if p.sku == sku)
            qty = random.randint(1, 2)
            items.append(OrderItem(order_id=order_id, product_id=pid[sku], sku=sku,
                                   qty=qty, price=prod.price))
            total += prod.price * qty
        o.total = round(total, 2)
        orders.append(o)

    # ---- 异常 SKU 注入: 销量下降 38% (prev7=100, last7=62), 退货率 18.4% ----
    def add_anomaly_orders(count: int, day_lo: float, day_hi: float) -> list[int]:
        ids = []
        nonlocal order_id
        for _ in range(count):
            order_id += 1
            created = _dt(random.uniform(day_lo, day_hi))
            orders.append(Order(id=order_id, customer_id=random.choice(cust_ids),
                                status="paid", total=259.0, created_at=created))
            items.append(OrderItem(order_id=order_id, product_id=pid[ANOMALY_SKU],
                                   sku=ANOMALY_SKU, qty=1, price=259.0))
            ids.append(order_id)
        return ids

    prev7 = add_anomaly_orders(100, 7, 14)     # 上一个 7 天
    last7 = add_anomaly_orders(62, 0, 7)       # 最近 7 天 → 下降 38%
    earlier = add_anomaly_orders(88, 14, 30)   # 更早, 凑总量 250
    anomaly_orders = prev7 + last7 + earlier

    # ---- 固定演示订单 #10086 (退款审批 demo: 金额 $300 > $200 阈值) ----
    orders.append(Order(id=10086, customer_id=cust_ids[0], status="paid", total=300.0,
                        created_at=_dt(3)))
    items.append(OrderItem(order_id=10086, product_id=pid[ANOMALY_SKU], sku=ANOMALY_SKU,
                           qty=1, price=300.0))

    db.add_all(orders)
    db.add_all(items)
    db.flush()

    # ---- returns (普通 500 + 异常 46 = 18.4% of 250) ----
    returns = []
    for _ in range(500):
        returns.append(Return(order_id=random.randint(1, 5000),
                              sku=random.choice(skus),
                              reason=random.choice(["size", "changed mind", "damaged", "late"]),
                              amount=round(random.uniform(10, 300), 2),
                              created_at=_dt(random.uniform(0, 30))))
    for oid in random.sample(anomaly_orders, 46):
        returns.append(Return(order_id=oid, sku=ANOMALY_SKU, reason="broken handle",
                              amount=259.0, created_at=_dt(random.uniform(0, 10))))
    db.add_all(returns)

    # ---- support tickets (普通 770 + 异常 30 broken handle) ----
    tickets = []
    for _ in range(770):
        tickets.append(SupportTicket(sku=random.choice(skus),
                                     subject=random.choice(["咨询", "物流慢", "尺寸问题", "申请退款"]),
                                     body="顾客咨询/投诉 (示例)", status=random.choice(["open", "closed"]),
                                     created_at=_dt(random.uniform(0, 30))))
    for _ in range(30):
        tickets.append(SupportTicket(sku=ANOMALY_SKU, subject="broken handle",
                                     body="顾客反映空气炸锅把手断裂 (broken handle)", status="open",
                                     created_at=_dt(random.uniform(0, 7))))
    db.add_all(tickets)
    db.commit()
    print(f"业务数据: products={len(products)} customers={len(customers)} "
          f"orders={len(orders)} items={len(items)} returns={len(returns)} tickets={len(tickets)}")


def seed_docs(db) -> None:
    paths = sorted(glob.glob(DOCS_GLOB))
    if not paths:
        print("未找到政策文档")
        return
    connector = Connector(name="seed-policies", source=SourceType.file_upload,
                          config={"filenames": [os.path.basename(p) for p in paths]})
    db.add(connector)
    db.flush()
    attempt = IndexAttempt(connector_id=connector.id)
    db.add(attempt)
    db.commit()
    raws = [parse_file(p, os.path.basename(p)) for p in paths]
    attempt = index_raw_docs(db, raws, attempt, connector.id)
    print(f"政策知识库索引: status={attempt.status.value} chunks={attempt.num_chunks}")


def main() -> None:
    db = SessionLocal()
    try:
        seed_persona(db)
        seed_business(db)
        seed_docs(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()

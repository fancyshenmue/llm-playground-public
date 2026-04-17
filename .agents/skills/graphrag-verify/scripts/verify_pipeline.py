#!/usr/bin/env python3
"""
Enterprise GraphRAG Pipeline Verification Script
=================================================
Performs a comprehensive health check across PostgreSQL and Neo4j
after an ETL run. Cross-references results against the Phase 12
architecture specification.

Usage:
    pixi run python .agent/skills/graphrag-verify/scripts/verify_pipeline.py

Exit Codes:
    0 = All checks passed
    1 = One or more checks failed
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "backend", "ecommerce-graphrag"))

from core.database import get_neo4j_graph, get_postgres_pool

# ──────────────────────────────────────────────────
# Architecture Reference (from Phase 13 Specification)
# ──────────────────────────────────────────────────
EXPECTED_NODE_LABELS = {"Product", "Category", "Brand", "Feature", "Benefit", "Scenario", "Customer", "Order", "Review"}
EXPECTED_REL_TYPES_STRUCTURAL = {"BELONGS_TO", "PLACED", "CONTAINS", "WROTE", "ABOUT"}
EXPECTED_REL_TYPES_SEMANTIC = {"HAS_FEATURE", "PROVIDES_BENEFIT", "SUITABLE_FOR", "PRODUCED_BY"}
EXPECTED_CONSTRAINTS = {"product_id", "category_id", "customer_id", "review_id"}
EXPECTED_PG_TABLES = ["categories", "customers", "products", "orders", "order_items", "invoices", "reviews"]

passed = 0
failed = 0
warnings = 0


def check(name: str, condition: bool, detail: str = ""):
    global passed, failed
    icon = "✅" if condition else "❌"
    print(f"  {icon} {name}" + (f" — {detail}" if detail else ""))
    if condition:
        passed += 1
    else:
        failed += 1


def warn(name: str, detail: str = ""):
    global warnings
    print(f"  ⚠️  {name}" + (f" — {detail}" if detail else ""))
    warnings += 1


def verify_postgres():
    print("\n╔══════════════════════════════════════════╗")
    print("║   POSTGRESQL VERIFICATION                ║")
    print("╚══════════════════════════════════════════╝\n")

    verify_scale = int(os.environ.get("VERIFY_SCALE", os.environ.get("DATA_SCALE", "100000")))
    print(f"  🔍 Target Assert Scale: {verify_scale} (Control via VERIFY_SCALE or DATA_SCALE)")

    pool = get_postgres_pool()
    if not pool:
        check("PostgreSQL Connection", False, "Cannot connect to PostgreSQL")
        return

    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Table row counts
            counts = {}
            for table in EXPECTED_PG_TABLES:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cur.fetchone()[0]
                print(f"  📊 {table}: {counts[table]:,}")

            print()
            check("Categories populated", counts["categories"] > 0, f"{counts['categories']:,} rows")
            check("Customers populated", counts["customers"] > 0, f"{counts['customers']:,} rows")
            check(f"Products ≈ {verify_scale}", verify_scale * 0.9 <= counts["products"] <= verify_scale * 1.1, f"{counts['products']:,} rows")
            check("Orders populated", counts["orders"] > 0, f"{counts['orders']:,} rows")
            check("Order items populated", counts["order_items"] > 0, f"{counts['order_items']:,} rows")
            check("Invoices populated", counts["invoices"] > 0, f"{counts['invoices']:,} rows")
            check("Reviews populated", counts["reviews"] > 0, f"{counts['reviews']:,} rows")

            # FK integrity
            cur.execute("SELECT COUNT(*) FROM products p JOIN categories c ON p.category_id = c.id")
            fk_valid = cur.fetchone()[0]
            fk_pct = (fk_valid / counts["products"] * 100) if counts["products"] > 0 else 0
            check("FK Integrity = 100%", fk_pct == 100.0, f"{fk_valid:,}/{counts['products']:,} ({fk_pct:.1f}%)")

            # Diversity injection check
            cur.execute("SELECT reference, description FROM products LIMIT 1")
            row = cur.fetchone()
            if row:
                has_brand = any(b in row[0] for b in ["Lumina", "ApexGear", "NovaTech", "Vanguard", "Essential Goods",
                                                       "Urbanite", "EcoLife", "Zenith", "Pioneer", "Daily Basics",
                                                       "Aura", "Prism", "Global Direct", "Studio 99",
                                                       "Peak Performance", "NeoStyle", "Artisana", "EliteCraft",
                                                       "Creative Den", "Signature Supply"])
                has_lorem = "lorem" in (row[1] or "").lower() or "ipsum" in (row[1] or "").lower()
                check("Diversity injection (has brand)", has_brand, f"ref: {row[0][:60]}...")
                check("No Lorem Ipsum pollution", not has_lorem, "Description should be real e-commerce text")


def verify_neo4j():
    print("\n╔══════════════════════════════════════════╗")
    print("║   NEO4J VERIFICATION                     ║")
    print("╚══════════════════════════════════════════╝\n")

    verify_scale = int(os.environ.get("VERIFY_SCALE", os.environ.get("DATA_SCALE", "100000")))

    graph = get_neo4j_graph()
    if not graph:
        check("Neo4j Connection", False, "Cannot connect to Neo4j")
        return

    # Node counts by label
    labels = graph.query("MATCH (n) RETURN labels(n)[0] AS label, COUNT(n) AS count ORDER BY count DESC")
    label_map = {r["label"]: r["count"] for r in labels}
    total_nodes = sum(label_map.values())

    print("  📊 Node Labels:")
    for label, count in label_map.items():
        print(f"     {label}: {count:,}")

    print()
    check(f"Product nodes ≈ {verify_scale}", verify_scale * 0.9 <= label_map.get("Product", 0) <= verify_scale * 1.1,
          f"{label_map.get('Product', 0):,}")
    check("Category nodes exist", label_map.get("Category", 0) > 0,
          f"{label_map.get('Category', 0)}")

    # Check all expected label types exist (only if LLM extraction ran)
    present_labels = set(label_map.keys())
    missing_semantic = EXPECTED_NODE_LABELS - present_labels
    if missing_semantic:
        if label_map.get("Feature", 0) == 0 and label_map.get("Brand", 0) == 0:
            warn("Semantic node types missing", f"Missing: {missing_semantic}. Run ETL with EXTRACT_LIMIT > 0")
        else:
            check("All ontology node types present", False, f"Missing: {missing_semantic}")
    else:
        check("All ontology node types present", True, str(present_labels))

    # Relationship types
    rels = graph.query("MATCH ()-[r]->() RETURN type(r) AS type, COUNT(r) AS count ORDER BY count DESC")
    rel_map = {r["type"]: r["count"] for r in rels}

    print("\n  📊 Relationship Types:")
    for rtype, count in rel_map.items():
        print(f"     {rtype}: {count:,}")

    print()
    check("Structural Core edges exist", rel_map.get("BELONGS_TO", 0) > 0 and rel_map.get("WROTE", 0) > 0,
          f"BELONGS_TO: {rel_map.get('BELONGS_TO', 0):,}, WROTE: {rel_map.get('WROTE', 0):,}")

    present_semantic_rels = EXPECTED_REL_TYPES_SEMANTIC.intersection(set(rel_map.keys()))
    if len(present_semantic_rels) > 0:
        check("Semantic relationship types present", True, str(present_semantic_rels))
    else:
        warn("No semantic relationships", "Run ETL with EXTRACT_LIMIT > 0 for LLM extraction")

    # Constraints
    constraints = graph.query("SHOW CONSTRAINTS")
    constraint_names = {c.get("name", "") for c in constraints}
    print(f"\n  📊 Constraints: {constraint_names}")
    check("Product UNIQUE constraint", "product_id" in constraint_names)
    check("Category UNIQUE constraint", "category_id" in constraint_names)
    check("Customer UNIQUE constraint", "customer_id" in constraint_names)
    check("Review UNIQUE constraint", "review_id" in constraint_names)

    # Indexes
    hybrid = graph.query("SHOW INDEXES YIELD name, type, state WHERE name = 'product_hybrid_index' RETURN name, type, state")
    keyword = graph.query("SHOW INDEXES YIELD name, type, state WHERE name = 'product_keyword_index' RETURN name, type, state")

    check("Vector index (product_hybrid_index) exists",
          len(hybrid) > 0, f"{hybrid[0] if hybrid else 'MISSING'}")
    check("Keyword index (product_keyword_index) exists",
          len(keyword) > 0, f"{keyword[0] if keyword else 'MISSING'}")

    if hybrid:
        check("Vector index ONLINE", hybrid[0].get("state") == "ONLINE",
              f"state={hybrid[0].get('state')}")
    if keyword:
        check("Keyword index ONLINE", keyword[0].get("state") == "ONLINE",
              f"state={keyword[0].get('state')}")

    # Embedding coverage
    emb_count = graph.query("MATCH (p:Product) WHERE p.embedding IS NOT NULL RETURN COUNT(p) AS count")[0]["count"]
    product_count = label_map.get("Product", 0)
    emb_pct = (emb_count / product_count * 100) if product_count > 0 else 0
    check("Embedding coverage ≥ 95%", emb_pct >= 95.0,
          f"{emb_count:,}/{product_count:,} ({emb_pct:.1f}%)")

    # Semantic extraction coverage
    semantic = graph.query("MATCH (p:Product)-[r]->() WHERE type(r) <> 'BELONGS_TO' RETURN COUNT(DISTINCT p) AS count")[0]["count"]
    print(f"\n  📊 Products with semantic edges: {semantic}")
    if semantic == 0:
        warn("Zero semantic extractions", "This is expected if EXTRACT_LIMIT was 0 or ETL Part B was skipped")
    else:
        check("Semantic extraction completed", semantic > 0, f"{semantic} products have LLM-extracted knowledge")

    # Sample product verification
    sample = graph.query("""
        MATCH (p:Product) WHERE p.embedding IS NOT NULL
        RETURN p.id AS id, p.title AS title, p.price AS price,
               p.image AS image, p.category AS category
        LIMIT 2
    """)
    print("\n  📊 Sample Products:")
    for s in sample:
        img_status = "🖼️" if s.get("image") else "🚫"
        print(f"     [{s['id']}] {s['title']}")
        print(f"       price=${s['price']} | cat={s['category']} | img={img_status}")

    check("Products have price property", all(s.get("price") is not None for s in sample))
    check("Products have image property", all(s.get("image") is not None for s in sample))
    check("Products have category property", all(s.get("category") is not None for s in sample))


def main():
    print("=" * 50)
    print("  Enterprise GraphRAG Pipeline Verification")
    print("=" * 50)

    verify_postgres()
    verify_neo4j()

    print("\n" + "=" * 50)
    print(f"  RESULTS: {passed} passed, {failed} failed, {warnings} warnings")
    print("=" * 50)

    if failed > 0:
        print("\n  ❌ PIPELINE UNHEALTHY — Review failures above.")
        sys.exit(1)
    elif warnings > 0:
        print("\n  ⚠️  PIPELINE OPERATIONAL — Some items need attention.")
        sys.exit(0)
    else:
        print("\n  🟢 PIPELINE FULLY HEALTHY — All checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()

"""Seed Neo4j graph with demo companies and relationships."""
import os
import random

from neo4j import GraphDatabase

URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASS = os.environ["NEO4J_PASSWORD"]

INDUSTRIES = ["Construction", "Healthcare", "Manufacturing", "Technology", "Real Estate",
              "Energy", "Logistics", "Food & Beverage", "Retail", "Telecom"]

driver = GraphDatabase.driver(URI, auth=(USER, PASS))
try:
    with driver.session() as session:
        # Check if already seeded
        result = session.run("MATCH (n) RETURN count(n) AS c")
        if result.single()["c"] > 0:
            print(f"Graph already has {result.single()['c']} nodes, skipping")
            exit(0)

        # Create industry nodes
        for ind in INDUSTRIES:
            session.run("MERGE (i:Industry {name: $name})", name=ind)
        print(f"Created {len(INDUSTRIES)} industry nodes")

        # Create company nodes
        for i in range(1, 1001):
            industry = random.choice(INDUSTRIES)
            session.run("""
                MERGE (c:Company {cr_number: $cr})
                SET c.name = $name, c.industry = $industry
            """, cr=f"{1000000000 + i}", name=f"Demo Company {i}", industry=industry)
        print("Created 1000 company nodes")

        # Link companies to industries
        for i in range(1, 1001):
            industry = random.choice(INDUSTRIES)
            session.run("""
                MATCH (c:Company {cr_number: $cr})
                MATCH (i:Industry {name: $industry})
                MERGE (c)-[:BELONGS_TO]->(i)
            """, cr=f"{1000000000 + i}", industry=industry)
        print("Linked companies to industries")

        # Create some supplier relationships
        for _ in range(500):
            a = random.randint(1, 1000)
            b = random.randint(1, 1000)
            if a != b:
                session.run("""
                    MATCH (a:Company {cr_number: $cr1})
                    MATCH (b:Company {cr_number: $cr2})
                    MERGE (a)-[:SUPPLIES]->(b)
                """, cr1=f"{1000000000 + a}", cr2=f"{1000000000 + b}")
        print("Created 500 supplier relationships")

        result = session.run("MATCH (n) RETURN count(n) AS c, count(DISTINCT labels(n)) AS labels")
        row = result.single()
        print(f"Graph now has {row['c']} nodes across {row['labels']} labels")
finally:
    driver.close()

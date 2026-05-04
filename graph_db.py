import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class KnowledgeGraph:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_relationship(self, entity1, relation, entity2):
        with self.driver.session() as session:
            session.execute_write(self._create_and_return_relationship, entity1, relation, entity2)

    @staticmethod
    def _create_and_return_relationship(tx, entity1, relation, entity2):
        # We sanitize the relation string to be a valid Neo4j relationship type
        clean_relation = relation.upper().replace(' ', '_').replace('-', '_')
        if not clean_relation.replace('_', '').isalnum():
             clean_relation = "RELATED_TO"
             
        query = (
            "MERGE (e1:Entity {name: $e1_name}) "
            "MERGE (e2:Entity {name: $e2_name}) "
            f"MERGE (e1)-[r:{clean_relation}]->(e2) "
            "RETURN e1, r, e2"
        )
        result = tx.run(query, e1_name=entity1, e2_name=entity2)
        return result.data()
        
    def get_all_triples(self):
        with self.driver.session() as session:
            result = session.run("MATCH (n:Entity)-[r]->(m:Entity) RETURN n.name as source, type(r) as relation, m.name as target LIMIT 100")
            return [{"source": record["source"], "relation": record["relation"], "target": record["target"]} for record in result]

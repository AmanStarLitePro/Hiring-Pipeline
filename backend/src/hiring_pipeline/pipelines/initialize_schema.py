import os
import json
import uuid
import datetime
import concurrent.futures
import pandas as pd
from dotenv import load_dotenv
from cassandra.cluster import Session
from src.hiring_pipeline.logger_config import setup_logger
from src.hiring_pipeline.api.dependencies import get_cassandra_session

load_dotenv()
log = setup_logger(__name__)

class initialize_database:
    def __init__(self, session: Session = get_cassandra_session()):
        self.session = session
        self.keyspace = os.getenv("CASSANDRA_KEYSPACE")

    def create_tables_from_schema(self, schema_file: str):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        schema_path = os.path.join(project_root, "artifacts", schema_file)

        log.info(f"Resolved schema path: {schema_path}") 
        with open(schema_path, "r") as f:
            schema = json.load(f)

        self.session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {self.keyspace}
            WITH replication = {{ 'class': 'SimpleStrategy', 'replication_factor': 1 }};
        """)
        self.session.set_keyspace(self.keyspace)

        for table_name, table_def in schema["tables"].items():
            columns = table_def["columns"]
            primary_key = table_def.get("primary_key")

            col_defs = [f"{col_name} {col_type}" for col_name, col_type in columns.items()]
            if primary_key:
                pk = ", ".join(primary_key)
                col_defs.append(f"PRIMARY KEY ({pk})")

            if table_name == "stages":
                cql = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        {", ".join(col_defs)}
                    ) WITH CLUSTERING ORDER BY (entered_at DESC);
                """
            else:
                cql = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        {", ".join(col_defs)}
                    );
                """

            log.info(f"Creating table {table_name}...")
            self.session.execute(cql)

        log.info("All tables created successfully.")

    def insert_sample_data(self):
        candidates = [
            {"id": uuid.uuid4(), "name": "Priya Sharma", "email": "priya@example.com", "current_stage": "Screening"},
            {"id": uuid.uuid4(), "name": "Aman Kumar", "email": "aman@example.com", "current_stage": "Interview"},
            {"id": uuid.uuid4(), "name": "John Doe", "email": "john@example.com", "current_stage": "Applied"}
        ]

        def insert_candidate(candidate):
            self.session.execute(
                """
                INSERT INTO candidates (id, name, email, current_stage, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (candidate["id"], candidate["name"], candidate["email"], candidate["current_stage"], datetime.datetime.utcnow())
            )

        def insert_stage(candidate):
            self.session.execute(
                """
                INSERT INTO stages (candidate_id, stage_name, entered_at)
                VALUES (%s, %s, %s)
                """,
                (candidate["id"], candidate["current_stage"], datetime.datetime.utcnow())
            )

        def insert_audit(candidate):
            self.session.execute(
                """
                INSERT INTO audit_log (log_id, candidate_id, action, timestamp, metadata)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (uuid.uuid4(), candidate["id"], f"Moved to {candidate['current_stage']}", datetime.datetime.utcnow(), "Initial insert")
            )

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for candidate in candidates:
                futures.append(executor.submit(insert_candidate, candidate))
                futures.append(executor.submit(insert_stage, candidate))
                futures.append(executor.submit(insert_audit, candidate))
            concurrent.futures.wait(futures)

        log.info("Sample data inserted successfully.")
        return pd.DataFrame(candidates)

if __name__ == "__main__":
    db_initializer = initialize_database()
    db_initializer.create_tables_from_schema("schema.json")
    df = db_initializer.insert_sample_data()
    print("Sample data inserted to all tables")
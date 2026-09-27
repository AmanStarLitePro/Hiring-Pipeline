import os
from dotenv import load_dotenv
from src.hiring_pipeline.logger_config import setup_logger
from src.hiring_pipeline.api.dependencies import get_cassandra_session
import json
from cassandra.cluster import Session
import uuid
import datetime
import concurrent.futures
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pandas as pd

load_dotenv()

log = setup_logger(__name__)

def create_tables_from_schema(schema_file: str, session: Session = get_cassandra_session()):
    schema_path = os.path.join(os.path.dirname(__file__), schema_file)
    with open(schema_path, "r") as f:
        schema = json.load(f)

    keyspace = os.getenv("CASSANDRA_KEYSPACE")

    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {keyspace}
        WITH replication = {{ 'class': 'SimpleStrategy', 'replication_factor': 1 }};
    """)

    session.set_keyspace(keyspace)

    for table_name, table_def in schema["tables"].items():
        columns = table_def["columns"]
        primary_key = table_def.get("primary_key")

        col_defs = []
        for col_name, col_type in columns.items():
            col_defs.append(f"{col_name} {col_type}")

        if primary_key:
            pk = ", ".join(primary_key)
            col_defs.append(f"PRIMARY KEY ({pk})")

        cql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {", ".join(col_defs)}
            );
        """
        log.info(f"Creating table {table_name}...")
        session.execute(cql)

    log.info("All tables created successfully.")

def insert_sample_data(session: Session = get_cassandra_session()):
    """
    Insert sample data concurrently into candidates, stages, and audit_log tables.
    """
    candidates = [
        {"id": uuid.uuid4(), "name": "Priya Sharma", "email": "priya@example.com", "current_stage": "Screening"},
        {"id": uuid.uuid4(), "name": "Aman Kumar", "email": "aman@example.com", "current_stage": "Interview"},
        {"id": uuid.uuid4(), "name": "John Doe", "email": "john@example.com", "current_stage": "Applied"}
    ]

    def insert_candidate(candidate):
        session.execute(
            """
            INSERT INTO candidates (id, name, email, current_stage, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (candidate["id"], candidate["name"], candidate["email"], candidate["current_stage"], datetime.datetime.utcnow())
        )

    def insert_stage(candidate):
        session.execute(
            """
            INSERT INTO stages (candidate_id, stage_name, entered_at)
            VALUES (%s, %s, %s)
            """,
            (candidate["id"], candidate["current_stage"], datetime.datetime.utcnow())
        )

    def insert_audit(candidate):
        session.execute(
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

def generate_embeddings(df: pd.DataFrame, text_column: str = "name"):
    """
    Generate embeddings from a Pandas DataFrame column and build a FAISS index.
    
    Args:
        df (pd.DataFrame): DataFrame containing candidate data.
        text_column (str): Column name with text to embed (default: 'name').
    
    Returns:
        dict: encoder, index, vectors, and dimension info.
    """
    if df.empty or text_column not in df.columns:
        return {"error": "DataFrame is empty or missing required column"}

    encoder = SentenceTransformer("all-mpnet-base-v2")
    texts = df[text_column].tolist()

    vectors = encoder.encode(texts, convert_to_numpy=True).astype("float32")
    dim = vectors.shape[1]

    index = faiss.IndexFlatL2(dim)
    index.add(vectors)

    log.info(f"Generated {len(texts)} embeddings")
    log.info(f"Vector dimension: {dim}")
    log.info(f"Number of vectors in FAISS: {index.ntotal}")

    faiss.write_index(index, "faiss_index.bin")

    return {
        "dim": dim,
        "vectors": vectors,
        "encoder": encoder,
        "index": index,
        "df": df.reset_index(drop=True)
    }

def searching_to_Vector_DB(
    encoder,
    index,
    df: pd.DataFrame,
    search_query: str,
    k: int = 1
):
    if index.ntotal == 0:
        return pd.DataFrame({"error": ["Index is empty"]})

    vec = encoder.encode([search_query], convert_to_numpy=True).astype("float32")
    distances, indices = index.search(vec, min(k, index.ntotal))

    results = df.iloc[indices[0]].copy()
    results["distance"] = distances[0]
    return results

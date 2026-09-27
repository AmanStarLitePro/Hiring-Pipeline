import os
import json
import uuid
import datetime
import concurrent.futures
import pandas as pd
import faiss
from dotenv import load_dotenv
from cassandra.cluster import Session
from sentence_transformers import SentenceTransformer
from src.hiring_pipeline.logger_config import setup_logger
from src.hiring_pipeline.api.dependencies import get_cassandra_session

load_dotenv()
log = setup_logger(__name__)

class database_pipeline:
    def __init__(self, session: Session = get_cassandra_session()):
        self.session = session
        self.keyspace = os.getenv("CASSANDRA_KEYSPACE")
        self.encoder = SentenceTransformer("all-mpnet-base-v2")
        self.index = None
        self.df = None

    def fetch_table_data(self, table_name: str, limit: int = 50) -> pd.DataFrame:
            """
            Fetch data from a Cassandra table and return as a Pandas DataFrame.
            
            Args:
                table_name (str): Name of the table to query.
                limit (int): Max number of rows to fetch (default: 50).
            
            Returns:
                pd.DataFrame: DataFrame containing the table rows.
            """
            self.session.set_keyspace(self.keyspace)
            query = f"SELECT * FROM {table_name} LIMIT {limit};"
            rows = self.session.execute(query)

            df = pd.DataFrame(list(rows))
            log.info(f"Fetched {len(df)} rows from {table_name}")
            return df

    def fetch_all_candidate_data(self, limit: int = 50) -> pd.DataFrame:
        """
        Merge candidates, stages, and audit_log into a single enriched dataframe.
        Each row represents one candidate with their latest stage and full audit trail.
        """
        self.session.set_keyspace(self.keyspace)

        candidates = list(self.session.execute(f"SELECT * FROM candidates LIMIT {limit};"))
        enriched = []

        for c in candidates:
            stage_row = self.session.execute(
                "SELECT stage_name, entered_at FROM stages WHERE candidate_id=%s LIMIT 1",
                (c.id,)
            ).one()

            logs = list(self.session.execute(
                "SELECT action, timestamp, metadata FROM audit_log WHERE candidate_id=%s",
                (c.id,)
            ))

            enriched.append({
                "id": str(c.id),
                "name": c.name,
                "email": c.email,
                "current_stage": c.current_stage,
                "created_at": c.created_at,
                "latest_stage": stage_row.stage_name if stage_row else None,
                "entered_at": stage_row.entered_at if stage_row else None,
                "audit_log": [
                    {
                        "action": log.action,
                        "timestamp": log.timestamp,
                        "metadata": log.metadata
                    } for log in logs
                ]
            })

        df = pd.DataFrame(enriched)
        log.info(f"Fetched and merged {len(df)} candidates with stages + audit logs")
        return df

    def generate_embeddings(self, df: pd.DataFrame, text_columns: list = ["name"]):
        if df.empty:
            return {"error": "DataFrame is empty"}

        combined_texts = df[text_columns].astype(str).agg(" ".join, axis=1).tolist()

        vectors = self.encoder.encode(combined_texts, convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(vectors)

        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)
        self.df = df.reset_index(drop=True)

        log.info(f"Generated {len(combined_texts)} embeddings from {text_columns}")
        return {"dim": vectors.shape[1], "vectors": vectors, "index": self.index, "df": self.df}

    def search(self, query: str, k: int = 3, columns: list = None):
        if self.index is None or self.index.ntotal == 0:
            return pd.DataFrame({"error": ["Index is empty"]})

        if columns:
            query_text = " ".join([str(query)])
        else:
            query_text = query

        vec = self.encoder.encode([query_text], convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(vec)

        distances, indices = self.index.search(vec, min(k, self.index.ntotal))
        results = self.df.iloc[indices[0]].copy()
        results["similarity"] = distances[0]
        return results

    def hybrid_search(self, query: str, k: int = 3):
            exact_matches = self.df[self.df["name"].str.lower() == query.lower()]
            if not exact_matches.empty:
                exact_matches["distance"] = 0.0
                return exact_matches

            return self.search(query, k)

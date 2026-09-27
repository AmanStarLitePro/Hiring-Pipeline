from src.hiring_pipeline.pipelines.database_pipeline import database_pipeline
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class SearchOutput(BaseModel):
    records: list = Field(default=[], description="List of records matching the search query")

class RAGPipeline:
    def __init__(self):
        self.db_pipeline = database_pipeline()
        self.structured_llm = None

    def initialize_llm_model(self):
        llm = ChatGroq(model="openai/gpt-oss-120b")
        self.structured_llm = llm.with_structured_output(SearchOutput, method="json_mode")

    def generate_response(self, search_query: str) -> SearchOutput:
        if not self.structured_llm:
            raise RuntimeError("LLM model not initialized. Call initialize_llm_model() first.")

        df = self.db_pipeline.fetch_all_candidate_data()
        self.db_pipeline.generate_embeddings(df, text_columns=df.columns.tolist())

        retrieved = self.db_pipeline.search(search_query, k=5)
        records_dict = retrieved.to_dict(orient="records")

        # prompt = f"""
        # You are a recruiter assistant.
        # The user asked: "{search_query}"
        # Here are candidate records: {records_dict}
        # filters the matching records only and return them inside the 'records' field of the JSON output.
        # """

        prompt = f"""
        You are a recruiter assistant.
        The user asked: "{search_query}"
        Here are candidate records: {records_dict}

        If there are matching records, return them inside the 'records' field of the JSON output.
        If no records match, return a single object inside 'records' with a 'reason' field explaining why nothing was found.
        """

        return self.structured_llm.invoke(prompt)
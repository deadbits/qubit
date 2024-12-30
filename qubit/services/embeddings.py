"""OpenAI client."""

from typing import List
from loguru import logger
from openai import OpenAI

from qubit.models.config import Config


class OpenAIClient:
    """OpenAI client."""

    def __init__(self, config: Config):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=config.embeddings.openai_api_key)
        self.embedding_model = config.embeddings.openai_embedding_model

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        logger.info(f"Generating embeddings for {len(texts)} text(s)")
        response = self.client.embeddings.create(
            input=texts,
            model=self.embedding_model,
            encoding_format="float"
        )
        return [v.embedding for v in response.data]

"""Application module for rag-embedder."""


class App:
    """Batch embedding and storage application for RAG system."""

    def run(self) -> None:
        """
        Run the embedder.

        Load chunks from JSON, generate embeddings, save to JSON and database.
        """
        raise NotImplementedError  # TODO: implement

    @staticmethod
    async def _write_to_db(results: list) -> None:
        """
        Write embedding results to the database.

        Parameters
        ----------
        results : list
            List of ``ChunkWithEmbedding`` objects.
        """
        raise NotImplementedError  # TODO: implement

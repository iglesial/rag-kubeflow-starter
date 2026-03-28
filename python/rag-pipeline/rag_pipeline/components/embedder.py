"""KFP container component for the embedder."""

from kfp import dsl

EMBEDDER_IMAGE = "rag-embedder:local"


@dsl.container_component
def embedder_component(
    chunks_artifact: dsl.Input[dsl.Artifact],
    db_url: str,
    embedding_model: str,
    batch_size: int,
    embeddings_artifact: dsl.Output[dsl.Artifact],
) -> dsl.ContainerSpec:
    """
    KFP component that runs rag-embedder in a container.

    Parameters
    ----------
    chunks_artifact : dsl.Input[dsl.Artifact]
        Input artifact from the loader (chunked JSON).
    db_url : str
        PostgreSQL connection string.
    embedding_model : str
        Sentence-transformers model name.
    batch_size : int
        Batch size for embedding.
    embeddings_artifact : dsl.Output[dsl.Artifact]
        Output artifact for embeddings JSON.

    Returns
    -------
    dsl.ContainerSpec
        Container specification for the embedder.
    """
    raise NotImplementedError  # TODO: implement

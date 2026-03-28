"""KFP container component for the document loader."""

from kfp import dsl

LOADER_IMAGE = "rag-loader:local"


@dsl.container_component
def loader_component(
    input_dir: str,
    chunk_size: int,
    chunk_overlap: int,
    chunks_artifact: dsl.Output[dsl.Artifact],
) -> dsl.ContainerSpec:
    """
    KFP component that runs rag-loader in a container.

    Parameters
    ----------
    input_dir : str
        Path to documents inside the container.
    chunk_size : int
        Maximum characters per chunk.
    chunk_overlap : int
        Overlap between consecutive chunks.
    chunks_artifact : dsl.Output[dsl.Artifact]
        Output artifact for chunked JSON.

    Returns
    -------
    dsl.ContainerSpec
        Container specification for the loader.
    """
    raise NotImplementedError  # TODO: implement

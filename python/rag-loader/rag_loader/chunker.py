"""Recursive character text splitter for rag-loader."""

SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def chunk_text(text: str, chunk_size: int = 512, chunk_overlap: int = 64) -> list[str]:
    """
    Split text into overlapping chunks using a recursive character strategy.

    Tries separators in order (paragraph, newline, sentence, word, character)
    and falls back to the next separator when a segment exceeds ``chunk_size``.

    Parameters
    ----------
    text : str
        The input text to split.
    chunk_size : int
        Maximum number of characters per chunk.
    chunk_overlap : int
        Number of overlapping characters between consecutive chunks.

    Returns
    -------
    list[str]
        List of text chunks.

    Raises
    ------
    ValueError
        If ``chunk_overlap`` is greater than or equal to ``chunk_size``.
    """
    raise NotImplementedError  # TODO: implement


def _split_recursive(text: str, chunk_size: int, sep_idx: int) -> list[str]:
    """
    Recursively split text using the separator hierarchy.

    Parameters
    ----------
    text : str
        Text to split.
    chunk_size : int
        Maximum chunk size.
    sep_idx : int
        Current index into the ``SEPARATORS`` list.

    Returns
    -------
    list[str]
        List of text segments.
    """
    raise NotImplementedError  # TODO: implement


def _merge_with_overlap(segments: list[str], chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Merge small segments into chunks and add overlap between them.

    Parameters
    ----------
    segments : list[str]
        Text segments to merge.
    chunk_size : int
        Maximum chunk size.
    chunk_overlap : int
        Target overlap between consecutive chunks.

    Returns
    -------
    list[str]
        Merged chunks with overlap.
    """
    raise NotImplementedError  # TODO: implement

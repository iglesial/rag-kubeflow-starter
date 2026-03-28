"""Document reader module for rag-loader."""

from pathlib import Path

SUPPORTED_EXTENSIONS = {".txt", ".md"}


def read_documents(input_dir: str) -> list[dict[str, object]]:
    """
    Read all supported text files from a directory.

    Reads ``.txt`` and ``.md`` files (non-recursive) and returns their
    content along with metadata.

    Parameters
    ----------
    input_dir : str
        Path to the directory containing documents.

    Returns
    -------
    list[dict[str, object]]
        List of dicts with keys ``document_name``, ``content``, ``metadata``.
        Metadata contains ``file_size`` (int) and ``extension`` (str).

    Raises
    ------
    FileNotFoundError
        If ``input_dir`` does not exist.
    NotADirectoryError
        If ``input_dir`` is not a directory.
    """
    raise NotImplementedError  # TODO: implement

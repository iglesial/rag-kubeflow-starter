"""Application module for rag-pipeline."""

PIPELINE_YAML = "rag-ingestion-pipeline.yaml"


class App:
    """Pipeline compiler and submitter application."""

    def run(self) -> None:
        """
        Compile and optionally submit the KFP pipeline.

        If ``compile_only`` is True, writes YAML and exits.
        Otherwise, submits the pipeline to the KFP cluster.
        """
        raise NotImplementedError  # TODO: implement

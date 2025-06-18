import logging
import math

from injector import inject, singleton
from llama_index.core.embeddings import BaseEmbedding, MockEmbedding

from bridgewell_gpt.paths import models_cache_path
from bridgewell_gpt.settings.settings import Settings

logger = logging.getLogger(__name__)


@singleton
class EmbeddingComponent:
    embedding_model: BaseEmbedding
    batch_size: int

    @inject
    def __init__(self, settings: Settings) -> None:
        embedding_mode = settings.embedding.mode
        logger.info("Initializing the embedding model in mode=%s", embedding_mode)
        self.batch_size = getattr(settings.embedding, "batch_size", 32)
        match embedding_mode:
            case "huggingface":
                try:
                    from llama_index.embeddings.huggingface import (  # type: ignore
                        HuggingFaceEmbedding,
                    )
                except ImportError as e:
                    raise ImportError(
                        "Local dependencies not found, install with `poetry install --extras embeddings-huggingface`"
                    ) from e

                self.embedding_model = HuggingFaceEmbedding(
                    model_name=settings.huggingface.embedding_hf_model_name,
                    cache_folder=str(models_cache_path),
                    trust_remote_code=settings.huggingface.trust_remote_code,
                )
            case "sagemaker":
                try:
                    from bridgewell_gpt.components.embedding.custom.sagemaker import (
                        SagemakerEmbedding,
                    )
                except ImportError as e:
                    raise ImportError(
                        "Sagemaker dependencies not found, install with `poetry install --extras embeddings-sagemaker`"
                    ) from e

                self.embedding_model = SagemakerEmbedding(
                    endpoint_name=settings.sagemaker.embedding_endpoint_name,
                )
            case "openai":
                try:
                    from bridgewell_gpt.components.embedding.custom.openai_batch import BatchedOpenAIEmbedding
                except ImportError as e:
                    raise ImportError(
                        "Custom OpenAI batching wrapper not found."
                    ) from e

                api_base = (
                    settings.openai.embedding_api_base or settings.openai.api_base
                )
                api_key = settings.openai.embedding_api_key or settings.openai.api_key
                model = settings.openai.embedding_model

                self.embedding_model = BatchedOpenAIEmbedding(
                    api_base=api_base,
                    api_key=api_key,
                    model=model,
                    batch_size=self.batch_size,
                )
            case "ollama":
                try:
                    from llama_index.embeddings.ollama import (  # type: ignore
                        OllamaEmbedding,
                    )
                    from ollama import Client  # type: ignore
                except ImportError as e:
                    raise ImportError(
                        "Local dependencies not found, install with `poetry install --extras embeddings-ollama`"
                    ) from e

                ollama_settings = settings.ollama

                # Calculate embedding model. If not provided tag, it will be use latest
                model_name = (
                    ollama_settings.embedding_model + ":latest"
                    if ":" not in ollama_settings.embedding_model
                    else ollama_settings.embedding_model
                )

                self.embedding_model = OllamaEmbedding(
                    model_name=model_name,
                    base_url=ollama_settings.embedding_api_base,
                )

                if ollama_settings.autopull_models:
                    if ollama_settings.autopull_models:
                        from bridgewell_gpt.utils.ollama import (
                            check_connection,
                            pull_model,
                        )

                        # TODO: Reuse llama-index client when llama-index is updated
                        client = Client(
                            host=ollama_settings.embedding_api_base,
                            timeout=ollama_settings.request_timeout,
                        )

                        if not check_connection(client):
                            raise ValueError(
                                f"Failed to connect to Ollama, "
                                f"check if Ollama server is running on {ollama_settings.api_base}"
                            )
                        pull_model(client, model_name)

            case "azopenai":
                try:
                    from llama_index.embeddings.azure_openai import (  # type: ignore
                        AzureOpenAIEmbedding,
                    )
                except ImportError as e:
                    raise ImportError(
                        "Azure OpenAI dependencies not found, install with `poetry install --extras embeddings-azopenai`"
                    ) from e

                azopenai_settings = settings.azopenai
                self.embedding_model = AzureOpenAIEmbedding(
                    model=azopenai_settings.embedding_model,
                    deployment_name=azopenai_settings.embedding_deployment_name,
                    api_key=azopenai_settings.api_key,
                    azure_endpoint=azopenai_settings.azure_endpoint,
                    api_version=azopenai_settings.api_version,
                )
            case "gemini":
                try:
                    from llama_index.embeddings.gemini import (  # type: ignore
                        GeminiEmbedding,
                    )
                except ImportError as e:
                    raise ImportError(
                        "Gemini dependencies not found, install with `poetry install --extras embeddings-gemini`"
                    ) from e

                self.embedding_model = GeminiEmbedding(
                    api_key=settings.gemini.api_key,
                    model_name=settings.gemini.embedding_model,
                )
            case "mistralai":
                try:
                    from llama_index.embeddings.mistralai import (  # type: ignore
                        MistralAIEmbedding,
                    )
                except ImportError as e:
                    raise ImportError(
                        "Mistral dependencies not found, install with `poetry install --extras embeddings-mistral`"
                    ) from e

                api_key = settings.openai.api_key
                model = settings.openai.embedding_model

                self.embedding_model = MistralAIEmbedding(
                    api_key=api_key,
                    model=model,
                )
            case "mock":
                # Not a random number, is the dimensionality used by
                # the default embedding model
                self.embedding_model = MockEmbedding(384)

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Batch embedding for OpenAI with profiling."""
        logger.info("get_embeddings called with %d texts", len(texts))
        if hasattr(self, "embedding_model") and self.embedding_model.__class__.__name__ == "OpenAIEmbedding":
            batch_size = self.batch_size
            all_embeddings = []
            n_batches = math.ceil(len(texts) / batch_size)
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                import time
                start = time.time()
                embeddings = self.embedding_model._get_text_embeddings(batch)
                logger.info(f"OpenAI embedding batch {i//batch_size+1}/{n_batches} (size {len(batch)}) took {time.time() - start:.2f}s")
                all_embeddings.extend(embeddings)
            return all_embeddings
        else:
            # Fallback to default
            logger.info("Using default embedding model for texts")
            return self.embedding_model._get_text_embeddings(texts)

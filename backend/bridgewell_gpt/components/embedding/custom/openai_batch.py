from llama_index.embeddings.openai import OpenAIEmbedding
import math
import time

class BatchedOpenAIEmbedding(OpenAIEmbedding):
    batch_size: int = 32

    def __init__(self, *args, batch_size=32, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch_size = batch_size

    def _get_text_embeddings(self, texts):
        batch_size = getattr(self, 'batch_size', 32)
        all_embeddings = []
        n_batches = math.ceil(len(texts) / batch_size)
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            start = time.time()
            embeddings = super()._get_text_embeddings(batch)
            print(f"OpenAI embedding batch {i//batch_size+1}/{n_batches} (size {len(batch)}) took {time.time() - start:.2f}s")
            all_embeddings.extend(embeddings)
        return all_embeddings 
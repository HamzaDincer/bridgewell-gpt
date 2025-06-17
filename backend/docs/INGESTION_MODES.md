# Ingestion Modes Documentation

## Overview

The Bridgewell GPT system supports multiple ingestion modes for processing documents. Each mode offers different trade-offs between performance and features.

## Available Ingestion Modes

### 1. Simple Mode (Default)
- **Configuration**: `ingest_mode: simple`
- **Features**: 
  - Sequential file processing
  - Full extraction support via LlamaExtract
  - RAG-based extraction for missing fields
  - Document phase tracking (parsing → extraction → embedding → rag → completed)
  - Background processing with threading
- **Use Case**: Best for reliable processing with all features enabled

### 2. Parallel Mode (Recommended for Production)
- **Configuration**: `ingest_mode: parallel`
- **Features**: 
  - Parallel file processing using multiprocessing
  - Full extraction support via LlamaExtract
  - RAG-based extraction for missing fields
  - Document phase tracking (parsing → extraction → embedding → rag → completed)
  - Background processing with threading
  - Better performance for large files
- **Use Case**: Recommended for production use with large document volumes

### 3. Batch Mode
- **Configuration**: `ingest_mode: batch`
- **Features**: 
  - Parallel file parsing
  - Batch embedding processing
  - No extraction or RAG support
- **Use Case**: Fast ingestion when extraction is not needed

### 4. Pipeline Mode
- **Configuration**: `ingest_mode: pipeline`
- **Features**: 
  - Maximum throughput with pipelined processing
  - No extraction or RAG support
- **Use Case**: Highest performance when only embeddings are needed

## Configuration

Update your `settings.yaml` file:

```yaml
embedding:
  mode: openai
  ingest_mode: parallel  # Options: simple, parallel, batch, pipeline
  count_workers: 4       # Number of parallel workers (for parallel, batch, pipeline modes)
  embed_dim: 1536
```

## Migration Guide

### Transitioning from Simple to Parallel Mode

1. **Update Configuration**:
   ```yaml
   embedding:
     ingest_mode: parallel
     count_workers: 4  # Adjust based on your CPU cores
   ```

2. **Test with Sample Documents**:
   - Start with a small set of documents
   - Verify extraction results match between modes
   - Check document phases update correctly

3. **Monitor Performance**:
   - Compare processing times
   - Monitor memory usage
   - Check CPU utilization

4. **Gradual Rollout**:
   - Use environment variables for easy switching:
     ```bash
     export EMBEDDING_INGEST_MODE=parallel
     ```
   - Run both modes in parallel during transition
   - Compare results for consistency

### Feature Comparison

| Feature | Simple | Parallel | Batch | Pipeline |
|---------|--------|----------|-------|----------|
| Extraction Support | ✅ | ✅ | ❌ | ❌ |
| RAG for Missing Fields | ✅ | ✅ | ❌ | ❌ |
| Document Phase Tracking | ✅ | ✅ | ❌ | ❌ |
| Background Processing | ✅ | ✅ | ❌ | ❌ |
| Parallel File Processing | ❌ | ✅ | ✅ | ✅ |
| Production Ready | ✅ | ✅ | ⚠️ | ⚠️ |

## Document Processing Phases

Both Simple and Parallel modes track document processing through these phases:

1. **parsing**: Document is being parsed from the original file
2. **extraction**: LlamaExtract is processing the document
3. **embedding**: Creating embeddings for vector search
4. **rag**: Using RAG to extract any missing fields
5. **completed**: Processing finished successfully
6. **error**: An error occurred during processing

## Best Practices

1. **For Production**:
   - Use `parallel` mode for better performance
   - Set `count_workers` to number of CPU cores - 1
   - Monitor system resources during processing

2. **For Development**:
   - Use `simple` mode for easier debugging
   - Enable detailed logging

3. **For Bulk Ingestion**:
   - Use `parallel` mode with appropriate worker count
   - Process files in batches to manage memory

## Troubleshooting

### Common Issues

1. **High Memory Usage**:
   - Reduce `count_workers`
   - Process smaller batches

2. **Extraction Failures**:
   - Check LlamaExtract API limits
   - Verify document format compatibility

3. **Phase Stuck in "processing"**:
   - Check logs for errors
   - Verify extraction component is initialized

## Future Roadmap

- The default mode will transition from `simple` to `parallel` after production validation
- `simple` mode will be maintained for compatibility but may be deprecated in future versions
- Additional optimizations planned for parallel extraction processing
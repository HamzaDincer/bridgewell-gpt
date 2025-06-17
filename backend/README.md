# Bridgewell GPT Backend

This is the backend service for Bridgewell GPT, a document processing and extraction system.

## Features

- Document ingestion with multiple processing modes
- Automatic extraction using LlamaExtract
- RAG-based extraction for missing fields
- Vector search capabilities
- RESTful API endpoints

## Quick Start

### Installation

```bash
poetry install
```

### Running

```bash
make dev
```

### Testing

```bash
make test
```

## Configuration

The application uses environment variables for configuration:

- `OPENAI_API_KEY`: Your OpenAI API key
- `LLAMA_CLOUD_API_KEY`: Your Llama Cloud API key
- `PORT`: Server port (default: 8080)

## Ingestion Modes

The system supports multiple ingestion modes to balance performance and features:

- **Simple Mode** (default): Sequential processing with full extraction and RAG support
- **Parallel Mode**: Parallel processing with full extraction and RAG support (recommended for production)
- **Batch Mode**: Fast parallel processing without extraction
- **Pipeline Mode**: Maximum throughput without extraction

See [docs/INGESTION_MODES.md](docs/INGESTION_MODES.md) for detailed documentation and migration guide.

## Deployment

The application can be deployed using Docker:

```bash
docker build -t bridgewell-gpt .
docker run -p 8080:8080 bridgewell-gpt
```

## Usage

Access the web interface at `http://your-domain:8080`

## API Documentation

Once running, visit http://localhost:8001/docs for the interactive API documentation.

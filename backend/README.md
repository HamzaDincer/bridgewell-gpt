# Bridgewell GPT

A production-ready AI tool for document extraction and analysis, customized for Bridgewell.

## Features

- Document Processing & Analysis
- OpenAI Integration
- Modern Web Interface
- Secure API Access
- Document Comparison Tools
- Benefit Analysis Features

## Configuration

The application uses environment variables for configuration:

- `OPENAI_API_KEY`: Your OpenAI API key
- `LLAMA_CLOUD_API_KEY`: Your Llama Cloud API key
- `PORT`: Server port (default: 8080)

## Deployment

The application can be deployed using Docker:

```bash
docker build -t bridgewell-gpt .
docker run -p 8080:8080 bridgewell-gpt
```

## Environment Variables

Required environment variables:

- `OPENAI_API_KEY`
- `LLAMA_CLOUD_API_KEY`

## Usage

Access the web interface at `http://your-domain:8080`

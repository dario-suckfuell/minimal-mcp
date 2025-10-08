# MCP Private Database (Pinecone)

A minimal, read-only MCP (Model Context Protocol) server that provides Deep Research-compatible Private Database functionality backed by Pinecone. This server exposes exactly two tools: `search` and `fetch` for document retrieval and content access.

## Features

- **Search**: Text-to-vector similarity search with preview results
- **Fetch**: Full content retrieval by document IDs
- **Read-only**: No indexing or document ingestion capabilities
- **Pinecone Integration**: Backed by Pinecone vector database
- **OpenAI Embeddings**: Configurable text embedding support
- **Deep Research Compatible**: Designed for seamless integration with Deep Research

## Quickstart

### 1. Environment Setup

Set up your local environment file:

```bash
# Quick setup (recommended)
make setup

# Or manually copy the example file
cp env.example .env
```

Edit your environment file with your actual values:

```bash
# Required Pinecone settings
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=your_index_name
PINECONE_HOST=your_pinecone_host

# Optional settings
NAMESPACE=your_namespace  # Optional
DEFAULT_TOP_K=8
MAX_CONTENT_CHARS=50000
ENABLE_EMBEDDING=true
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSIONS=3072
OPENAI_API_KEY=your_openai_api_key
```

### 2. Installation

```bash
# Install dependencies
make install
# or
pip install -r requirements.txt
```

### 3. Run the Server

```bash
# Start the MCP server
make run
# or
python -m mcp_private_db.main
```

The server will start on `http://0.0.0.0:8000` with the following endpoints:
- `/health` - Health check
- `/tools` - List available tools
- `/tools/search` - Search endpoint
- `/tools/fetch` - Fetch endpoint
- `/call` - Generic tool call endpoint
- `/sse/` - Deep Research compatibility endpoint

### 4. Test the Server

```bash
# Run tests
make test
# or
pytest tests/ -v
```

## Deep Research Integration

To integrate with Deep Research, add this configuration to your Deep Research settings:

```json
{
  "type": "mcp",
  "server_label": "private_db",
  "server_url": "http://0.0.0.0:8000",
  "require_approval": "never"
}
```

## API Contract

### Search Tool

**Purpose**: Find relevant documents using text similarity search.

**Input**:
- `query` (string): Search query text
- `top_k` (int, optional): Number of results (1-25, default: 8)

**Output**:
```json
{
  "results": [
    {
      "id": "document_id",
      "score": 0.95,
      "title": "Document Title",
      "snippet": "Preview text...",
      "source": "Document Source"
    }
  ]
}
```

**Behavior**:
- Converts text query to vector using OpenAI embeddings
- Queries Pinecone for similar documents
- Returns IDs, scores, and preview information only
- Never returns full document content

### Fetch Tool

**Purpose**: Retrieve full content for specific document IDs.

**Input**:
- `object_ids` (string[]): List of document IDs (1-50)

**Output**:
```json
{
  "objects": [
    {
      "id": "document_id",
      "content": "Full document content...",
      "metadata": {
        "title": "Document Title",
        "source": "Document Source",
        "uri": "Document URI",
        "truncated": false
      }
    }
  ]
}
```

**Behavior**:
- Fetches full content from Pinecone by IDs
- Truncates content if it exceeds `MAX_CONTENT_CHARS`
- Sets `metadata.truncated: true` when content is truncated
- Preserves all metadata fields

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PINECONE_API_KEY` | Yes | - | Pinecone API key |
| `PINECONE_INDEX` | Yes | - | Pinecone index name |
| `PINECONE_HOST` | Yes | - | Pinecone host/environment |
| `NAMESPACE` | No | - | Optional Pinecone namespace |
| `DEFAULT_TOP_K` | No | 8 | Default number of search results |
| `MAX_CONTENT_CHARS` | No | 50000 | Maximum content length before truncation |
| `ENABLE_EMBEDDING` | No | true | Enable text embedding |
| `EMBEDDING_PROVIDER` | No | openai | Embedding provider |
| `EMBEDDING_MODEL` | No | text-embedding-3-large | OpenAI embedding model |
| `EMBEDDING_DIMENSIONS` | No | 3072 | Embedding dimensions |
| `OPENAI_API_KEY` | No | - | OpenAI API key for embeddings |
| `METADATA_TEXT_KEYS` | No | text,chunk,content | Keys to probe for text content |
| `SECRET_TOKEN` | No | - | Bearer token for API authentication |

### Authentication

The server supports optional Bearer token authentication:

- **`SECRET_TOKEN`**: Set this environment variable to enable API authentication
- **Behavior**: 
  - If `SECRET_TOKEN` is not set, all endpoints are publicly accessible
  - If `SECRET_TOKEN` is set, protected endpoints require `Authorization: Bearer <token>` header
  - Public endpoints: `/health`, `/`, `/docs`, `/openapi.json`
  - Protected endpoints: `/tools`, `/tools/search`, `/tools/fetch`, `/call`, `/sse/`

**Example with authentication:**
```bash
curl -H "Authorization: Bearer your_secret_token" \
     -X POST http://localhost:8000/tools/search \
     -H "Content-Type: application/json" \
     -d '{"query": "machine learning", "top_k": 3}'
```

### Embedding Model Configuration

The server supports configurable OpenAI embedding models:

- **`EMBEDDING_MODEL`**: The OpenAI model to use (default: `text-embedding-3-large`)
- **`EMBEDDING_DIMENSIONS`**: The number of dimensions for the embedding (default: `3072`)

Supported models and their dimensions:
- `text-embedding-3-large`: 3072 dimensions (default)
- `text-embedding-3-small`: 1536 dimensions
- `text-embedding-ada-002`: 1536 dimensions

**Note**: Make sure your Pinecone index is configured with the same dimensions as your embedding model.

### Pinecone Index Requirements

Your Pinecone index should contain documents with:

- **ID**: Stable identifier (may be per-chunk)
- **Vector**: Embedding vector (stored server-side)
- **Metadata**: Including text content and document information:
  - `text`, `chunk`, or `content`: Main text content
  - `title`: Document title
  - `source`: Document source
  - `uri`: Document URI
  - `loc.lines.from`, `loc.lines.to`: Line numbers (optional)

## Development

### Project Structure

```
mcp_private_db/
├── __init__.py
├── main.py              # MCP server bootstrap & tool registration
├── tools.py             # search & fetch implementations
├── pinecone_client.py   # Pinecone client wrapper
├── embedder.py          # Embedding logic
├── schemas.py           # Pydantic models
├── config.py            # Environment variables loading
└── utils.py             # Helper functions

tests/
├── __init__.py
└── test_tools.py        # Unit tests

env.example              # Example environment variables
Makefile                 # Development commands
pyproject.toml           # Project configuration
README.md                # This file
```

### Available Commands

```bash
make install    # Install dependencies
make run        # Run the server
make test       # Run tests
make fmt        # Format code with black
make lint       # Lint code with ruff
make clean      # Clean up temporary files
make help       # Show available commands
```

### Testing

Tests use mocked Pinecone client to avoid requiring actual Pinecone credentials:

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_tools.py -v

# Run with coverage
pytest tests/ --cov=mcp_private_db
```

## Deployment

### Railway Deployment

1. Push this repository to GitHub
2. In Railway: New Project → Deploy from GitHub → select this repository
3. Add environment variables in Railway dashboard
4. Wait for build and deployment

The server will be available at the Railway-provided URL with `/health` endpoint for monitoring.

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "-m", "mcp_private_db.main"]
```

## Limitations

- **Read-only**: No document indexing or ingestion capabilities
- **No Web UI**: Command-line and API access only
- **Single Provider**: Currently supports OpenAI embeddings only
- **Basic Authentication**: Simple Bearer token authentication (no advanced auth features like OAuth, JWT, etc.)

## Error Handling

The server handles errors gracefully:

- **Empty queries**: Returns empty results instead of errors
- **Invalid IDs**: Filters out invalid IDs and continues
- **Pinecone errors**: Logs errors and returns empty results
- **Embedding failures**: Logs errors and returns empty results

All errors are logged at INFO level for monitoring and debugging.

## License

MIT License - see LICENSE file for details.
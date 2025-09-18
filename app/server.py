import os
import time
from fastmcp import FastMCP
from starlette.responses import PlainTextResponse
from starlette.requests import Request

mcp = FastMCP(
    name="fastmcp-minimal",
    instructions="A minimal FastMCP server exposing a single echo tool.",
)

@mcp.tool
def echo(message: str) -> dict:
    """Return the same message with a server-side timestamp."""
    return {"message": message, "timestamp": time.time()}

# tiny health check for Railway
@mcp.custom_route("/health", methods=["GET"])
async def health(_req: Request):
    return PlainTextResponse("OK")

def main():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    # HTTP transport so Railway can route traffic
    mcp.run(transport="http", host=host, port=port)

if __name__ == "__main__":
    main()

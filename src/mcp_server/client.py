from mcp_server.server import get_mcp_server
from fastmcp import Client

mcp_client = Client(get_mcp_server())


def get_mcp_client():
    global mcp_client
    return mcp_client

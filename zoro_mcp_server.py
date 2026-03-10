import asyncio
import json
from pathlib import Path
from typing import Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

# 1. Initialize FastMCP at the TOP (Global Level)
mcp = FastMCP("ZoroVault")
vault_path = Path("AI_Employee_Vault")

# --- TOOLS ---

@mcp.tool()
async def list_vault_structure(path: Optional[str] = None) -> str:
    """List the structure of the AI_Employee_Vault folder."""
    target_path = vault_path if path is None else vault_path / path
    if not target_path.exists():
        return f"Path does not exist: {target_path}"

    structure = {
        "path": str(target_path),
        "contents": []
    }
    if target_path.is_dir():
        for item in target_path.iterdir():
            structure["contents"].append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file"
            })
    return json.dumps(structure, indent=2)

@mcp.tool()
async def read_vault_file(file_path: str) -> str:
    """Read a specific file from the vault."""
    full_path = vault_path / file_path
    if not full_path.exists() or not full_path.is_file():
        return "File not found."
    
    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read(10000) # Read first 10k chars
    return content

@mcp.tool()
async def search_vault_files(query: str) -> str:
    """Search for content across all .md files in the vault."""
    results = []
    for file_path in vault_path.rglob("*.md"):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if query.lower() in content.lower():
                results.append(str(file_path.relative_to(vault_path)))
    return json.dumps({"query": query, "matches": results}, indent=2)

# --- ENTRY POINT ---

if __name__ == "__main__":
    # FastMCP automatically handles the server startup logic
    print("Zoro Vault MCP Server is starting...")
    mcp.run()
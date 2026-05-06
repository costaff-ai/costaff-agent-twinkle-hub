from core import mcp
import tools  # noqa: F401  (registers @mcp.tool() decorators on import)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")

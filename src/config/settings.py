from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega variáveis de ambiente de um arquivo .env na raiz do projeto, se existir
load_dotenv(os.path.join(BASE_DIR, ".env"))


@dataclass
class DatabaseSettings:
    user: str = os.getenv("POSTGRES_USER", "app_user")
    password: str = os.getenv("POSTGRES_PASSWORD", "app_password")
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    db: str = os.getenv("POSTGRES_DB", "book_reviews")

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


db_settings = DatabaseSettings()


@dataclass
class MCPSettings:
    """MCP client configuration (env). API expects MCP server already running when using streamable-http."""

    enabled: bool = os.getenv("MCP_ENABLED", "true").lower() in ("1", "true", "yes")
    transport: str = os.getenv("MCP_TRANSPORT", "streamable-http")
    # URL when transport is streamable-http (server must be running separately)
    server_url: str = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8001/mcp")
    fallback_to_local: bool = os.getenv("MCP_FALLBACK_TO_LOCAL", "true").lower() in ("1", "true", "yes")


mcp_settings = MCPSettings()


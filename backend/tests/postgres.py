"""一時の PostgreSQL の在りかを表す型。"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PostgresServer:
    """立てた一時の PostgreSQL の在りか。"""

    base_dir: Path
    data_dir: Path
    socket_dir: Path
    port: int
    user: str

    def conninfo(self, dbname: str = "postgres") -> str:
        """psycopg に渡す接続の文字列。"""
        return f"host={self.socket_dir} port={self.port} user={self.user} dbname={dbname}"

    def url(self, dbname: str = "postgres") -> str:
        """SQLAlchemy に渡す接続先(psycopg 3 の方言)。"""
        return f"postgresql+psycopg://{self.user}@/{dbname}?host={self.socket_dir}&port={self.port}"

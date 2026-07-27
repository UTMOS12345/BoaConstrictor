from __future__ import annotations

import pathlib
import tomllib
from dataclasses import dataclass, field
from urllib.parse import urlparse


CONFIG_PATH = pathlib.Path.home() / ".pg-explain.toml"


def _parse_conn_string(s: str) -> dict:
    if not s:
        return {}
    if s.startswith("postgresql://") or s.startswith("postgres://"):
        r = urlparse(s)
        result: dict = {}
        if r.hostname:
            result["host"] = r.hostname
        if r.port:
            result["port"] = r.port
        if r.username:
            result["user"] = r.username
        if r.password:
            result["password"] = r.password
        path = r.path.lstrip("/")
        if path:
            result["dbname"] = path
        return result
    parts = s.split()
    result = {}
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            result[k.lower()] = v
    return result


@dataclass
class DbConfig:
    host: str = "localhost"
    port: int = 5432
    dbname: str = ""
    user: str = ""
    password: str = ""

    @property
    def conn_string(self) -> str:
        parts = []
        if self.user:
            parts.append(f"user={self.user}")
        if self.password:
            parts.append(f"password={self.password}")
        if self.host:
            parts.append(f"host={self.host}")
        if self.port:
            parts.append(f"port={self.port}")
        if self.dbname:
            parts.append(f"dbname={self.dbname}")
        return " ".join(parts)

    def display_name(self) -> str:
        """Short human-readable label like 'localhost:5432/mydb'."""
        return f"{self.host}:{self.port}/{self.dbname or '(none)'}"

    @classmethod
    def from_conn_string(cls, s: str) -> "DbConfig":
        return cls(**{k: v for k, v in _parse_conn_string(s).items() if v})

    @classmethod
    def from_toml(cls, d: dict) -> "DbConfig":
        conn = d.get("connection", {})
        return cls(
            host=conn.get("host", "localhost"),
            port=conn.get("port", 5432),
            dbname=conn.get("dbname", ""),
            user=conn.get("user", ""),
            password=conn.get("password", ""),
        )


def load_config(path: pathlib.Path | None = None) -> DbConfig:
    path = path or CONFIG_PATH
    if not path.exists():
        return DbConfig()
    try:
        raw = path.read_bytes()
        data = tomllib.loads(raw.decode("utf-8"))
        return DbConfig.from_toml(data)
    except (tomllib.TOMLDecodeError, OSError):
        return DbConfig()


def merge_config(cli_db: str | None, file_config: DbConfig | None = None) -> DbConfig:
    base = file_config or DbConfig()
    if cli_db:
        return DbConfig.from_conn_string(cli_db)
    return base

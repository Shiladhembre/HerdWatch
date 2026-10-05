"""Read-only schema verification plus a transaction that is always rolled back."""
import json
import psycopg
from sqlalchemy.engine import make_url
from app.config import get_settings
from app.database import Base
import app.models  # noqa: F401


def main():
    url = make_url(get_settings().database_url)
    print("Checking PostgreSQL connectivity", flush=True)
    with psycopg.connect(host=url.host, port=url.port or 5432, user=url.username,
                          password=url.password, dbname=url.database, connect_timeout=5) as db:
        tables = {row[0] for row in db.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")}
        expected = set(Base.metadata.tables)
        result = {
            "database": url.database,
            "version": db.execute("SELECT version()").fetchone()[0],
            "postgis": db.execute("SELECT PostGIS_Version()").fetchone()[0],
            "migration": db.execute("SELECT version_num FROM alembic_version").fetchone()[0],
            "expected_tables": sorted(expected),
            "missing_tables": sorted(expected - tables),
        }
        db.execute("CREATE TEMP TABLE qa_rollback_probe (value integer)")
        db.execute("INSERT INTO qa_rollback_probe VALUES (1)")
        assert db.execute("SELECT value FROM qa_rollback_probe").fetchone()[0] == 1
        db.rollback()
        assert db.execute("SELECT to_regclass('qa_rollback_probe')").fetchone()[0] is None
        result["read_write_rollback"] = "PASS"
        print(json.dumps(result, indent=2))
        assert not result["missing_tables"], "Application tables are missing"


if __name__ == "__main__":
    main()

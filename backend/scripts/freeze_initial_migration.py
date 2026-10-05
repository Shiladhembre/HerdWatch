"""One-time migration authoring utility. Runtime migrations use the frozen SQL revision."""

from pathlib import Path
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql
from app.database import Base
import app.models  # noqa: F401


def main():
    destination = Path("alembic/versions/0001_initial.py")
    if destination.exists():
        raise SystemExit("Initial migration already exists; create a new revision instead.")
    statements = ["CREATE EXTENSION IF NOT EXISTS postgis"]
    for table in Base.metadata.sorted_tables:
        statements.append(str(CreateTable(table).compile(dialect=postgresql.dialect())))
        statements.extend(
            str(CreateIndex(index).compile(dialect=postgresql.dialect()))
            for index in sorted(table.indexes, key=lambda i: i.name)
        )
    code = '''"""Initial PostgreSQL/PostGIS schema. Frozen; independent of future ORM changes."""
from alembic import op
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
'''
    code += "\n".join("    op.execute(" + repr(stmt) + ")" for stmt in statements)
    code += "\n\ndef downgrade():\n"
    code += "\n".join("    op.drop_table(" + repr(t.name) + ")" for t in reversed(Base.metadata.sorted_tables)) + "\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(code, encoding="utf-8")
    print(f"Wrote frozen migration for {len(Base.metadata.tables)} tables.")


if __name__ == "__main__":
    main()

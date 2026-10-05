Run migrations from the backend directory with the virtual environment:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.server
```

The server entry point explicitly selects an asyncio selector loop on Windows.
The installed Uvicorn creates a Proactor loop by default, which psycopg async
connections do not support; changing the global event-loop policy alone does
not override Uvicorn's loop factory.

PostgreSQL/PostGIS must be running. The existing Docker Compose database can be
started with `docker compose up -d postgres`. Preserve its existing volume.

Supply the existing trained image artifact at
`models/cattle_image/cattle_disease_image_model.keras`, then restart the server.
No retraining is needed. The corresponding classes JSON is already present.
Health returns 503 until the database and both prediction models are ready.

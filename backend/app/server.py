"""Start with `python -m app.server`; psycopg requires a selector loop on Windows."""
import asyncio
import os
import sys

import uvicorn


def loop_factory():
    return asyncio.SelectorEventLoop() if sys.platform == "win32" else asyncio.new_event_loop()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=int(os.environ.get("PORT", "8000")),
                loop="app.server:loop_factory")

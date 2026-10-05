import asyncio
import sys

from app.server import loop_factory


def test_server_loop_supports_psycopg_on_windows():
    loop = loop_factory()
    try:
        if sys.platform == "win32":
            assert isinstance(loop, asyncio.SelectorEventLoop)
        assert not loop.is_closed()
    finally:
        loop.close()

import asyncio
from scripts.import_common import arguments, run_import

if __name__ == "__main__":
    asyncio.run(
        run_import(
            "historical_outbreak",
            arguments(
                "Import historical outbreak rows with explicit field mapping; keep post-event data outside prediction inputs."
            ),
        )
    )

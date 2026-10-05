import asyncio
from scripts.import_common import arguments, run_import

if __name__ == "__main__":
    asyncio.run(
        run_import(
            "historical_disease",
            arguments("Import historical disease statistics for context, not automatic ML training."),
        )
    )

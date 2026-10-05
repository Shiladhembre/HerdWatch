import asyncio
from scripts.import_common import arguments, run_import

if __name__ == "__main__":
    asyncio.run(run_import("census", arguments("Import verified village census columns with stable source IDs.")))

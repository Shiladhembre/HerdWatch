import argparse, hashlib, json
from pathlib import Path
import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from app.models import Location, HistoricalObservation
from app.database import SessionLocal
from app.utils.normalization import normalized, disease_name

POPULATIONS = [
    "cattle_population",
    "buffalo_population",
    "sheep_population",
    "goat_population",
    "pig_population",
    "poultry_population",
    "total_livestock",
]


def arguments(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("file", type=Path)
    parser.add_argument(
        "--mapping",
        type=Path,
        required=True,
        help="JSON mapping canonical field names to exact source columns. No guessed mappings.",
    )
    return parser.parse_args()


def batches(path):
    if path.suffix.lower() == ".csv":
        yield from pd.read_csv(path, dtype=str, chunksize=1000, keep_default_na=False)
    elif path.suffix.lower() in (".xls", ".xlsx"):
        frame = pd.read_excel(path, dtype=str, keep_default_na=False)
        for offset in range(0, len(frame), 1000):
            yield frame.iloc[offset : offset + 1000]
    else:
        raise ValueError("Use CSV, XLS or XLSX.")


def integer(value):
    if str(value).strip() == "":
        raise ValueError("Population data is missing; blank is not treated as zero.")
    numeric = float(str(value).replace(",", ""))
    if numeric < 0 or not numeric.is_integer():
        raise ValueError("Population must be a nonnegative whole number.")
    return int(numeric)


async def run_import(kind, args):
    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
    required = ["state", "district", "block", "village", "source_id", *POPULATIONS] if kind == "census" else ["disease"]
    if not set(required) <= set(mapping):
        raise ValueError(f"Mapping requires: {required}")
    total = 0
    for chunk in batches(args.file):
        missing = set(mapping.values()) - set(chunk.columns)
        if missing:
            raise ValueError(f"Missing source columns: {sorted(missing)}")
        records = []
        for _, row in chunk.iterrows():
            source = {str(k): str(v) for k, v in row.items()}
            canonical = {k: str(row[v]).strip() for k, v in mapping.items()}
            if kind == "census":
                if any(not canonical[k] for k in ["state", "district", "block", "village", "source_id"]):
                    raise ValueError(
                        "Blank location or official source ID; supply a stable source ID to avoid accidental village merges."
                    )
                record = {k: canonical[k] for k in ["state", "district", "block", "village"]}
                record.update(
                    {k + "_normalized": normalized(record[k]) for k in ["state", "district", "block", "village"]}
                )
                record.update({k: integer(canonical[k]) for k in POPULATIONS})
                record["source_key"] = hashlib.sha256(("census:" + canonical["source_id"]).encode()).hexdigest()
            else:
                if not canonical["disease"]:
                    raise ValueError("Blank disease label.")
                identity = json.dumps(source, sort_keys=True, ensure_ascii=False)
                record = {
                    "source_key": hashlib.sha256((kind + identity).encode()).hexdigest(),
                    "source": kind,
                    "disease": disease_name(canonical["disease"]),
                    "district": canonical.get("district", ""),
                    "raw_record": source,
                    "provenance": f"{args.file.name}; historical context only, not a model training contract",
                }
            records.append(record)
        # A duplicate row within the same file must not cause an upsert cardinality error.
        records = list({r["source_key"]: r for r in records}.values())
        model = Location if kind == "census" else HistoricalObservation
        async with SessionLocal.begin() as db:
            stmt = insert(model).values(records)
            if kind == "census":
                stmt = stmt.on_conflict_do_update(
                    index_elements=["source_key"],
                    set_={k: getattr(stmt.excluded, k) for k in records[0] if k != "source_key"},
                )
            else:
                stmt = stmt.on_conflict_do_nothing(index_elements=["source_key"])
            if records:
                await db.execute(stmt)
        total += len(records)
        print(f"Validated and processed {total} records.")

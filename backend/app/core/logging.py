import json
import logging

logger = logging.getLogger("herdwatch")
logging.basicConfig(level=logging.INFO, format="%(message)s")


def log_event(event, **fields):
    logger.info(json.dumps({"event": event, **fields}, default=str))

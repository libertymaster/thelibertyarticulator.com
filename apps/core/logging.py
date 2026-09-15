import json
import logging
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    def format(self, record):
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname, "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            result["exception"] = self.formatException(record.exc_info)
        return json.dumps(result, ensure_ascii=True)

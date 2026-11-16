"""Configuración del archivo de logs (único uso de archivos del sistema)."""
import logging
from pathlib import Path

RUTA_LOG = Path(__file__).resolve().parent / "logs" / "software_fj.log"


def configurar_logging() -> logging.Logger:
    """Crea (una sola vez) el logger 'software_fj' que escribe en logs/software_fj.log."""
    logger = logging.getLogger("software_fj")
    if logger.handlers:
        return logger
    RUTA_LOG.parent.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(RUTA_LOG, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger

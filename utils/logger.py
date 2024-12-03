from loguru import logger
import sys

def format_record(record):
    format_string = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>\n"
    return format_string

async def configure_logger():
    logger.remove()

    logger.add(
        sys.stdout,
        format=format_record,
        level="DEBUG",
        colorize=True,
        backtrace=True,
        diagnose=True
    )

    logger.add(
        "logs/log.log",
        format=format_record,
        level="DEBUG",
        rotation="10 MB",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
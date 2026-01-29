import requests 
import wikipediaapi
import logging 
import os 
from urllib.parse import unquote
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def running_in_prefect() -> bool:
    return any(
        key in os.environ
        for key in (
            "PREFECT_FLOW_RUN_ID",
            "PREFECT_API_URL",
            "PREFECT__API__URL",
        )
    )


def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers (important for reloads / MCP servers)
    root_logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s — %(levelname)s — %(name)s — %(message)s"
    )

    if running_in_prefect():
        # ✅ Horizon / Prefect → stdout
        handler = logging.StreamHandler()
    else:
        # ✅ Local dev → file
        log_dir = Path("../logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_dir / "server-log.log")

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


setup_logging()

logger = logging.getLogger(__name__)
def inspect(link: str):
    try:
        
        lang = link.split("://")[1].split(".")[0]
        page_title = link.split("/wiki/")[-1]
        
        # Decode URL characters like %20 into spaces/brackets
        page_title = unquote(page_title)

        wiki = wikipediaapi.Wikipedia(
            user_agent='RusMil-MCP',
            language='en',
            extract_format=wikipediaapi.ExtractFormat.WIKI
        )

        page = wiki.page(page_title)

        if page.exists():
            full_text = page.text    
            return full_text
        else:
            return "No valid link provided"

    except Exception as e:
        return str(e)

if __name__ == "__main__":
    i = inspect("https://en.wikipedia.org/wiki/Koltsovo_International_Airport")
    print(i)

# eof
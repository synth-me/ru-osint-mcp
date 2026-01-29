import requests 
import wikipediaapi
import logging 
import os 
from urllib.parse import unquote

logging.basicConfig(
    filename="../logs/server-log.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

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
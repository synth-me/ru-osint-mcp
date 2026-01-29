import os
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd 
import json 
from typing import Optional
from datetime import datetime, timedelta 
import requests
import re 
import logging 

os.chdir(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    filename="../logs/server-log.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

logger = logging.getLogger(__name__)

class POI_Explorer:
    """
    This object allows you to explore the "points of interest" database 
    with strict validation for user types and change categories.
    """
    
    VALID_USERS = ['CIV', 'MIL']
    VALID_CHANGES = [
        "Complete new location", 
        "Routine works", 
        "Construction new location area(s)"
    ]

    def __init__(self, db_path: str = "../sqlite-database/ru-poi.sqlite"):
        self.db_path = db_path
        self.tables = ["points_of_interest"]

    def _validate_user(self, user: Optional[str]):
        """Validate user parameter against CIV/MIL"""
        if user and user.upper() not in self.VALID_USERS:
            raise ValueError(f"Invalid user '{user}'. Must be one of: {', '.join(self.VALID_USERS)}")

    def _validate_change_type(self, type_of_change: Optional[str]):
        """Validate Type of Change against defined logistics categories"""
        if type_of_change and type_of_change not in self.VALID_CHANGES:
            raise ValueError(
                f"Invalid Type of Change. Must be exactly one of:\n"
                f"- {self.VALID_CHANGES[0]}\n"
                f"- {self.VALID_CHANGES[1]}\n"
                f"- {self.VALID_CHANGES[2]}"
            )

    def query_template(
        self,
        table_name: str,
        locations: Optional[str] = None,
        user: Optional[str] = None,
        type_of_locations: Optional[str] = None,
        type_of_change: Optional[str] = None,
        loc_id: Optional[str] = None,
        state: Optional[str] = None,
        limit: Optional[int] = None
    ) -> list:
        
        self._validate_user(user)
        self._validate_change_type(type_of_change)

        conn = sqlite3.connect(self.db_path)
        try:
            conditions = []
            params = []
            
            if user:
                conditions.append("UPPER(user) = ?")
                params.append(user.upper())

            if type_of_change:
                conditions.append("type_of_change = ?")
                params.append(type_of_change)

            filters = {
                'locations': locations,
                'type_of_locations': type_of_locations,
                'loc_id': loc_id,
                'state': state
            }

            for col, val in filters.items():
                if val:
                    conditions.append(f"{col} LIKE ?")
                    params.append(f"%{val}%")
            
            query = f"SELECT * FROM {table_name}"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            if limit:
                query += f" LIMIT {int(limit)}"
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error querying POI database: {e}")
            return []
        finally:
            conn.close()

    def query_points_of_interest(self, **kwargs):
        return self.query_template(table_name='points_of_interest', **kwargs)

    def get_statistics(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql_query("SELECT type_of_locations, COUNT(*) as count FROM points_of_interest GROUP BY type_of_locations", conn)
            return {"total": len(df), "breakdown": df.to_dict('records')}
        finally:
            conn.close()

class POI_downloader:

    def __init__(self):

        with open("../config/url.json","r",encoding="utf-8") as url_links_source:
            url_links_source_text = json.loads(url_links_source.read())
            url_links_source.close()

        self.url = url_links_source_text["POI"]
        self.source = ""
        self.tables = []  
        self.names = [
            "index_table",
            "points_of_interest"
        ]

    def download_source(self) -> bool:
        try:
            r = requests.get(self.url)
            self.source = r.text

            with open("../sources/POI.html","w",encoding="utf-8") as file:
                file.write(self.source)
                file.close()

            return True 
        except:
            return False      

    def find_table_sections(self):
        """
        Find table sections in HTML, even when malformed.
        Uses the opening <table> tags with border="3" as markers.
        
        Returns:
            list: List of tuples (start_pos, table_tag)
        """
        pattern = r'<table[^>]*border="3"[^>]*>'
        
        matches = []
        for match in re.finditer(pattern, self.source, re.IGNORECASE):
            start_pos = match.start()
            table_tag = match.group()
            matches.append((start_pos, table_tag))
        
        return matches

    def extract_table_until_next(self, start_pos, next_start_pos=None):
        """
        Extract table content from start position until the next table or end.
        Stops before any embedded title tables (border="0").
        
        Args:
            start_pos: Starting position of this table
            next_start_pos: Starting position of next table (or None for last table)
            
        Returns:
            str: Extracted table HTML
        """
        
        if next_start_pos is None:
            search_end = len(self.source)
        else:
            search_end = next_start_pos
        
        search_area = self.source[start_pos:search_end]
        
        title_table_pattern = r'(</td>|</tr>|</tbody>)<table[^>]*border="0"[^>]*>'
        
        title_match = re.search(title_table_pattern, search_area, re.IGNORECASE)
        
        if title_match:
            end_pos = start_pos + title_match.start() + len(title_match.group(1))
        else:
            if next_start_pos is None:
                end_pos = search_end
            else:
                last_td = search_area.rfind('</td>')
                if last_td > 0:
                    end_pos = start_pos + last_td + 5  
                else:
                    end_pos = next_start_pos
        
        table_html = self.source[start_pos:end_pos]
        
        table_html = table_html.rstrip()
        
        if not table_html.endswith('</table>'):
            if not table_html.endswith('</tbody>'):
                table_html += '\n  </tbody>'
            table_html += '\n</table>'
        
        return table_html

    def extract_tables(self):
        """
        Extract all data tables from the source HTML.
        
        Returns:
            list: List of table HTML strings
        """
        if not self.source:
            return []
        
        table_positions = self.find_table_sections()
        
        extracted_tables = []
        
        for idx, (start_pos, table_tag) in enumerate(table_positions):
            if idx < len(table_positions) - 1:
                next_start = table_positions[idx + 1][0]
            else:
                next_start = None
            
            table_html = self.extract_table_until_next(start_pos, next_start)
            extracted_tables.append(table_html)
        
        self.tables = extracted_tables
        return extracted_tables

    def save_tables_to_files(self, output_dir="../tables/POI", prefix="table"):
        """
        Save each extracted table as a separate HTML file.
        
        Args:
            output_dir: Directory to save the tables
            prefix: Prefix for output filenames
            
        Returns:
            list: List of output filenames
        """
        
        output_files = []
        
        for idx, table_html in enumerate(self.tables, 1):
            html_doc = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Table {idx}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        table {{
            border-collapse: collapse;
        }}
        td, th {{
            padding: 8px;
        }}
    </style>
</head>
<body>
{table_html}
</body>
</html>"""
            
            output_filename = os.path.join(output_dir, f"{self.names[idx]}.html")
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(html_doc)
            
            output_files.append(output_filename)
        
        return output_files

    def get_table(self, index):
        """
        Get a specific table by index (1-based).
        
        Args:
            index: Table index (1 for first table, 2 for second, etc.)
            
        Returns:
            str: Table HTML or None if index is out of range
        """
        if 0 < index <= len(self.tables):
            return self.tables[index - 1]
        return None

    def get_table_count(self):
        """
        Get the number of extracted tables.
        
        Returns:
            int: Number of tables
        """
        return len(self.tables)

class POI_Parser:
    
    def __init__(self):
        self.headers = [
            "locations", "user", "type_of_locations", "type_of_change",
            "loc_id", "start", "image_s", "state", "image_c", "street", "kml"
        ]
        self.files = ["points_of_interest"]
        self.contents = {name: self.get_source(name) for name in self.files}

    def get_source(self, file: str) -> str:

        with open(f"../tables/POI/{file}.html","r",encoding="utf-8") as file:
            content = file.read()
            file.close()

        return content

    def extract_link_from_td(self, td):
        anchor = td.find('a')
        return anchor.get('href') if anchor and anchor.get('href') else None

    def format_json(self, cells: list) -> dict:
        """
        Maps HTML cells to unique dictionary keys.
        The HTML has 'Image' at index 6 and index 8.
        """
        return {
            'locations': cells[0].get_text(strip=True),
            'user': cells[1].get_text(strip=True),
            'type_of_locations': cells[2].get_text(strip=True),
            'type_of_change': cells[3].get_text(strip=True),
            'loc_id': cells[4].get_text(strip=True),
            'start': cells[5].get_text(strip=True),
            
            'image_s': self.extract_link_from_td(cells[6]), 
            'state': cells[7].get_text(strip=True),
            'image_c': self.extract_link_from_td(cells[8]),
            
            'street_link': self.extract_link_from_td(cells[9]),
            'kml': self.extract_link_from_td(cells[14]) 
        }

    def parse_table(self, table_name: str) -> list:
        container = []
        soup = BeautifulSoup(self.contents[table_name], 'html.parser')
        rows = soup.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 15:
                if "Locations" in cells[0].get_text():
                    continue
                container.append(self.format_json(cells))
        return container

    def push_to_database(self):
        data = self.parse_table("points_of_interest")
        if not data:
            return

        db_path = f"../sqlite-database/ru-poi.sqlite"
        conn = sqlite3.connect(db_path)
        try:
            df = pd.DataFrame(data)
            df.to_sql('points_of_interest', conn, if_exists='replace', index=False)
            conn.commit()
            logger.info("POI Database updated with unique Image columns.")
        finally:
            conn.close() 
    
    def check_login_and_update(self):
        file_path = "../logs/last-update.txt"
        current_time = datetime.now()
        
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                stored_time_str = f.read().strip()
                
            try:
                last_login = datetime.strptime(stored_time_str, "%Y-%m-%d %H:%M:%S")
                
                delta = current_time - last_login
                
                if delta > timedelta(hours=24):
                    d = POI_downloader()
                    d.download_source()
                    d.extract_tables()
                    d.save_tables_to_files()
                    logger.info("Updating database...")
                    self.push_to_database()
                    logger.info("Finished updating database !")
                    
            except ValueError:
                logger.info("Stored format was invalid. Updating timestamp.")
                self.push_to_database()
        else:
            logger.info("First login detected. Creating storage file.")
            self.push_to_database()

        with open(file_path, "w") as f:
            f.write(current_time.strftime("%Y-%m-%d %H:%M:%S"))

    def run(self):

        self.check_login_and_update()

        return 

# eof
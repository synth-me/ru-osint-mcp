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


class GF_Explorer:
    """
        This object allows you to explore the "ground forces" database 
    """
    
    VALID_COUNTRIES = ['RUS', 'BLR',"UKR","GEO","MDA","ARM"]
    VALID_SERVICES = ['A', 'N', 'UI', 'NF', None]  # Adjust based on actual ground forces services
    
    def __init__(self, db_path: str = "../sqlite-database/ru-ground-forces.sqlite"):
        self.db_path = db_path

        self.tables = [
            "barracks_tanks_forces",
            "barracks_motorized_rifle_forces",
            "barracks_artillery_forces",
            "barracks_airborne_forces",
            "barracks_headquarters_forces",
            "other_barracks",
            "other_military_bases",
            "other_facilities",
            "special_facilities"   
        ]
        
        self.headers = [
            "Country",
            "Location",
            "Oblast",
            "Service",
            "Main User",
            "State",
            "Image",
            "Topo",            
            "Street",
            "Rail",
            "KML",
            "POI"
        ]

    def _validate_country(self, country: Optional[str]) -> bool:
        """Validate country parameter"""
        if country is None:
            return True
        if country.upper() not in self.VALID_COUNTRIES:
            raise ValueError(f"Invalid country '{country}'. Must be one of: {', '.join(self.VALID_COUNTRIES)}")
        return True

    def _validate_service(self, service: Optional[str]) -> bool:
        """Validate service parameter"""
        if service is None:
            return True
        if service.upper() not in [s for s in self.VALID_SERVICES if s is not None]:
            raise ValueError(f"Invalid service '{service}'. Must be one of: A, N, UI, NF, or None")
        return True

    def query_template(
        self,
        table_name: str ,
        country: Optional[str] = None,
        location: Optional[str] = None,
        oblast: Optional[str] = None,
        service: Optional[str] = None,
        main_user: Optional[str] = None,
        state: Optional[str] = None,
        image: Optional[str] = None,
        topo: Optional[str] = None,
        street: Optional[str] = None,
        rail: Optional[str] = None,
        kml: Optional[str] = None,
        poi: Optional[str] = None,
        limit: Optional[int] = None
    ) -> list:
        """
        Generic query template for searching the database.
        All parameters are optional - if None, they won't be used as filters.
        
        Args:
            country: Must be 'RUS' or 'BLR'
            service: Must be 'A', 'N', 'UI', 'NF', or None
            Other parameters use LIKE for partial matching (case-insensitive).
        
        Returns:
            List with rows found in the specified table 
        """
        
        # Validate inputs
        self._validate_country(country)
        self._validate_service(service)
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Build the WHERE clause dynamically
            conditions = []
            params = []
            
            # Country uses exact match (case-insensitive)
            if country is not None:
                conditions.append("UPPER(country) = ?")
                params.append(country.upper())
            
            if location is not None:
                conditions.append("location LIKE ?")
                params.append(f"%{location}%")
            
            if oblast is not None:
                conditions.append("oblast LIKE ?")
                params.append(f"%{oblast}%")
            
            # Service uses exact match (case-insensitive) or NULL check
            if service is not None:
                conditions.append("UPPER(service) = ?")
                params.append(service.upper())
            
            if main_user is not None:
                conditions.append("main_user LIKE ?")
                params.append(f"%{main_user}%")
            
            if state is not None:
                conditions.append("state LIKE ?")
                params.append(f"%{state}%")
            
            if image is not None:
                conditions.append("image LIKE ?")
                params.append(f"%{image}%")
            
            if topo is not None:
                conditions.append("topo LIKE ?")
                params.append(f"%{topo}%")
            
            if street is not None:
                conditions.append("street LIKE ?")
                params.append(f"%{street}%")
            
            if rail is not None:
                conditions.append("rail LIKE ?")
                params.append(f"%{rail}%")
            
            if kml is not None:
                conditions.append("kml LIKE ?")
                params.append(f"%{kml}%")
            
            if poi is not None:
                conditions.append("poi LIKE ?")
                params.append(f"%{poi}%")
            
            # Build the SQL query
            query = f"SELECT * FROM {table_name}"
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            if limit is not None:
                query += f" LIMIT {limit}"
            
            # Execute query
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            logging.info("Query: "+query)
            logging.info("Params: "+",".join(params))

            # Fetch all rows
            rows = cursor.fetchall()
            
            # Convert to dictionary format
            result = [dict(zip(columns, row)) for row in rows]
            
            return result
            
        except Exception as e:
            logger.info(f"Error querying database: {e}")
            return []
            
        finally:
            conn.close()
    
    def query_barracks_tanks_forces(self, **kwargs) -> dict:
        """Query barracks tanks forces table"""
        return self.query_template(table_name='barracks_tanks_forces', **kwargs)
    
    def query_barracks_motorized_rifle_forces(self, **kwargs) -> dict:
        """Query barracks motorized rifle forces table"""
        return self.query_template(table_name='barracks_motorized_rifle_forces', **kwargs)
    
    def query_barracks_artillery_forces(self, **kwargs) -> dict:
        """Query barracks artillery forces table"""
        return self.query_template(table_name='barracks_artillery_forces', **kwargs)
    
    def query_barracks_airborne_forces(self, **kwargs) -> dict:
        """Query barracks airborne forces table"""
        return self.query_template(table_name='barracks_airborne_forces', **kwargs)
    
    def query_barracks_headquarters_forces(self, **kwargs) -> dict:
        """Query barracks headquarters forces table"""
        return self.query_template(table_name='barracks_headquarters_forces', **kwargs)
    
    def query_other_barracks(self, **kwargs) -> dict:
        """Query other barracks table"""
        return self.query_template(table_name='other_barracks', **kwargs)
    
    def query_other_military_bases(self, **kwargs) -> dict:
        """Query other military bases table"""
        return self.query_template(table_name='other_military_bases', **kwargs)
    
    def query_other_facilities(self, **kwargs) -> dict:
        """Query other facilities table"""
        return self.query_template(table_name='other_facilities', **kwargs)
    
    def query_special_facilities(self, **kwargs) -> dict:
        """Query special facilities table"""
        return self.query_template(table_name='special_facilities', **kwargs)
    
    def get_all_records(self, table_name: str) -> dict:
        """Get all records from a specific table"""
        return self.query_template(table_name=table_name)
    
    def search_all_tables(self, **kwargs) -> dict:
        """Search across all tables with the same criteria"""
        results = {}
        for table_name in self.tables:
            d = self.query_template(table_name=table_name, **kwargs)
            results[table_name] = d
        return results
    
    def get_statistics(self) -> dict:
        """Get statistics for all tables in the database"""
        conn = sqlite3.connect(self.db_path)
        stats = {}
        
        try:
            cursor = conn.cursor()
            
            for table_name in self.tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    stats[table_name] = count
                except Exception as e:
                    logger.info(f"Error getting stats for {table_name}: {e}")
                    stats[table_name] = 0
            
            return stats
            
        finally:
            conn.close()

class GF_downloader:

    def __init__(self):

        with open("../config/url.json","r",encoding="utf-8") as url_links_source:
            url_links_source_text = json.loads(url_links_source.read())
            url_links_source.close()

        self.url = url_links_source_text["GF"]
        self.source = ""
        self.tables = []  
        
        self.names = [
            "teste0", # ignored 
            "index_table",
            "barracks_tanks_forces",
            "barracks_motorized_rifle_forces",
            "barracks_artillery_forces",
            "barracks_airborne_forces",
            "barracks_headquarters_forces",
            "other_barracks",
            "other_military_bases",
            "other_facilities",
            "special_facilities"
        ]


    def download_source(self) -> bool:
        try:
            r = requests.get(self.url)
            self.source = r.text

            with open("../sources/GF.html","w",encoding="utf-8") as file:
                file.write(self.source)
                file.close()

            return True 
        except Exception as e :
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
                # This is the last table
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
        
        # Find all data tables (border="3")
        table_positions = self.find_table_sections()
        
        extracted_tables = []
        
        for idx, (start_pos, table_tag) in enumerate(table_positions):
            # Determine where this table ends (before next table starts)
            if idx < len(table_positions) - 1:
                next_start = table_positions[idx + 1][0]
            else:
                next_start = None
            
            # Extract the table
            table_html = self.extract_table_until_next(start_pos, next_start)
            extracted_tables.append(table_html)
        
        self.tables = extracted_tables
        return extracted_tables

    def save_tables_to_files(self, output_dir="../tables/GF", prefix="table"):
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
            # Create complete HTML document
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
            
            # Save to file
            output_filename = os.path.join(output_dir, f"{self.names[idx]}.html")
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(html_doc)
                f.close()
            
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

class GF_Parser:

    """
        This object defines the parser for the ground forces data 
        with all the following tables:

            Barracks of tank forces
            Barracks of motorized rifle forces
            Barracks of artillery forces
            Barracks of airborne forces
            Barracks of headquarters forces
            Other barracks of the ground forces
            Other military base of the ground forces
            Other facilities of the ground forces
            Other facilities of the ground forces

    """

    def __init__(self):

        self.headers = [
            "Country",
            "Location",
            "Oblast",
            "Service",
            "Main User",
            "State",
            "Image",
            "Topo",            
            "Street",
            "Rail",
            "KML",
            "POI"
        ]

        self.columns = ['_'.join(header.split()).lower() for header in self.headers]

        self.files = [
            "barracks_tanks_forces",
            "barracks_motorized_rifle_forces",
            "barracks_artillery_forces",
            "barracks_airborne_forces",
            "barracks_headquarters_forces",
            "other_barracks",
            "other_military_bases",
            "other_facilities",
            "special_facilities"   
        ]
        self.contents = {}

        self.contents = {name:self.get_source(name) for name in self.files}

    def get_source(self, file: str) -> str:

        with open(f"../tables/GF/{file}.html","r",encoding="utf-8") as file:
            content = file.read()
            file.close()

        return content

    def extract_link_from_td(self, td):
        anchor = td.find('a')
        if anchor and anchor.get('href'):
            return anchor.get('href')
        return None

    def format_json(self, cells: list) -> dict:
         return {
            'country': cells[0].get_text(strip=True),
            'location': cells[1].get_text(strip=True),
            'oblast': cells[2].get_text(strip=True),
            'service': cells[3].get_text(strip=True),
            'main_user': cells[4].get_text(strip=True),
            'state': cells[5].get_text(strip=True),
            
            # Link extractions
            'image': self.extract_link_from_td(cells[6]),
            'topo': self.extract_link_from_td(cells[7]),
            'street': self.extract_link_from_td(cells[8]),
            'rail': self.extract_link_from_td(cells[9]),
            'kml': self.extract_link_from_td(cells[10]),
            'poi': self.extract_link_from_td(cells[11])
        }

    def parse_table(self, table_name:str) -> list:

        container = []

        soup = BeautifulSoup(self.contents[table_name], 'html.parser')
        
        rows = soup.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            
            row_data = self.format_json(cells)
            
            container.append(row_data)
        
        return container

    def parse_barracks_tank_forces(self) -> list:
        table = self.parse_table("barracks_tanks_forces")
        return table 

    def parse_barracks_motorized_rifle_forces(self) -> list:
        table = self.parse_table("barracks_motorized_rifle_forces")
        return table 
    
    def parse_barracks_artillery_forces(self) -> list:
        table = self.parse_table("barracks_artillery_forces")
        return table

    def parse_barracks_airborne_forces(self) -> list:
        table = self.parse_table("barracks_airborne_forces")
        return table
    
    def parse_barracks_headquarters_forces(self) -> list:
        table = self.parse_table("barracks_headquarters_forces")
        return table
        
    def parse_other_barracks(self) -> list:
        table = self.parse_table("other_barracks")
        return table
    
    def parse_other_military_bases(self) -> list:
        table = self.parse_table("other_military_bases")
        return table
    
    def parse_other_facilities(self) -> list:
        table = self.parse_table("other_facilities")
        return table

    def parse_special_facilities(self) -> list:
        table = self.parse_table("special_facilities")
        return table

    def push_to_database(self):

        barracks_tanks = self.parse_barracks_tank_forces()
        barracks_motorized = self.parse_barracks_motorized_rifle_forces()
        barracks_artillery = self.parse_barracks_artillery_forces()
        barracks_airborne = self.parse_barracks_airborne_forces()
        barracks_headquarters = self.parse_barracks_headquarters_forces()
        other_barracks = self.parse_other_barracks()
        other_military_bases = self.parse_other_military_bases()
        other_facilities = self.parse_other_facilities()
        special_facilities = self.parse_special_facilities()
        
        db_path = "../sqlite-database/ru-ground-forces.sqlite"
        conn = sqlite3.connect(db_path)
        
        try:
            if barracks_tanks:
                df_tanks = pd.DataFrame(barracks_tanks[1:] if len(barracks_tanks) > 1 else barracks_tanks)
                df_tanks.to_sql('barracks_tank_forces', conn, if_exists='replace', index=False)
            
            if barracks_motorized:
                df_motorized = pd.DataFrame(barracks_motorized[1:] if len(barracks_motorized) > 1 else barracks_motorized)
                df_motorized.to_sql('barracks_motorized_rifle_forces', conn, if_exists='replace', index=False)
            
            if barracks_artillery:
                df_artillery = pd.DataFrame(barracks_artillery[1:] if len(barracks_artillery) > 1 else barracks_artillery)
                df_artillery.to_sql('barracks_artillery_forces', conn, if_exists='replace', index=False)
            
            if barracks_airborne:
                df_airborne = pd.DataFrame(barracks_airborne[1:] if len(barracks_airborne) > 1 else barracks_airborne)
                df_airborne.to_sql('barracks_airborne_forces', conn, if_exists='replace', index=False)
            
            if barracks_headquarters:
                df_headquarters = pd.DataFrame(barracks_headquarters[1:] if len(barracks_headquarters) > 1 else barracks_headquarters)
                df_headquarters.to_sql('barracks_headquarters_forces', conn, if_exists='replace', index=False)
            
            if other_barracks:
                df_other_barracks = pd.DataFrame(other_barracks[1:] if len(other_barracks) > 1 else other_barracks)
                df_other_barracks.to_sql('other_barracks', conn, if_exists='replace', index=False)
            
            if other_military_bases:
                df_other_bases = pd.DataFrame(other_military_bases[1:] if len(other_military_bases) > 1 else other_military_bases)
                df_other_bases.to_sql('other_military_bases', conn, if_exists='replace', index=False)
            
            if other_facilities:
                df_other_facilities = pd.DataFrame(other_facilities[1:] if len(other_facilities) > 1 else other_facilities)
                df_other_facilities.to_sql('other_facilities', conn, if_exists='replace', index=False)
            
            if special_facilities:
                df_special = pd.DataFrame(special_facilities[1:] if len(special_facilities) > 1 else special_facilities)
                df_special.to_sql('special_facilities', conn, if_exists='replace', index=False)
            
            conn.commit()
            logger.info("Database updated successfully!")
            
        except Exception as e:
            logger.info(f"Error updating database: {e}")
            conn.rollback()
            
        finally:
            conn.close()
        
        return

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
                    d = GF_downloader()
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
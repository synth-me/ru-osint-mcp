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
import sys 

os.chdir(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s — %(levelname)s — %(name)s — %(message)s",
)

logger = logging.getLogger(__name__)

class Depot_Explorer:
    """
    This object allows you to explore the "ru-depots" database 
    containing central and regional logistics facilities.
    """
    
    VALID_COUNTRIES = ['RUS', 'BLR', "UKR", "GEO", "MDA", "ARM"]
    VALID_SERVICES = ['A', 'N', 'UI', 'NF', None]  
    
    def __init__(self, db_path: str = "../sqlite-database/ru-depots.sqlite"):
        self.db_path = db_path

        self.tables = [
            "index_table",
            "central_nuclear_arsenals",
            "central_ammunition_depots",
            "central_pol_depots",
            "central_sam_depots",
            "central_weapon_depots",
            "central_artillery_depots",
            "central_vehicle_depots",
            "central_unknown_depots",
            "central_aircraft_repair",
            "regional_nuclear_support",
            "regional_ammunition",
            "regional_pol",
            "regional_supply",
            "regional_transport",
            "regional_open_air"
        ]
        
        self.headers = [
            "Country", "Locations", "Oblast", "Service",
            "Specifications", "State", "Image", "Topo",            
            "Street", "Rail", "KML", "POI"
        ]

    def _validate_country(self, country: Optional[str]) -> bool:
        if country and country.upper() not in self.VALID_COUNTRIES:
            raise ValueError(f"Invalid country '{country}'. Must be: {', '.join(self.VALID_COUNTRIES)}")
        return True

    def _validate_service(self, service: Optional[str]) -> bool:
        if service and service.upper() not in [s for s in self.VALID_SERVICES if s is not None]:
            raise ValueError(f"Invalid service '{service}'. Must be: A, N, UI, NF")
        return True

    def query_template(self, table_name: str, **kwargs) -> list:
        """Base query engine for all depot tables."""
        country = kwargs.get('country')
        service = kwargs.get('service')
        limit = kwargs.get('limit')
        
        self._validate_country(country)
        self._validate_service(service)
        
        conn = sqlite3.connect(self.db_path)
        try:
            conditions = []
            params = []
            
            # Direct filters (Exact)
            if country:
                conditions.append("UPPER(country) = ?")
                params.append(country.upper())
            if service:
                conditions.append("UPPER(service) = ?")
                params.append(service.upper())
            
            # String filters (Partial match)
            for field in ['locations', 'oblast', 'specifications', 'state', 'image', 'topo', 'street', 'rail', 'kml', 'poi']:
                val = kwargs.get(field)
                if val:
                    conditions.append(f"{field} LIKE ?")
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
            logger.error(f"Error in {table_name}: {e}")
            return []
        finally:
            conn.close()

    # --- Central Facilities Queries ---
    def query_index_table(self, **kwargs): 
        return self.query_template("index_table", **kwargs)
    
    def query_central_nuclear_arsenals(self, **kwargs): 
        return self.query_template("central_nuclear_arsenals", **kwargs)
    
    def query_central_ammunition_depots(self, **kwargs): 
        return self.query_template("central_ammunition_depots", **kwargs)
    
    def query_central_pol_depots(self, **kwargs): 
        return self.query_template("central_pol_depots", **kwargs)
    
    def query_central_sam_depots(self, **kwargs): 
        return self.query_template("central_sam_depots", **kwargs)

    def query_central_weapon_depots(self, **kwargs): 
        return self.query_template("central_weapon_depots", **kwargs)

    def query_central_artillery_depots(self, **kwargs): 
        return self.query_template("central_artillery_depots", **kwargs)

    def query_central_vehicle_depots(self, **kwargs): 
        return self.query_template("central_vehicle_depots", **kwargs)
    
    def query_central_unknown_depots(self, **kwargs): 
        return self.query_template("central_unknown_depots", **kwargs)
    
    def query_central_aircraft_repair(self, **kwargs): 
        return self.query_template("central_aircraft_repair", **kwargs)

    def query_regional_nuclear_support(self, **kwargs): 
        return self.query_template("regional_nuclear_support", **kwargs)

    def query_regional_ammunition(self, **kwargs): 
        return self.query_template("regional_ammunition", **kwargs)

    def query_regional_pol(self, **kwargs): 
        return self.query_template("regional_pol", **kwargs)

    def query_regional_supply(self, **kwargs): 
        return self.query_template("regional_supply", **kwargs)

    def query_regional_transport(self, **kwargs): 
        return self.query_template("regional_transport", **kwargs)
    
    def query_regional_open_air(self, **kwargs): 
        return self.query_template("regional_open_air", **kwargs)

    def get_statistics(self) -> dict:
        """Returns row counts for all depot tables."""
        stats = {}
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            for table in self.tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            return stats
        finally:
            conn.close()

class Depot_downloader:

    def __init__(self):

        with open("../config/url.json","r",encoding="utf-8") as url_links_source:
            url_links_source_text = json.loads(url_links_source.read())
            url_links_source.close()

        self.url = url_links_source_text["LOG"]
        self.source = ""
        self.tables = []  
        
        self.names = [
            "teste0", # ignored 
            "index_table",
            "central_nuclear_arsenals",
            "central_ammunition_depots",
            "central_pol_depots",
            "central_surface_to_air_missile_depots",
            "central_weapon_depots",
            "central_artillery_depots",
            "central_vehicle_depots",
            "central_depots_unknown_function",
            "central_aircraft_repair_plants",
            "regional_nuclear_support_base",
            "regional_ammunition_depots",
            "regional_pol_depots",
            "regional_supply_depots",
            "regional_transport_bases",
            "regional_open_air_depots"
        ]


    def download_source(self) -> bool:
        try:
            r = requests.get(self.url)
            self.source = r.text

            print(self.source)

            with open("../sources/Depot.html","w",encoding="utf-8") as file:
                file.write(self.source)
                file.close()

            return True 
        except Exception as e :

            print(e)

            return False
        
    def find_table_sections(self):
        """
        Find table sections in HTML, even when malformed.
        Uses the opening <table> tags with border="3" as markers.
        
        Returns:
            list: List of tuples (start_pos, table_tag)
        """
        # Find all table opening tags with border="3"
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
            
            # Extract the table
            table_html = self.extract_table_until_next(start_pos, next_start)
            extracted_tables.append(table_html)
        
        self.tables = extracted_tables
        print(self.tables)
        return extracted_tables

    def save_tables_to_files(self, output_dir="../tables/LOG", prefix="table"):
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

class Depot_Parser:
    """
        This object defines the parser for the logistics and depot data 
        with all specialized logistics tables.
    """

    def __init__(self):
        self.headers = [
            "Country", "Locations", "Oblast", "Service",
            "Specifications", "State", "Image", "Topo",            
            "Street", "Rail", "KML", "POI"
        ]

        self.columns = ['_'.join(header.split()).lower() for header in self.headers]

        self.files = [
            "central_nuclear_arsenals",
            "central_ammunition_depots",
            "central_pol_depots",
            "central_surface_to_air_missile_depots",
            "central_weapon_depots",
            "central_artillery_depots",
            "central_vehicle_depots",
            "central_depots_unknown_function",
            "central_aircraft_repair_plants",
            "regional_nuclear_support_base",
            "regional_ammunition_depots",
            "regional_pol_depots",
            "regional_supply_depots",
            "regional_transport_bases",
            "regional_open_air_depots"
        ]
        
        self.contents = {name: self.get_source(name) for name in self.files}

    def get_source(self, file: str) -> str:
        with open(f"../tables/LOG/{file}.html", "r", encoding="utf-8") as f:
            content = f.read()
        return content

    def extract_link_from_td(self, td):
        anchor = td.find('a')
        if anchor and anchor.get('href'):
            return anchor.get('href')
        return None

    def format_json(self, cells: list) -> dict:
        return {
            'country': cells[0].get_text(strip=True),
            'locations': cells[1].get_text(strip=True),
            'oblast': cells[2].get_text(strip=True),
            'service': cells[3].get_text(strip=True),
            'specifications': cells[4].get_text(strip=True),
            'state': cells[5].get_text(strip=True),
            
            # Link extractions
            'image': self.extract_link_from_td(cells[6]),
            'topo': self.extract_link_from_td(cells[7]),
            'street': self.extract_link_from_td(cells[8]),
            'rail': self.extract_link_from_td(cells[9]),
            'kml': self.extract_link_from_td(cells[10]),
            'poi': self.extract_link_from_td(cells[11])
        }

    def parse_table(self, table_name: str) -> list:
        container = []
        soup = BeautifulSoup(self.contents[table_name], 'html.parser')
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if cells:
                row_data = self.format_json(cells)
                container.append(row_data)
        return container

    def parse_index_table(self): 
        return self.parse_table("index_table")

    def parse_central_nuclear_arsenals(self): 
        return self.parse_table("central_nuclear_arsenals")
    
    def parse_central_ammunition_depots(self): 
        return self.parse_table("central_ammunition_depots")
    
    def parse_central_pol_depots(self): 
        return self.parse_table("central_pol_depots")
    
    def parse_central_sam_depots(self): 
        return self.parse_table("central_surface_to_air_missile_depots")
    
    def parse_central_weapon_depots(self): 
        return self.parse_table("central_weapon_depots")
    
    def parse_central_artillery_depots(self): 
        return self.parse_table("central_artillery_depots")
    
    def parse_central_vehicle_depots(self): 
        return self.parse_table("central_vehicle_depots")
    
    def parse_central_unknown_depots(self): 
        return self.parse_table("central_depots_unknown_function")
    
    def parse_central_aircraft_repair(self): 
        return self.parse_table("central_aircraft_repair_plants")
    
    def parse_regional_nuclear_support(self): 
        return self.parse_table("regional_nuclear_support_base")
    
    def parse_regional_ammunition(self): 
        return self.parse_table("regional_ammunition_depots")
    
    def parse_regional_pol(self): 
        return self.parse_table("regional_pol_depots")
    
    def parse_regional_supply(self): 
        return self.parse_table("regional_supply_depots")
    
    def parse_regional_transport(self): 
        return self.parse_table("regional_transport_bases")
    
    def parse_regional_open_air(self): 
        return self.parse_table("regional_open_air_depots")

    def push_to_database(self):
        central_nuclear = self.parse_central_nuclear_arsenals()
        central_ammunition = self.parse_central_ammunition_depots()
        central_pol = self.parse_central_pol_depots()
        central_sam = self.parse_central_sam_depots()
        central_weapon = self.parse_central_weapon_depots()
        central_artillery = self.parse_central_artillery_depots()
        central_vehicle = self.parse_central_vehicle_depots()
        central_unknown = self.parse_central_unknown_depots()
        central_aircraft = self.parse_central_aircraft_repair()
        regional_nuclear = self.parse_regional_nuclear_support()
        regional_ammunition = self.parse_regional_ammunition()
        regional_pol = self.parse_regional_pol()
        regional_supply = self.parse_regional_supply()
        regional_transport = self.parse_regional_transport()
        regional_open_air = self.parse_regional_open_air()
        
        db_path = "../sqlite-database/ru-depots.sqlite"
        conn = sqlite3.connect(db_path)
        
        try:
            if central_nuclear:
                df_nuclear = pd.DataFrame(central_nuclear[1:] if len(central_nuclear) > 1 else central_nuclear)
                df_nuclear.to_sql('central_nuclear_arsenals', conn, if_exists='replace', index=False)
            
            if central_ammunition:
                df_ammo = pd.DataFrame(central_ammunition[1:] if len(central_ammunition) > 1 else central_ammunition)
                df_ammo.to_sql('central_ammunition_depots', conn, if_exists='replace', index=False)
            
            if central_pol:
                df_pol = pd.DataFrame(central_pol[1:] if len(central_pol) > 1 else central_pol)
                df_pol.to_sql('central_pol_depots', conn, if_exists='replace', index=False)
            
            if central_sam:
                df_sam = pd.DataFrame(central_sam[1:] if len(central_sam) > 1 else central_sam)
                df_sam.to_sql('central_sam_depots', conn, if_exists='replace', index=False)
            
            if central_weapon:
                df_weapon = pd.DataFrame(central_weapon[1:] if len(central_weapon) > 1 else central_weapon)
                df_weapon.to_sql('central_weapon_depots', conn, if_exists='replace', index=False)
            
            if central_artillery:
                df_cartillery = pd.DataFrame(central_artillery[1:] if len(central_artillery) > 1 else central_artillery)
                df_cartillery.to_sql('central_artillery_depots', conn, if_exists='replace', index=False)
            
            if central_vehicle:
                df_vehicle = pd.DataFrame(central_vehicle[1:] if len(central_vehicle) > 1 else central_vehicle)
                df_vehicle.to_sql('central_vehicle_depots', conn, if_exists='replace', index=False)
            
            if central_unknown:
                df_unknown = pd.DataFrame(central_unknown[1:] if len(central_unknown) > 1 else central_unknown)
                df_unknown.to_sql('central_unknown_depots', conn, if_exists='replace', index=False)
            
            if central_aircraft:
                df_aircraft = pd.DataFrame(central_aircraft[1:] if len(central_aircraft) > 1 else central_aircraft)
                df_aircraft.to_sql('central_aircraft_repair', conn, if_exists='replace', index=False)
            
            if regional_nuclear:
                df_r_nuclear = pd.DataFrame(regional_nuclear[1:] if len(regional_nuclear) > 1 else regional_nuclear)
                df_r_nuclear.to_sql('regional_nuclear_support', conn, if_exists='replace', index=False)
            
            if regional_ammunition:
                df_r_ammo = pd.DataFrame(regional_ammunition[1:] if len(regional_ammunition) > 1 else regional_ammunition)
                df_r_ammo.to_sql('regional_ammunition', conn, if_exists='replace', index=False)
            
            if regional_pol:
                df_r_pol = pd.DataFrame(regional_pol[1:] if len(regional_pol) > 1 else regional_pol)
                df_r_pol.to_sql('regional_pol', conn, if_exists='replace', index=False)
            
            if regional_supply:
                df_supply = pd.DataFrame(regional_supply[1:] if len(regional_supply) > 1 else regional_supply)
                df_supply.to_sql('regional_supply', conn, if_exists='replace', index=False)
            
            if regional_transport:
                df_transport = pd.DataFrame(regional_transport[1:] if len(regional_transport) > 1 else regional_transport)
                df_transport.to_sql('regional_transport', conn, if_exists='replace', index=False)
            
            if regional_open_air:
                df_open_air = pd.DataFrame(regional_open_air[1:] if len(regional_open_air) > 1 else regional_open_air)
                df_open_air.to_sql('regional_open_air', conn, if_exists='replace', index=False)
            
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
                    d = Depot_downloader()
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


# eof 
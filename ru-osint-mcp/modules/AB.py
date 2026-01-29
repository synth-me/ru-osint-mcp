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

class AB_Explorer:
    """
        This object allows you to explore the "airfield" database 
    """
    
    VALID_COUNTRIES = ['RUS', 'BLR']
    VALID_SERVICES = ['A', 'N', 'UI', 'NF', None]
    
    def __init__(self, db_path: str = "../sqlite-database/ru-airfields.sqlite"):
        self.db_path = db_path

        self.tables = [
            'military_air_bases',
            'reserve_military_airfields',
            'former_military_airfields',
            'civil_airports',
            'helicopter_bases'
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
        table_name: str,
        country: Optional[str] = None,
        air_base: Optional[str] = None,
        service: Optional[str] = None,
        location: Optional[str] = None,
        oblast: Optional[str] = None,
        main_user: Optional[str] = None,
        has: Optional[str] = None,
        revetm: Optional[str] = None,
        aircraft: Optional[str] = None,
        state: Optional[str] = None,
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
            
            if air_base is not None:
                conditions.append("air_base LIKE ?")
                params.append(f"%{air_base}%")
            
            # Service uses exact match (case-insensitive) or NULL check
            if service is not None:
                conditions.append("UPPER(service) = ?")
                params.append(service.upper())
            
            if location is not None:
                conditions.append("location LIKE ?")
                params.append(f"%{location}%")
            
            if oblast is not None:
                conditions.append("oblast LIKE ?")
                params.append(f"%{oblast}%")
            
            if main_user is not None:
                conditions.append("main_user LIKE ?")
                params.append(f"%{main_user}%")
            
            if has is not None:
                conditions.append("has LIKE ?")
                params.append(f"%{has}%")
            
            if revetm is not None:
                conditions.append("revetm LIKE ?")
                params.append(f"%{revetm}%")
            
            if aircraft is not None:
                conditions.append("aircraft LIKE ?")
                params.append(f"%{aircraft}%")
            
            if state is not None:
                conditions.append("state LIKE ?")
                params.append(f"%{state}%")
            
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

            logging.info(json.dumps(result,indent=4))
            
            return result
            
        except Exception as e:
            logger.info(f"Error querying database: {e}")
            return []
            
        finally:
            conn.close()
    
    def query_military_air_bases(self, **kwargs) -> dict:
        """Query military air bases table"""
        return self.query_template(table_name='military_air_bases', **kwargs)
    
    def query_reserve_military_airfields(self, **kwargs) -> dict:
        """Query reserve military airfields table"""
        return self.query_template(table_name='reserve_military_airfields', **kwargs)
    
    def query_former_military_airfields(self, **kwargs) -> dict:
        """Query former military airfields table"""
        return self.query_template(table_name='former_military_airfields', **kwargs)
    
    def query_civil_airports(self, **kwargs) -> dict:
        """Query civil airports table"""
        return self.query_template(table_name='civil_airports', **kwargs)
    
    def query_helicopter_bases(self, **kwargs) -> dict:
        """Query helicopter bases table"""
        return self.query_template(table_name='helicopter_bases', **kwargs)
    
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
        """Get basic statistics about the database"""
        conn = sqlite3.connect(self.db_path)
        stats = {}
        
        try:
            for table_name in self.tables:
                # Total count
                count_query = f"SELECT COUNT(*) as count FROM {table_name}"
                count_df = pd.read_sql_query(count_query, conn)
                
                # Country breakdown
                country_query = f"SELECT country, COUNT(*) as count FROM {table_name} GROUP BY country"
                country_df = pd.read_sql_query(country_query, conn)
                
                # Service breakdown
                service_query = f"SELECT service, COUNT(*) as count FROM {table_name} GROUP BY service"
                service_df = pd.read_sql_query(service_query, conn)
                
                stats[table_name] = {
                    'total': count_df['count'][0],
                    'by_country': country_df.to_dict('records'),
                    'by_service': service_df.to_dict('records')
                }
        
        finally:
            conn.close()
        
        return stats

class AB_downloader:

    def __init__(self):

        with open("../config/url.json","r",encoding="utf-8") as url_links_source:
            url_links_source_text = json.loads(url_links_source.read())
            url_links_source.close()

        self.url = url_links_source_text["AB"]
        self.source = ""
        self.tables = []  # Store extracted tables
        self.names = [
            "index_table",
            "military_air_bases_used_by_military_units",
            "reserve_military_airfields",
            "former_military_airfields",
            "civil_airfields",
            "helicopters_bases"
        ]

    def download_source(self) -> bool:
        try:
            r = requests.get(self.url)
            self.source = r.text

            with open("../sources/AB.html","w",encoding="utf-8") as file:
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
        # First, find where to search until
        if next_start_pos is None:
            search_end = len(self.source)
        else:
            search_end = next_start_pos
        
        # Search area for this table
        search_area = self.source[start_pos:search_end]
        
        # Look for embedded title tables (border="0") that appear after data rows
        # These are title tables for the NEXT section, not part of the current data table
        # Pattern matches: </td><table, </tr><table, or </tbody><table with border="0"
        title_table_pattern = r'(</td>|</tr>|</tbody>)<table[^>]*border="0"[^>]*>'
        
        title_match = re.search(title_table_pattern, search_area, re.IGNORECASE)
        
        if title_match:
            # Found a title table - stop before it
            # The match includes the closing tag (</td>, </tr>, or </tbody>)
            end_pos = start_pos + title_match.start() + len(title_match.group(1))
        else:
            # No title table found, use the original logic
            if next_start_pos is None:
                # This is the last table
                end_pos = search_end
            else:
                # Find the last </td> before the next table
                last_td = search_area.rfind('</td>')
                if last_td > 0:
                    end_pos = start_pos + last_td + 5  # +5 for length of </td>
                else:
                    end_pos = next_start_pos
        
        table_html = self.source[start_pos:end_pos]
        
        # Clean up and close tags properly
        table_html = table_html.rstrip()
        
        # Add closing tags if missing
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

    def save_tables_to_files(self, output_dir="../tables/AB", prefix="table"):
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

class AB_Parser:

    """
        This object defines the parser for the airfield data 
        with all the following tables:
        
            Military Air Bases
            Reserve Military Airfields
            Former Military Airfields
            Civil Airports
            Helicopter Bases
    """

    def __init__(self):

        self.headers = [
            "Country",
            "Air Base",
            "Service",
            "Location",
            "Oblast",
            "Main User",
            "HAS",
            "Revetm",
            "Aircraft",
            "State",
            "Link",
            "Image",
            "Street",
            "Rail",
            "KML"
        ]
        self.columns = ['_'.join(header.split()).lower() for header in self.headers]

        self.files = [
            "civil_airfields",
            "former_military_airfields",
            "helicopters_bases",
            "military_air_bases_used_by_military_units",
            "reserve_military_airfields"
        ]
        self.contents = {}

        self.contents = {name:self.get_source(name) for name in self.files}
 
    def get_source(self, file: str) -> str:

        with open(f"../tables/AB/{file}.html","r",encoding="utf-8") as file:
            content = file.read()
            file.close()

        return content

    def extract_link_from_td(self, td):
        anchor = td.find('a')
        if anchor and anchor.get('href'):
            return anchor.get('href')
        return None

    def format_json(self,cells: list) -> list:

        return {
            'country': cells[0].get_text(strip=True),
            'air_base': cells[1].get_text(strip=True),
            'service': cells[2].get_text(strip=True),
            'location': cells[3].get_text(strip=True),
            'oblast': cells[4].get_text(strip=True),
            'main_user': cells[5].get_text(strip=True),
            'has': cells[6].get_text(strip=True),
            'revetm': cells[7].get_text(strip=True),
            'aircraft': cells[8].get_text(strip=True),
            'state': cells[9].get_text(strip=True),

            'link': self.extract_link_from_td(cells[10]),
            'image': self.extract_link_from_td(cells[11]),
            'street': self.extract_link_from_td(cells[12]),
            'rail': self.extract_link_from_td(cells[13]),
            'kml': self.extract_link_from_td(cells[14])
        }

    def parse_table(self, table_name:str) -> list:

        container = []

        soup = BeautifulSoup(self.contents[table_name], 'html.parser')
        
        rows = soup.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            
            if len(cells) < 15:
                continue
            
            row_data = self.format_json(cells)
            
            container.append(row_data)
        
        return container
    
    def parse_military_air_base(self) -> list:
        table = self.parse_table("military_air_bases_used_by_military_units")
        return table

    def parse_reserve_military_airfield(self) -> list:
        table = self.parse_table("reserve_military_airfields")
        return table 
    
    def parse_former_military_airfield(self) -> list:
        table = self.parse_table("former_military_airfields")
        return table 
    
    def parse_civil_airports(self) -> list:
        table = self.parse_table("civil_airfields")
        return table 
    
    def parse_helicopters_bases(self) -> list:
        table = self.parse_table("helicopters_bases")
        return table 
    
    def push_to_database(self):
    
        military_airbases = self.parse_military_air_base()
        reserve_military_airbase = self.parse_reserve_military_airfield()
        former_military_airbase = self.parse_former_military_airfield()
        civil_airfield = self.parse_civil_airports()
        helicopter_bases = self.parse_helicopters_bases()
        
        db_path = "../sqlite-database/ru-airfields.sqlite"
        conn = sqlite3.connect(db_path)
        
        try:
    
            if military_airbases:
                df_military = pd.DataFrame(military_airbases[1:] if len(military_airbases) > 1 else military_airbases)
                df_military.to_sql('military_air_bases', conn, if_exists='replace', index=False)
            
            if reserve_military_airbase:
                df_reserve = pd.DataFrame(reserve_military_airbase[1:] if len(reserve_military_airbase) > 1 else reserve_military_airbase)
                df_reserve.to_sql('reserve_military_airfields', conn, if_exists='replace', index=False)
            
            if former_military_airbase:
                df_former = pd.DataFrame(former_military_airbase[1:] if len(former_military_airbase) > 1 else former_military_airbase)
                df_former.to_sql('former_military_airfields', conn, if_exists='replace', index=False)
            
            if civil_airfield:
                df_civil = pd.DataFrame(civil_airfield[1:] if len(civil_airfield) > 1 else civil_airfield)
                df_civil.to_sql('civil_airports', conn, if_exists='replace', index=False)
            
            if helicopter_bases:
                df_helicopters = pd.DataFrame(helicopter_bases[1:] if len(helicopter_bases) > 1 else helicopter_bases)
                df_helicopters.to_sql('helicopter_bases', conn, if_exists='replace', index=False)
            
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
                    d = AB_downloader()
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
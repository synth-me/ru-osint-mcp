import sqlite3
import re
import math
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from mcp.types import Icon
import logging
import os 
import sys 
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s — %(levelname)s — %(name)s — %(message)s",
)

logger = logging.getLogger(__name__)

def extract_maps(origin: tuple, radius_km: float, mode: str = "ground") -> dict:
    """
        Returns a dictionary where:
            Key: Table Name
            Value: List of rows (including distance) found within that table
    """

    if mode == "ground":
        db_name = "ru-ground-forces.sqlite"
    elif mode == "airfield":
        db_name = "ru-airfields.sqlite"
    elif mode == "depot":
        db_name = "ru-depots.sqlite"
    
    try:
        conn = sqlite3.connect("../sqlite-database/"+db_name)
        cursor = conn.cursor()
    except sqlite3.OperationalError:
        print(f"Error: Could not find database {db_name}")
        return {}

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    
    categorized_results = {}

    for table in tables:
        cursor.execute(f"PRAGMA table_info(`{table}`)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'image' not in columns:
            continue
            
        img_index = columns.index('image')
        cursor.execute(f"SELECT * FROM `{table}`")
        rows = cursor.fetchall()

        table_matches = []

        for row in rows:
            coords = parse_map(row[img_index])
            if coords:
                dist_val = distance(origin, coords)
                if dist_val <= radius_km:
                    row_list = list(row)
                    row_list.append(round(dist_val, 2))
                    table_matches.append(row_list)

        # Only add the table to the dictionary if we found matches
        if table_matches:
            # Sort matches within this table by distance
            table_matches.sort(key=lambda x: x[-1])
            categorized_results[table] = table_matches

    conn.close()
    return categorized_results

def parse_map(url: str) -> tuple:
    if not isinstance(url, str): return None
    regex = r"@([-+]?\d+\.\d+),([-+]?\d+\.\d+)"
    match = re.search(regex, url)
    return (float(match.group(1)), float(match.group(2))) if match else None

def distance(origin: tuple, final: tuple) -> float:
    lat1, lon1 = origin
    lat2, lon2 = final
    R = 6371.0 
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def near_bases(origin: str, radius: float = 150, mode: str = "ground") -> dict:
    geolocator = Nominatim(user_agent="osint-researcher")
    
    try:
        location = geolocator.geocode(origin)
        if location:
            logging.info(f"Found: {location.address}")
            origin = (location.latitude, location.longitude)
        else:
            logging.info(f"Location not found: {origin}")
            return {}
    except GeocoderTimedOut:
        logging.info("Service timed out. Try again.")
        return {}

    return extract_maps(origin, radius, mode)

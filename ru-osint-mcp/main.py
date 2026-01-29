from modules import AB, GF, Depot, POI, GeoTools, Oblast, InspectionTools,Authentication, Metadata
from fastmcp import FastMCP
from mcp.types import Icon
from typing import Optional
import logging 
import sys

mcp = FastMCP(
    name="RusMilMcp"
)
mcp.add_middleware(Authentication.SQLiteAuthMiddleware())

airbases = AB.AB_Explorer()
ground_forces = GF.GF_Explorer()
metadata = Metadata.Metadata()
explorer = POI.POI_Explorer()

logging.basicConfig(
    filename="../logs/server-log.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

logger = logging.getLogger(__name__)

# ------- prompts -------------

@mcp.prompt 
def react_map():
    """
        This prompt allows you to render a map using coordinates
    """
    with open("./additional-information/react-template-map.jsx","r",encoding="utf-8") as react_template_file:
        react_template_content = react_template_file.read()
        react_template_file.close()
    return react_template_content

# ------- auxiliary - tools -------------

@mcp.tool 
def near_assets(origin: str, radius: float = 150, mode: str = "ground") -> dict:
    """
    Find assets (airfield, ground forces or airfields) near an origin place.

    Args:
        origin: Place name (city, address, landmark)
        radius: Range in km to search
        mode: 
            airfield
            ground
            depot
        
    Returns:
        List of bases in the area with their types
    """
    return GeoTools.near_bases(origin, radius, mode)

@mcp.tool
def inspect_detailed(link: str) -> str:

    """
        This function takes the "link" column of a given information
        and retrieve a clean version of the page it is consulting 

        Args:
            link (str): the "link" column of a given data 
        
        Returns:
            The cleaned and more detailed information from that link
    """

    return InspectionTools.inspect(link)

@mcp.tool
def query_metadata(database: str) -> dict | str:
    """
        This tool can find metadata related size of information 
        in specific databases (how many elements in each table). 
        The possible databases are any other table 
        that exists in the query tools

        Args:
            airfield
            ground forces
            point of interest
            depots 
        
        Returns:
            a dict with the size of the tables inside given database
    """

    if database == "airfield":
        return metadata.airfield_metadata()
    elif database == "ground forces":
        return metadata.ground_forces_metadata()
    elif database == "points of interest":
        return metadata.poi_metadata()
    elif database == "depots":
        return metadata.depots_metadata()
    else:
        return f"{database} does not exist"

# ------- ground forces - tools -------------

@mcp.tool
def query_ground_forces(
    table: str = "all",
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
) -> list | dict:
    """
    Query any table in the ground forces database.
    
    Args:
        table: The table to search. Options:
            - "tanks" or "barracks tanks forces"
            - "motorized" or "barracks motorized rifle forces"
            - "artillery" or "barracks artillery forces"
            - "airborne" or "barracks airborne forces"
            - "headquarters" or "barracks headquarters forces"
            - "other barracks"
            - "other military bases"
            - "other facilities"
            - "special facilities"
            - "all" (search all tables)
        country: Country code (RUS, BLR, UKR, GEO, MDA, ARM)
        location: Location name (partial match)
        oblast: Oblast/region name (partial match)
        service: Service type (A=Army, N=Navy, UI=Unknown, NF=Naval Fleet)
        main_user: Main user/military unit (partial match)
        state: State/status (partial match)
        image: Image information (partial match)
        topo: Topographic information (partial match)
        street: Street information (partial match)
        rail: Rail information (partial match)
        kml: KML data (partial match)
        poi: POI information (partial match)
        limit: Maximum number of results to return
    
    Returns:
        JSON string of matching facilities
    """
    oblast = Oblast.get_fuzzy_oblast(oblast)
    kwargs = {
        'country': country,
        'location': location,
        'oblast': oblast,
        'service': service,
        'main_user': main_user,
        'state': state,
        'image': image,
        'topo': topo,
        'street': street,
        'rail': rail,
        'kml': kml,
        'poi': poi,
        'limit': limit
    }
    
    table = table.lower()
    
    if table in ["tanks", "barracks tanks forces"]:
        return ground_forces.query_barracks_tanks_forces(**kwargs)
    elif table in ["motorized", "barracks motorized rifle forces"]:
        return ground_forces.query_barracks_motorized_rifle_forces(**kwargs)
    elif table in ["artillery", "barracks artillery forces"]:
        return ground_forces.query_barracks_artillery_forces(**kwargs)
    elif table in ["airborne", "barracks airborne forces"]:
        return ground_forces.query_barracks_airborne_forces(**kwargs)
    elif table in ["headquarters", "barracks headquarters forces"]:
        return ground_forces.query_barracks_headquarters_forces(**kwargs)
    elif table == "other barracks":
        return ground_forces.query_other_barracks(**kwargs)
    elif table == "other military bases":
        return ground_forces.query_other_military_bases(**kwargs)
    elif table == "other facilities":
        return ground_forces.query_other_facilities(**kwargs)
    elif table == "special facilities":
        return ground_forces.query_special_facilities(**kwargs)
    elif table == "all":
        return ground_forces.search_all_tables(**kwargs)
    else:
        return {"error": f"Unknown table: {table}. Use 'tanks', 'motorized', 'artillery', 'airborne', 'headquarters', 'other barracks', 'other military bases', 'other facilities', 'special facilities', or 'all'"}

# ------- air force - airfield - tools -------------

@mcp.tool
def query_airfields(
    table: str = "all",
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
) -> list | dict:
    """
    Query any table in the airfields database.
    
    Args:
        table: The table to search. Options:
            - "helicopter" or "helicopter bases"
            - "civil" or "civil airports"
            - "military" or "military air bases"
            - "reserve" or "reserve military airfields"
            - "former" or "former military airfields"
            - "all" (search all tables)
        country: Country code (RUS or BLR)
        air_base: Air base/airport name (partial match)
        service: Service type (A=Air Force, N=Navy, UI=Unknown, NF=Naval Fleet)
        location: Location name (partial match)
        oblast: Oblast/region name (partial match)
        main_user: Main user/operator (partial match)
        has: HAS (Hardened Aircraft Shelter) information
        revetm: Revetment information
        aircraft: Aircraft type (partial match)
        state: State/status (partial match)
        limit: Maximum number of results to return
    
    Returns:
        List of the information found in the databases
    """

    oblast = Oblast.get_fuzzy_oblast(oblast)
    kwargs = {
        'country': country,
        'air_base': air_base,
        'service': service,
        'location': location,
        'oblast': oblast,
        'main_user': main_user,
        'has': has,
        'revetm': revetm,
        'aircraft': aircraft,
        'state': state,
        'limit': limit
    }
    
    table = table.lower()
    
    if table in ["helicopter", "helicopter bases"]:
        return airbases.query_helicopter_bases(**kwargs)
    elif table in ["civil", "civil airports"]:
        return airbases.query_civil_airports(**kwargs)
    elif table in ["military", "military air bases"]:
        return airbases.query_military_air_bases(**kwargs)
    elif table in ["reserve", "reserve military airfields"]:
        return airbases.query_reserve_military_airfields(**kwargs)
    elif table in ["former", "former military airfields"]:
        return airbases.query_former_military_airfields(**kwargs)
    elif table == "all":
        return airbases.search_all_tables(**kwargs)
    else:
        return {"error": f"Unknown table: {table}. Use 'helicopter', 'civil', 'military', 'reserve', 'former', or 'all'"}

# ------- depots - tools -------------

@mcp.tool
def query_depots(
    table: str = "all",
    country: Optional[str] = None,
    locations: Optional[str] = None,
    service: Optional[str] = None,
    oblast: Optional[str] = None,
    specifications: Optional[str] = None,
    state: Optional[str] = None,
    limit: Optional[int] = 50
):
    """
    Query any logistics table in the depots database (ru-depots.sqlite).
    
    Args:
        table: The logistics category to search. Options:
            - "nuclear": Central & Regional nuclear storage
            - "ammunition": Central & Regional ammo depots
            - "pol": Central & Regional fuel depots
            - "sam": Surface-to-air missile depots
            - "weapons": Central weapon depots
            - "vehicles": Central vehicle storage
            - "repair": Aircraft repair plants
            - "supply": Regional supply & transport
            - "all": Search all logistics tables
        country: Country code (e.g., RUS, BLR, UKR)
        locations: Specific location name (partial match)
        service: Service type (A=Army, N=Navy, UI=Unknown, NF=Naval Fleet)
        oblast: Oblast/region name (partial match)
        specifications: Technical specs or main user info (partial match)
        state: Status of the facility (partial match)
        limit: Max results per table (default 50)
    
    Returns:
        List of findings across the specified logistics categories.
    """
    explorer = Depot.Depot_Explorer()
    results = []

    # Map friendly tool names to the actual database tables
    table_mapping = {
        "nuclear": ["central_nuclear_arsenals", "regional_nuclear_support"],
        "ammunition": ["central_ammunition_depots", "regional_ammunition"],
        "pol": ["central_pol_depots", "regional_pol"],
        "sam": ["central_sam_depots"],
        "weapons": ["central_weapon_depots", "central_artillery_depots"],
        "vehicles": ["central_vehicle_depots"],
        "repair": ["central_aircraft_repair"],
        "supply": ["regional_supply", "regional_transport", "regional_open_air"],
        "index": ["index_table"]
    }

    # Determine which tables to iterate over
    target_tables = []
    if table.lower() == "all":
        target_tables = explorer.tables
    elif table.lower() in table_mapping:
        target_tables = table_mapping[table.lower()]
    else:
        # Fallback for exact table name matches
        target_tables = [table] if table in explorer.tables else []

    if not target_tables:
        return f"Error: Table category '{table}' not found."

    oblast = Oblast.get_fuzzy_oblast(oblast)

    # Execute queries using the explorer logic
    for t_name in target_tables:
        table_results = explorer.query_template(
            table_name=t_name,
            country=country,
            locations=locations,
            service=service,
            oblast=oblast,
            specifications=specifications,
            state=state,
            limit=limit
        )
        
        # Add metadata to identify the source table in combined results
        for row in table_results:
            row["source_table"] = t_name
            results.append(row)

    return results 

# ------- poi - tools -------------

@mcp.tool
def query_poi(
    locations: Optional[str] = None,
    user: Optional[str] = None,
    type_of_locations: Optional[str] = None,
    type_of_change: Optional[str] = None,
    loc_id: Optional[str] = None,
    state: Optional[str] = None,
    limit: Optional[int] = 50
):
    """
    Query the Points of Interest (POI) database for infrastructure changes.
    
    Args:
        locations: Specific location name (partial match)
        user: Must be 'CIV' (Civilian) or 'MIL' (Military)
        type_of_locations: Category of the POI (e.g., 'Storage', 'Industrial')
        type_of_change: Specific category of change. Options:
            - "Complete new location"
            - "Routine works"
            - "Construction new location area(s)"
        loc_id: Unique Location Identifier (exact or partial)
        state: Status or condition of the POI
        limit: Maximum number of results to return (default 50)
        
    Returns:
        List of POI records including satellite imagery and street-level links.
    """
            
    oblast = Oblast.get_fuzzy_oblast(oblast)
    
    results = explorer.query_template(
        table_name="points_of_interest",
        locations=locations,
        user=user,
        type_of_locations=type_of_locations,
        type_of_change=type_of_change,
        loc_id=loc_id,
        state=state,
        limit=limit
    )

    if not results:
        return "No points of interest found matching those criteria."

    return results

# ------- oblasts - tools -------------

@mcp.tool
def get_oblasts():
    """
        This returns all possible oblasts 
    """
    return Oblast.all_oblasts()

# ------- database update -------------

def update_database():

    p0 = AB.AB_Parser()
    p0.run()

    p1 = GF.GF_Parser()
    p1.run()

    p2 = Depot.Depot_Parser()
    p2.run()

    p3 = POI.POI_Parser()
    p3.run()

    return 

if __name__ == "__main__":
    update_database()
    mode = sys.argv[1]
    if len(mode) >= 2:
        if mode == "stdio":
            mcp.run(transport="stdio")
        else:
            mcp.run(transport="sse", port=6000)
    else:
        mcp.run(transport="stdio")


# eof

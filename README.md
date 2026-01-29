# 🇷🇺 🔍 Russian Military Assets OSINT MCP

<img alt="logo" width="300" height="300" src="https://github.com/synth-me/ru-osint-mcp/blob/main/ru-osint-mcp/icons/server-logo.png"></img>

# Summary

- [Russian Military Assets OSINT MCP](#russian-military-assets-osint-mcp)
- [Summary](#summary)
  - [Purpose and Scope](#purpose-and-scope)
  - [Tools](#tools)
    - [Auxiliary Tools](#auxiliary-tools)
    - [Airfield Tools](#airfield-tools)
    - [Ground Forces Tools](#ground-forces-tools)
    - [Depot \& Logistics Tools](#depot--logistics-tools)
    - [Points of Interest (POI) Tools](#points-of-interest-poi-tools)
  - [Prompts](#prompts)
  - [Data Characteristics](#data-characteristics)
    - [Geographic Coverage](#geographic-coverage)
    - [Data Fields (Common)](#data-fields-common)
    - [Search Features](#search-features)
  - [Usage:](#usage)
  - [⚠️ Important ⚠️](#️-important-️)
  - [Future Upgrades](#future-upgrades)

## Purpose and Scope

This MCP (Model Context Protocol) server provides tools for querying publicly available information about Russian military infrastructure from OSINT databases. The server aggregates data about airfields, ground forces installations, logistics depots, and infrastructure changes.
One of the reasons I created this mcp server is to help OSINT researchers that do not have all the coding skills to 
extract data easily from public available sources. Also, in the future, other researchers may create new OSINT tools and 
this mcp server will help integrate it with other data sources that an LLM may have access to, helping open source researchers
to improve their investigation capabilities.  

I recommend using a powerful model (Claude, Mistral, ChatGPT all the free services available) because there are many tools and this will easily consume the context window of smaller models. but if you do not have a powerfull PC and want to run it locally i would recommend using:
* Qwen3:7b
* Granite4:Tiny

For more specific tools that closed source models may refuse to do (because we are dealing with military related information) i recommend using: 

* Cogito:8b
* Hermes3:8b

## Tools 

### Auxiliary Tools

* `near_assets`
Find military assets within a specified radius of any location.

**Parameters:**
- `origin` (str): Place name, city, address, or landmark to search from
- `radius` (float): Search radius in kilometers (default: 150 km)
- `mode` (str): Type of asset to search for
  - `"airfield"`: Military and civil airfields
  - `"ground"`: Ground forces installations
  - `"depot"`: Logistics and storage facilities

**Returns:** Dictionary of nearby military installations with their types and distances

**Example Use Cases:**
- "Find all airbases within 100km of Voronezh"
- "Show ground forces installations near the Ukrainian border"
- "Locate depots within 200km of Kaliningrad"

---

* `inspect_detailed`
Retrieve detailed, cleaned information from a database entry's source link.

**Parameters:**
- `link` (str): The "link" column value from any query result

**Returns:** Cleaned and detailed text content from the referenced webpage

**Example Use Cases:**
- Get full details about a specific airfield after finding it in search results
- Read complete information about a construction project
- Access detailed facility specifications

---

* `query_metadata`
Get metadata about database sizes and table information.

**Parameters:**
- `database` (str): Database to query
  - `"airfield"`: Airfield database statistics
  - `"ground forces"`: Ground forces database statistics
  - `"points of interest"`: POI database statistics
  - `"depots"`: Depot database statistics

**Returns:** Dictionary with table names and row counts for the specified database

**Example Use Cases:**
- Check how many military airfields are in the database
- Understand the scope of available ground forces data
- Verify database coverage before running queries

---

* `get_oblasts`
Retrieve a complete list of all Russian oblasts (administrative regions) recognized by the database.

**Parameters:** None

**Returns:** List of all valid oblast names for use in other queries

**Example Use Cases:**
- Get correct spelling for oblast names
- Browse available regions
- Reference for filtering queries

---

### Airfield Tools

* `query_airfields`
Query the comprehensive airfields database covering military, civil, and reserve aviation facilities.

**Parameters:**
- `table` (str): The category to search (default: `"all"`)
  - `"helicopter"` or `"helicopter bases"`: Dedicated helicopter facilities
  - `"civil"` or `"civil airports"`: Commercial/civilian airports
  - `"military"` or `"military air bases"`: Active military airfields
  - `"reserve"` or `"reserve military airfields"`: Reserve/standby airfields
  - `"former"` or `"former military airfields"`: Decommissioned facilities
  - `"all"`: Search across all airfield tables
- `country` (str, optional): Country code (RUS, BLR)
- `air_base` (str, optional): Air base/airport name (partial match supported)
- `service` (str, optional): Service branch
  - `"A"`: Air Force
  - `"N"`: Navy
  - `"UI"`: Unknown
  - `"NF"`: Naval Fleet
- `location` (str, optional): City or location name (partial match)
- `oblast` (str, optional): Oblast/region name (fuzzy matching enabled)
- `main_user` (str, optional): Primary operator or unit (partial match)
- `has` (str, optional): HAS (Hardened Aircraft Shelter) information
- `revetm` (str, optional): Revetment information
- `aircraft` (str, optional): Aircraft type stationed (partial match)
- `state` (str, optional): Operational status (partial match)
- `limit` (int, optional): Maximum number of results

**Returns:** List of airfield records with coordinates, operators, aircraft types, and infrastructure details

**Example Use Cases:**
- "Find all active military air bases in Kaliningrad Oblast"
- "List helicopter bases in Belarus"
- "Show former military airfields in Western Russia"

---

### Ground Forces Tools

* `query_ground_forces`
Query the ground forces database containing information about army installations, barracks, and military bases.

**Parameters:**
- `table` (str): The installation category (default: `"all"`)
  - `"tanks"` or `"barracks tanks forces"`: Tank unit barracks
  - `"motorized"` or `"barracks motorized rifle forces"`: Motorized rifle units
  - `"artillery"` or `"barracks artillery forces"`: Artillery unit installations
  - `"airborne"` or `"barracks airborne forces"`: Airborne/VDV forces
  - `"headquarters"` or `"barracks headquarters forces"`: Command headquarters
  - `"other barracks"`: Miscellaneous barracks
  - `"other military bases"`: Other types of bases
  - `"other facilities"`: Various military facilities
  - `"special facilities"`: Special purpose installations
  - `"all"`: Search across all ground forces tables
- `country` (str, optional): Country code (RUS, BLR, UKR, GEO, MDA, ARM)
- `location` (str, optional): Location name (partial match)
- `oblast` (str, optional): Oblast/region (fuzzy matching)
- `service` (str, optional): Service type
  - `"A"`: Army
  - `"N"`: Navy
  - `"UI"`: Unknown
  - `"NF"`: Naval Fleet
- `main_user` (str, optional): Military unit designation (partial match)
- `state` (str, optional): Status/condition (partial match)
- `image` (str, optional): Satellite imagery information
- `topo` (str, optional): Topographic data
- `street` (str, optional): Street-level information
- `rail` (str, optional): Rail connection data
- `kml` (str, optional): KML mapping data
- `poi` (str, optional): Point of interest data
- `limit` (int, optional): Maximum results

**Returns:** List of ground forces installations with coordinates, units, and facility details

**Example Use Cases:**
- "Find all tank barracks in the Southern Military District"
- "Search for motorized rifle units near Ukraine"
- "List airborne forces bases in Pskov Oblast"
- "Show headquarters facilities in Moscow Oblast"

---

### Depot & Logistics Tools

* `query_depots`
Query the logistics and supply infrastructure database covering ammunition, fuel, vehicles, and specialized storage facilities.

**Parameters:**
- `table` (str): Logistics category (default: `"all"`)
  - `"nuclear"`: Central & Regional nuclear storage sites
  - `"ammunition"`: Central & Regional ammunition depots
  - `"pol"`: Central & Regional POL (Petroleum, Oil, Lubricants) depots
  - `"sam"`: Surface-to-air missile storage depots
  - `"weapons"`: Central weapon depots (including artillery)
  - `"vehicles"`: Central vehicle storage facilities
  - `"repair"`: Aircraft repair plants
  - `"supply"`: Regional supply & transport hubs
  - `"all"`: Search all depot categories
- `country` (str, optional): Country code (RUS, BLR, UKR)
- `locations` (str, optional): Location name (partial match)
- `service` (str, optional): Service branch (A, N, UI, NF)
- `oblast` (str, optional): Oblast/region (fuzzy matching)
- `specifications` (str, optional): Technical specs or main user (partial match)
- `state` (str, optional): Facility status (partial match)
- `limit` (int, optional): Maximum results per table (default: 50)

**Returns:** List of depot records with source table identification, coordinates, and specifications

**Example Use Cases:**
- "Find ammunition depots in Western Military District"
- "Search for nuclear storage facilities"
- "List fuel depots in Crimea"
- "Show vehicle storage facilities near Moscow"
- "Find all SAM depot locations"

---

### Points of Interest (POI) Tools

* `query_poi`
Query the Points of Interest database tracking infrastructure changes, construction activity, and facility development.

**Parameters:**
- `locations` (str, optional): Location name (partial match)
- `user` (str, optional): Infrastructure type
  - `"CIV"`: Civilian infrastructure
  - `"MIL"`: Military infrastructure
- `type_of_locations` (str, optional): POI category (e.g., "Storage", "Industrial")
- `type_of_change` (str, optional): Change classification
  - `"Complete new location"`: Entirely new facilities
  - `"Routine works"`: Maintenance and regular operations
  - `"Construction new location area(s)"`: Expansion/new construction
- `loc_id` (str, optional): Unique Location Identifier (exact or partial)
- `state` (str, optional): Current status/condition
- `limit` (int, optional): Maximum results (default: 50)

**Returns:** List of POI records with satellite imagery links, street-level references, and change documentation

**Example Use Cases:**
- "Find new military construction in 2024"
- "Search for storage facility expansions in Rostov Oblast"
- "Show routine works at military locations"
- "List all civilian infrastructure changes"

---

## Prompts

* `react_map`
Generates a React template for rendering interactive maps with military location data.

**Parameters:**
- `name` (str): Map name/identifier for the rendered report

**Returns:** React JSX template code for creating an interactive map visualization

**Example Use Cases:**
- Create visual map of airfields in a region
- Plot ground forces deployment patterns
- Visualize logistics network coverage

---

## Data Characteristics

### Geographic Coverage
- **Primary:** Russian Federation
- **Secondary:** Belarus, Ukraine, Georgia, Moldova, Armenia

### Data Fields (Common)
Most queries return records containing:
- **Coordinates:** Latitude/longitude (WGS84)
- **Location:** City, oblast, administrative region
- **Service:** Military branch designation
- **Main User:** Unit name or operator
- **State:** Operational status
- **Links:** Satellite imagery, street view, topographic maps
- **Specifications:** Facility-specific technical details

### Search Features
- **Partial matching:** Most text fields support substring searches
- **Fuzzy oblast matching:** Automatically corrects oblast name variations
- **Cross-table search:** "all" option searches multiple related tables
- **Result limiting:** Control output size with limit parameter

---

## Usage: 

You can download it yourself and then install and usage both with `stdio` or `sse` and `http` 
or you can use the remote server that i just deployed at: https://rus-mil-osint.fastmcp.app/mcp
This specific cloud services has read only properties so i had to change some things 
to make it work, which means that all the logs are stdou instead of .log file, so be aware 
If you want to use it, email me at: murielpanegassi1@gmail.com or dm me here on github so that i can allow your
AI service to use this endpoint. 


## ⚠️ Important ⚠️

**Website Down**
Apparently https://osint-rumiloc.comi/ is down. The current server would fetch the data every 1 hour 
from the website but i cannot do it right now. So all the database is up to to date until `01/28/2026 15:56`
so take care, i couldnt scrap fetch all the data before it went down. 


## Future Upgrades

* Databases:
  * [x] ground forces
  * [x] airfields
  * [ ] aircrafts
  * [x] depots
  * [ ] air defenses 
  * [x] all possible oblasts
  * [x] POIS (points of interest)
* [x] find bases near an specified place in natural language 
* [x] auto update for every 1 hour login 
* [x] add metadata information 
 

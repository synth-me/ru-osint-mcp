import difflib
from typing import Optional

regions_data = [
    {"region": "Adygea", "type": "Republic", "map": 1, "link": None},
    {"region": "Arkhangelsk", "type": "Oblast", "map": None, "link": None},
    {"region": "Astrachan", "type": "Oblast", "map": None, "link": None},
    {"region": "Belgorod", "type": "Oblast", "map": None, "link": None},
    {"region": "Bryansk", "type": "Oblast", "map": None, "link": None},
    {"region": "Chechnya", "type": "Republic", "map": None, "link": None},
    {"region": "Chelyabinsk", "type": "Oblast", "map": 1, "link": None},
    {"region": "Crimea", "type": "Republic", "map": None, "link": "Oblast_40O.htm"},
    {"region": "Dagestan", "type": "Republic", "map": None, "link": None},
    {"region": "Ingushetia", "type": "Republic", "map": None, "link": None},
    {"region": "Ivanovo", "type": "Oblast", "map": 2, "link": None},
    {"region": "Kabardino-Balkar", "type": "Republic", "map": 7, "link": None},
    {"region": "Kaliningrad", "type": "Oblast", "map": None, "link": None},
    {"region": "Kalmyk", "type": "Republic", "map": 8, "link": None},
    {"region": "Kaluga", "type": "Oblast", "map": 3, "link": None},
    {"region": "Karachay-Cherkess", "type": "Republic", "map": 9, "link": None},
    {"region": "Karelia", "type": "Republic", "map": None, "link": None},
    {"region": "Kemerovo", "type": "Oblast", "map": 5, "link": None},
    {"region": "Komi", "type": "Republic", "map": None, "link": None},
    {"region": "Kostroma", "type": "Oblast", "map": 6, "link": None},
    {"region": "Krasnodar", "type": "Kray", "map": 1, "link": "Oblast_38O.htm"},
    {"region": "Kursk", "type": "Oblast", "map": None, "link": None},
    {"region": "Leningrad", "type": "Oblast", "map": None, "link": None},
    {"region": "Lipetsk", "type": "Oblast", "map": 8, "link": None},
    {"region": "Mari El", "type": "Republic", "map": 11, "link": None},
    {"region": "Mordovia", "type": "Republic", "map": 12, "link": None},
    {"region": "Moscow", "type": "Oblast", "map": 10, "link": None},
    {"region": "Murmansk", "type": "Oblast", "map": None, "link": None},
    {"region": "Nizhny Novgorod", "type": "Oblast", "map": 11, "link": None},
    {"region": "North Ossetia-Alania", "type": "Republic", "map": 13, "link": None},
    {"region": "Novgorod", "type": "Oblast", "map": 12, "link": None},
    {"region": "Orel", "type": "Oblast", "map": 14, "link": None},
    {"region": "Orenburg", "type": "Oblast", "map": None, "link": None},
    {"region": "Penza", "type": "Oblast", "map": 15, "link": None},
    {"region": "Perm", "type": "Kray", "map": None, "link": None},
    {"region": "Pskov", "type": "Oblast", "map": None, "link": None},
    {"region": "Rostov", "type": "Oblast", "map": None, "link": "Oblast_61O.htm"},
    {"region": "Ryazan", "type": "Oblast", "map": 16, "link": None},
    {"region": "Samara", "type": "Oblast", "map": 18, "link": None},
    {"region": "Saratov", "type": "Oblast", "map": None, "link": None},
    {"region": "Stavropol", "type": "Kray", "map": 2, "link": None},
    {"region": "Sverdlovsk", "type": "Oblast", "map": 19, "link": None},
    {"region": "Tambov", "type": "Oblast", "map": 20, "link": None},
    {"region": "Tula", "type": "Oblast", "map": 21, "link": None},
    {"region": "Tver", "type": "Oblast", "map": None, "link": None},
    {"region": "Ulyanovsk", "type": "Oblast", "map": 23, "link": None},
    {"region": "Vladimir", "type": "Oblast", "map": 24, "link": None},
    {"region": "Volgograd", "type": "Oblast", "map": 25, "link": None},
    {"region": "Vologda", "type": "Oblast", "map": 26, "link": None},
    {"region": "Voronezh", "type": "Oblast", "map": None, "link": "Oblast_86O.htm"},
    {"region": "Yaroslavl", "type": "Oblast", "map": 27, "link": None}
]

def all_oblasts():
    return regions_data

def get_fuzzy_oblast(user_input: Optional[str], threshold: float = 0.7) -> Optional[str]:
    """Finds the best matching region name from the known list."""
    if not user_input:
        return None
        
    search_term = user_input.lower().strip()
    best_match = None
    highest_ratio = 0.0

    for element in regions_data:
        region_name = element["region"]

        if search_term == region_name.lower():
            return region_name
        
        ratio = difflib.SequenceMatcher(None, search_term, region_name.lower()).ratio()
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match = region_name

    return best_match if highest_ratio >= threshold else user_input


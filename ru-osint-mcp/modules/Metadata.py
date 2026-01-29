import sqlite3

class Metadata:
    def __init__(self):

        self.databases = [
            "ru-airfields",
            "ru-depots",
            "ru-ground-forces",
            "ru-poi"
        ]

    def _fetch_counts(self, db_name: str) -> dict:
        """Helper method to connect and extract row counts for all tables."""
        results = {}
        try:

            conn = sqlite3.connect(f"{db_name}.sqlite")
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM [{table}];")
                results[table] = cursor.fetchone()[0]
                
            conn.close()
        except sqlite3.Error as e:
            return {"error": f"Could not access {db_name}: {str(e)}"}
            
        return results

    def get_metadata(self) -> dict:
        """Returns a nested dictionary with row counts for all 4 databases."""
        all_meta = {}
        for db in self.databases:
            all_meta[db] = self._fetch_counts(db)
        return all_meta

    def airfield_metadata(self) -> dict:
        return self._fetch_counts("ru-airfields")

    def depots_metadata(self) -> dict:
        return self._fetch_counts("ru-depots")

    def ground_forces_metadata(self) -> dict:
        return self._fetch_counts("ru-ground-forces")

    def poi_metadata(self) -> dict:
        return self._fetch_counts("ru-poi")

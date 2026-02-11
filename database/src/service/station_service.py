import hashlib
import random
import string
from db.record_types import get_all_repositories
from db.station_repo import StationRepository
from db.database_core import *
from service_core import *


class StationService(BaseService):
    def __init__(self, session):
        self._station_repo = StationRepository(session)
        self._record_repos = {
            r.get_record_identifier(): r for r in get_all_repositories()
        }
            
        super().__init__(session, "Station")
    
    # -- Station Auth -- #
    def get_stations(self):
        return self._station_repo.get_stations()

        
        
    def create_station(self, station_name: str) -> str:
        unhashed_pw, hashed_pw = self.generate_password_string()
        self._station_repo.create_new_station(station_name, hashed_pw)
        return unhashed_pw
        
        
    def update_station_password(self, station_id: int) -> str:
        unhashed_pw, hashed_pw = self.generate_password_string()
        self._station_repo.update_station_password(station_id, hashed_pw)
        return unhashed_pw


    ## Password Generation
    def generate_password_string(self) -> tuple[str, str]:
        string_len = random.randint(10, 15)
        password_string = "".join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(string_len)
        )
        print(f"Raw password String: {password_string}")
        hasher = hashlib.new("sha256")
        hasher.update(password_string.encode())
        hashed_pw = hasher.hexdigest()
        print(f"hashed_pw: {hashed_pw}")
        return password_string, hashed_pw


    # -- Station Handler -- #
    def get_trains_from_station(self, station_name: str, recent=False) -> dict:
        try:
            station_id = self._station_repo.get_station_id(station_name)
            
            results = {
                f"{t}_records": r.get_station_records(station_id, recent=recent)
                for t, r in self._record_repos.items()
            }
            
            return results
        
        except (IndexError, ValueError, TypeError) as e:
            raise ServiceParsingError(self.__class__.__name__, str(e))
        
        
    # TODO: Probably not neeeded
    def get_pin_info(self, station_name: str) -> dict:
        try:
            station_id = self._station_repo.get_station_id(station_name)

            results = {
                f"{t}_records": r.parse_station_records(
                    r.get_recent_station_records(station_id)
                )
                for t, r in self._record_repos.items()
            }
            
            return results

        except (IndexError, ValueError, TypeError) as e:
            raise ServiceParsingError(self.__class__.__name__, str(e))


    # -- Station Online -- #
    def get_last_seen(self, station_name: str) -> str:
        return self._station_repo.get_last_seen(station_name)
        
        
    def update_last_seen(self, station_id: int):
        self._station_repo.update_last_seen(station_id)
            
            
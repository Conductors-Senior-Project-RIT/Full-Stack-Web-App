import hashlib
import random
import string
from database.src.db.record_types import RecordTypes, get_record_repository
import database.src.db.station_repo as repo
from database.src.db.database_status import *
from database.src.service.service_core import *


class StationService(BaseService):
    def __init__(self):
        super().__init__("Station")
    
    # -- Station Auth -- #
    def get_stations(self):
        try:
            return repo.get_stations()
        except RepositoryTimeoutError:
            raise ServiceTimeoutError(self)
        except (RepositoryInternalError, RepositoryParsingError) as e:
            raise ServiceInternalError(self, str(e))
        
        
    def create_station(self, station_name: str) -> str:
        try:
            unhashed_pw, hashed_pw = self.generate_password_string()
            repo.create_new_station(station_name, hashed_pw)
            return unhashed_pw
        except RepositoryTimeoutError:
            raise ServiceTimeoutError(self)
        except RepositoryInternalError as e:
            raise ServiceInternalError(self, str(e))
        
        
    def update_station_password(self, station_id: int) -> str:
        try:
            unhashed_pw, hashed_pw = self.generate_password_string()
            repo.update_station_password(station_id, hashed_pw)
            return unhashed_pw
        except RepositoryTimeoutError:
            raise ServiceTimeoutError(self)
        except RepositoryNotFoundError as e:
            raise ServiceResourceNotFound(self, str(e))
        except RepositoryInternalError as e:
            raise ServiceInternalError(self, str(e))


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
            station_id = repo.get_station_id(station_name)
            
            repos = {
                "eot": get_record_repository(RecordTypes.EOT),
                "hot": get_record_repository(RecordTypes.HOT)
            }
            results = {
                f"{t}_records": r.get_station_records(station_id, recent=recent)
                for t, r in repos.items()
            }
            
            return results
        
        except RepositoryNotFoundError as e:
            raise ServiceResourceNotFound(self, str(e))
        except RepositoryTimeoutError:
            raise ServiceTimeoutError(self)
        except (RepositoryInternalError, RepositoryParsingError) as e:
            raise ServiceInternalError(self, str(e))
        except (IndexError, ValueError, TypeError) as e:
            raise ServiceParsingError(self)
        
        
    # TODO: Probably not neeeded
    def get_pin_info(self, station_name: str) -> dict:
        try:
            station_id = repo.get_station_id(station_name)
            
            repos = {
                "eot": get_record_repository(RecordTypes.EOT), 
                "hot": get_record_repository(RecordTypes.HOT)
            }
            results = {
                f"{t}_records": r.parse_station_records(
                    r.get_recent_station_records(station_id)
                )
                for t, r in repos.items()
            }
            
            return results
            
        except RepositoryTimeoutError:
            raise ServiceTimeoutError(self)
        except (RepositoryInternalError, RepositoryParsingError) as e:
            raise ServiceInternalError(self, str(e))
        except (IndexError, ValueError, TypeError) as e:
            raise ServiceParsingError(self)


    # -- Station Online -- #
    def get_last_seen(self, station_name: str) -> str:
        try:
            return repo.get_last_seen(station_name)
        except RepositoryTimeoutError:
            raise ServiceTimeoutError(self)
        except (RepositoryInternalError, RepositoryParsingError) as e:
            raise ServiceInternalError(self, str(e))
        except RepositoryNotFoundError as e:
            raise ServiceResourceNotFound(self, str(e))
        
        
    def update_last_seen(self, station_id: int):
        try:
            repo.update_last_seen(station_id)
        except RepositoryTimeoutError:
            raise ServiceTimeoutError()
        except RepositoryInternalError as e:
            raise ServiceInternalError(self, str(e))
        except RepositoryNotFoundError as e:
            raise ServiceResourceNotFound(self, str(e))
            
            
import hashlib
import random
import string
from database.src.db.record_types import RecordTypes, get_record_repository
import database.src.db.station_repo as repo
from database.src.db.database_status import NotFoundError, RepositoryError
from database.src.service.service_status import ServiceError

# Station Auth
def get_stations():
    try:
        return repo.get_stations()
    except RepositoryError as e:
        raise ServiceError(str(e))
    
def create_station(station_name: str) -> str:
    try:
        unhashed_pw, hashed_pw = generate_password_string()
        repo.create_new_station(station_name, hashed_pw)
        return unhashed_pw
    except RepositoryError as e:
        raise ServiceError(str(e))
    
def update_station_password(station_id: int) -> str:
    try:
        unhashed_pw, hashed_pw = generate_password_string()
        repo.update_station_password(station_id, hashed_pw)
        return unhashed_pw
    except NotFoundError as e:
        raise ValueError(str(e))
    except RepositoryError as e:
        raise ServiceError(str(e))

## Password Generation
def generate_password_string() -> tuple[str, str]:
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


# Station Handler
def get_trains_from_station(station_name: str, recent=False) -> dict:
    try:
        station_id = repo.get_station_id(station_name)
        
        repos = {
            "eot": get_record_repository(RecordTypes.EOT),
            "hot": get_record_repository(RecordTypes.HOT)
        }
        results = {
            f"{t}_records": (
                r.get_recent_station_records(station_id) 
                if recent else 
                r.get_station_records(station_id)
            )
            for t, r in repos.items()
        }
        
        return results
    
    except NotFoundError as e:
        return ValueError(str(e))
    except RepositoryError as e:
        return ServiceError(str(e))
    except (IndexError, ValueError, TypeError) as e:
        raise ServiceError(f"Error constructing results: {e}")
    
    
def get_pin_info(station_name: str) -> dict:
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
         
    except (IndexError, ValueError, TypeError) as e:
        raise ServiceError(f"Error constructing results: {e}")
    except RepositoryError as e:
        raise ServiceError(str(e))
    except NotFoundError as e:
        raise ValueError(str(e))
    

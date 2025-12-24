import hashlib
import random
import string
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


    

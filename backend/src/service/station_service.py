import hashlib
import random
import string

from ..db.station_repo import StationRepository
from .service_core import BaseService

class StationService(BaseService):
    def __init__(self, session):
        self._station_repo = StationRepository(session)
    
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


    # -- Station Online -- #
    def get_last_seen(self, station_name: str) -> str:
        return self._station_repo.get_last_seen(station_name)
        
    def update_last_seen(self, station_id: int) -> str:
        return self._station_repo.update_last_seen(station_id)
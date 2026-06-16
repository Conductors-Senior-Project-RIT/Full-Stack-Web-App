from datetime import datetime
import hashlib
import random
import string

from sqlalchemy.orm import Session

from ..db.station_repo import StationRepository
from .service_core import ServiceErrorWrapper


class StationService(ServiceErrorWrapper):
    """Handles business logic for station related data processing."""
    def __init__(self, session: Session):
        """Initializes a `StationRepository` with a provided **SQLAlchemy** session.

        Args:
            session (Session): The SQLAlchemy session to be used for database
                transactions in the service's repositories.
        """
        self.station_repo = StationRepository(session)

    # -- Station Auth -- #
    def get_stations(self) -> list[dict]:
        """Returns a list of station ID and name pairs from the database as dictionaries.

        Returns:
            list[dict]: A list of dictionaries containing station IDs and names.
        """
        return self.station_repo.get_stations()

    def create_station(self, station_name: str) -> str:
        """Creates a new station in the database with the provided name.

        Additionally, a random password is generated using generate_password_string`,
        and associated with the new station.

        Args:
            station_name (str): The name of the new station.

        Returns:
            str: The new randomly generated password for the new station.
        """
        unhashed_pw, hashed_pw = self.generate_password_string()
        self.station_repo.create_new_station(station_name, hashed_pw)
        return unhashed_pw

    def update_station_password(self, station_id: int) -> str:
        """Generates and updates the password of a specified station.

        The password is generated using `generate_password_string`.

        Args:
            station_id (int): The ID corresponding to the station to update.

        Returns:
            str: The newly generated password for the station.
        """
        unhashed_pw, hashed_pw = self.generate_password_string()
        self.station_repo.update_station_password(station_id, hashed_pw)
        return unhashed_pw

    ## Password Generation
    def generate_password_string(self) -> tuple[str, str]:
        """Generates a password string of 10 to 15 random uppercase ASCII and digit
        characters. Additionally, the password is hashed using SHA256.

        Returns:
            tuple[str, str]: Returns two strings in which the first is the unhashed
                password and the second is the hashed password.
        """

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
        """Returns a formatted datetime timestamp of when a station last pinged the server.

        Args:
            station_name (str): The name of the station.

        Returns:
            str: A formatted string containing the time and/or date of the ping. If the
                date is today, it is formatted as `HH:MM AM/PM`; otherwise, it is
                formatted as `MON DD, YYYY at HH:MM AM/PM`.
        """
        dt = self.station_repo.get_last_seen(station_name)
        return self._format_date(dt)

    def update_last_seen(self, station_id: int) -> str:
        """Updates a station's ping timestamp to the date and time at which this method is
        called.

        Args:
            station_id (int): The ID of the station to update.

        Returns:
            str: A formatted string containing the time of the ping, formatted as `HH:MM
                AM/PM`.
        """
        dt = self.station_repo.update_last_seen(station_id)
        return self._format_date(dt)

    def _format_date(self, dt: datetime) -> str:
        """Formats a datetime object into a string. If the date is today, it is formatted
        as `HH:MM AM/PM`; otherwise, it is formatted as `MON DD, YYYY at HH:MM AM/PM`.

        Args:
            dt (datetime): The datetime object to format.

        Returns:
            str: The formatted date string.
        """
        return (
            dt.strftime("%I:%M %p")
            if dt.date() == datetime.today().date()
            else dt.strftime("%b %d, %Y at %I:%M %p")
        )

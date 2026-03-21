from typing import Any, Self

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.automap import automap_base
from flask import Flask


db = SQLAlchemy()  # the db object gives you access to the db.Model class to define models, and the db.session to execute queries.

# Used for type checking
class Base(DeclarativeBase):  
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def _asdict(self) -> dict[str, Any]:
        return {
            col.key : getattr(self, col.key)
            for col in inspect(self).mapper.column_attrs
        }
        
    def __hash__(self):
        return hash((self.__class__, self.id))

    def __eq__(self, other) -> bool:
        if isinstance(other, Base):
            return self._asdict() == other._asdict()
        elif isinstance(other, dict):
            return self._asdict() == other
        else:
            False
            
    def copy(self) -> Self:
        return self.__class__(**self._asdict())
        
        


# Initialize automap using that Base class
AutomapBase = automap_base(declarative_base=Base)

def init_models(app: Flask):
    with app.app_context():
        # Prepare the Base model
        AutomapBase.prepare(autoload_with=db.engine)
        
        # Automapping models lacks Intellisense features, but reduces effort when changing tables.sql
        global Station
        Station = AutomapBase.classes.stations
        
        global ResetRequest
        ResetRequest = AutomapBase.classes.reset_requests
        
        global Symbol
        Symbol = AutomapBase.classes.symbols
        
        global EOTRecord
        EOTRecord = AutomapBase.classes.eotrecords
        
        global HOTRecord
        HOTRecord = AutomapBase.classes.hotrecords
        
        # global DPURecord
        # DPURecord = AutomapBase.classes.DPURecords
        
        global NotificationConfig
        NotificationConfig = AutomapBase.classes.notificationconfig
        
        global Pin
        Pin = AutomapBase.classes.pins
        
        global User
        User = AutomapBase.classes.users
        
        global UserPreference
        UserPreference = AutomapBase.classes.userpreferences
            
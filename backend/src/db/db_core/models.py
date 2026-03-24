from sqlalchemy import (
    String, Integer, ForeignKey,
    TIMESTAMP, Time, func, inspect
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime, time
from typing import Any, List, Optional, Self

from ....database import db

class Base(db.Model):  
    __abstract__ = True
    
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
        
        
class Station(Base):
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(primary_key=True)
    station_name: Mapped[str] = mapped_column(String(240), nullable=False)
    passwd: Mapped[str] = mapped_column(String(240), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), nullable=False)

    user_preferences = relationship("UserPreference", back_populates="station")
    eot_records = relationship("EOTRecord", back_populates="station")
    hot_records = relationship("HOTRecord", back_populates="station")
    notifications = relationship("NotificationConfig", back_populates="station")
    pins = relationship("Pin", back_populates="station")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(240), unique=True, nullable=False)
    passwd: Mapped[str] = mapped_column(String(240), nullable=False)
    token: Mapped[Optional[str]] = mapped_column(String(480), nullable=True)
    # 2 is normal user, 1 is volunteer, 0 is admin (ken) 
    acc_status: Mapped[int] = mapped_column(default=2, nullable=False)
    starting_time: Mapped[time] = mapped_column(Time(timezone=True), default=time(0, 0))
    ending_time: Mapped[time] = mapped_column(Time(timezone=True), default=time(23, 59))
    pushover_id: Mapped[Optional[str]] = mapped_column(String(240))
    
    user_preferences = relationship("UserPreference", back_populates="user")
    reset_requests = relationship("ResetRequest", back_populates="user")
    verified_eot = relationship("EOTRecord", back_populates="verifier")
    verified_hot = relationship("HOTRecord", back_populates="verifier")
        
    
class ResetRequest(Base):
    __tablename__ = "reset_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(64), nullable=False)
    expiration: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)

    user = relationship("User", back_populates="reset_requests")
    
    
class Symbol(Base):
    __tablename__ = "symbols"

    id: Mapped[int] = mapped_column(primary_key=True)
    symb_name: Mapped[str] = mapped_column(String(240), nullable=False)


class EngineNumber(Base):
    __tablename__ = "engine_numbers"

    id: Mapped[int] = mapped_column(primary_key=True)
    eng_num: Mapped[str] = mapped_column(String(240), nullable=False)
    

class EOTRecord(Base):
    __tablename__ = "eotrecords"

    id: Mapped[int] = mapped_column(primary_key=True)
    date_rec: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    station_recorded: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False)
    symbol_id: Mapped[Optional[int]] = mapped_column(ForeignKey("symbols.id"))
    engine_num: Mapped[Optional[int]] = mapped_column(ForeignKey("engine_numbers.id"))
    unit_addr: Mapped[str] = mapped_column(String(240), default="unknown")
    brake_pressure: Mapped[str] = mapped_column(String(240), default="unknown")
    motion: Mapped[str] = mapped_column(String(240), default="unknown")
    marker_light: Mapped[str] = mapped_column(String(240), default="unknown")
    turbine: Mapped[str] = mapped_column(String(240), default="unknown")
    battery_cond: Mapped[str] = mapped_column(String(240), default="unknown")
    battery_charge: Mapped[str] = mapped_column(String(240), default="unknown")
    arm_status: Mapped[str] = mapped_column(String(240), default="unknown")
    signal_strength: Mapped[float] = mapped_column(default=0.0)
    verified: Mapped[bool] = mapped_column(default=False)
    verifier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    most_recent: Mapped[bool] = mapped_column(default=True)
    locomotive_num: Mapped[str] = mapped_column(String(240), default="unknown")

    station = relationship("Station", back_populates="eot_records")
    symbol = relationship("Symbol")
    engine = relationship("EngineNumber")
    verifier = relationship("User", back_populates="verified_eot")
    
    
class HOTRecord(Base):
    __tablename__ = "hotrecords"

    id: Mapped[int] = mapped_column(primary_key=True)
    date_rec: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    station_recorded: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False)
    symbol_id: Mapped[Optional[int]] = mapped_column(ForeignKey("symbols.id"))
    engine_num: Mapped[Optional[int]] = mapped_column(ForeignKey("engine_numbers.id"))
    frame_sync: Mapped[str] = mapped_column(String(240), default="UNKNOWN")
    unit_addr: Mapped[str] = mapped_column(String(240), default="UNKNOWN")
    command: Mapped[str] = mapped_column(String(240), default="UNKNOWN")
    checkbits: Mapped[str] = mapped_column(String(240), default="UNKNOWN")
    parity: Mapped[str] = mapped_column(String(240), default="UNKNOWN")
    verified: Mapped[bool] = mapped_column(default=False)
    verifier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    most_recent: Mapped[bool] = mapped_column(default=True)
    locomotive_num: Mapped[str] = mapped_column(String(240), default="unknown")
    signal_strength: Mapped[float] = mapped_column(default=0.0)

    # For Station side (eg. HOTRecord.station_recorded <-> Station.hot_records)
    station = relationship("Station", back_populates="hot_records")
    symbol = relationship("Symbol")
    engine = relationship("EngineNumber")
    # For User side (eg. User.station_recorded <-> Station.hot_records)
    verifier = relationship("User", back_populates="verified_hot")
    
    
class NotificationConfig(Base):
    __tablename__ = "notificationconfig"

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False)
    notification_user_ids: Mapped[List[int]] = mapped_column(ARRAY(Integer))

    station = relationship("Station", back_populates="notifications")
    
    
class Pin(Base):
    __tablename__ = "pins"

    id: Mapped[int] = mapped_column(primary_key=True)
    station_location: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False)
    eot_signal: Mapped[Optional[int]] = mapped_column(ForeignKey("eotrecords.id"))
    hot_signal: Mapped[Optional[int]] = mapped_column(ForeignKey("hotrecords.id"))
    train_symbol: Mapped[Optional[int]] = mapped_column(ForeignKey("symbols.id"))
    engine_num: Mapped[Optional[int]] = mapped_column(ForeignKey("engine_numbers.id"))

    station = relationship("Station", back_populates="pins")
    
    
class UserPreference(Base):
    __tablename__ = "userpreferences"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), primary_key=True)
    
    station = relationship("Station", back_populates="user_preferences")
    user = relationship("User", back_populates="user_preferences")

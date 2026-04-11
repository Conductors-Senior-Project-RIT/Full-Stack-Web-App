from sqlalchemy import (
    String, Integer, ForeignKey,
    TIMESTAMP, Time, func, inspect
)
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime, time
from typing import Any, List, Optional, Self

from ....database import db

class Base(db.Model):  
    __abstract__ = True
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def _asdict(self):
        mapper = inspect(self.__class__)
        return {
            col.key: getattr(self, col.key)
            for col in mapper.columns
        }
        
    def __hash__(self):
        return hash(tuple(sorted(self._asdict().items())))

    def __eq__(self, other):
        if self is other:
            return True
        
        if isinstance(other, self.__class__):
            return self._asdict() == other._asdict()
        
        if isinstance(other, dict):
            return self._asdict() == other
        
        return False
            
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
    

class BaseRecord(AbstractConcreteBase, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    date_rec: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    unit_addr: Mapped[str] = mapped_column(String(240), default="unknown")
    verified: Mapped[bool] = mapped_column(default=False)
    most_recent: Mapped[bool] = mapped_column(default=True)
    locomotive_num: Mapped[str] = mapped_column(String(240), default="unknown")
    signal_strength: Mapped[float] = mapped_column(default=0.0)

    # Declarative columns
    @declared_attr
    def station_recorded(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("stations.id"), nullable=False)
        
    @declared_attr
    def symbol_id(cls) -> Mapped[Optional[int]]:
        return mapped_column(ForeignKey("symbols.id"))
    
    @declared_attr
    def engine_num(cls) -> Mapped[Optional[int]]:
        return mapped_column(ForeignKey("engine_numbers.id"))
    
    @declared_attr
    def verifier_id(cls) -> Mapped[Optional[int]]:
        return mapped_column(ForeignKey("users.id"))

    # Declarative relationships
    @declared_attr
    def station(cls) -> Mapped["Station"]:
        return relationship("Station")
    
    @declared_attr
    def verifier(cls) -> Mapped["User"]:
        return relationship("User")
    
    @declared_attr
    def symbol(cls) -> Mapped["Symbol"]:
        return relationship("Symbol")
    
    @declared_attr
    def engine(cls) -> Mapped["EngineNumber"]:
        return relationship("EngineNumber")
    

class EOTRecord(BaseRecord):
    __tablename__ = "eotrecords"

    brake_pressure: Mapped[str] = mapped_column(String(240), default="unknown")
    motion: Mapped[str] = mapped_column(String(240), default="unknown")
    marker_light: Mapped[str] = mapped_column(String(240), default="unknown")
    turbine: Mapped[str] = mapped_column(String(240), default="unknown")
    battery_cond: Mapped[str] = mapped_column(String(240), default="unknown")
    battery_charge: Mapped[str] = mapped_column(String(240), default="unknown")
    arm_status: Mapped[str] = mapped_column(String(240), default="unknown")

    # Override base relationships
    station = relationship("Station", back_populates="eot_records")
    verifier = relationship("User", back_populates="verified_eot")
    
    
class HOTRecord(BaseRecord):
    __tablename__ = "hotrecords"

    frame_sync: Mapped[str] = mapped_column(String(240), default="unknown")
    command: Mapped[str] = mapped_column(String(240), default="unknown")
    checkbits: Mapped[str] = mapped_column(String(240), default="unknown")
    parity: Mapped[str] = mapped_column(String(240), default="unknown")

    # Override base relationships
    station = relationship("Station", back_populates="hot_records")
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

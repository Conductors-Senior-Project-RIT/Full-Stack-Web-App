from sqlalchemy import (
    Boolean,
    Float,
    Interval,
    String,
    Integer,
    ForeignKey,
    TIMESTAMP,
    Time,
    func,
    inspect,
    text,
)
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime, time, timedelta
from typing import List, Optional, Self

from ....database import db


class Base(db.Model):
    __abstract__ = True

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _asdict(self):
        mapper = inspect(self.__class__)
        return {col.key: getattr(self, col.key) for col in mapper.columns}

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
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    station_name: Mapped[str] = mapped_column(String(240), nullable=False)
    passwd: Mapped[str] = mapped_column(String(240), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), nullable=False
    )

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
    acc_status: Mapped[int] = mapped_column(default=2, server_default=text("2"), nullable=False)
    starting_time: Mapped[time] = mapped_column(
        Time(timezone=True),
        default=time(0, 0),
        server_default=text("'00:00 EST'")
    )
    ending_time: Mapped[time] = mapped_column(
        Time(timezone=True),
        default=time(23, 59),
        server_default=text("'23:59 EST'")
    )
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
    unit_addr: Mapped[str] = mapped_column(String(240), default="unknown", server_default="unknown")
    verified: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    most_recent: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    locomotive_num: Mapped[str] = mapped_column(String(240), default="unknown", server_default="unknown")
    signal_strength: Mapped[float] = mapped_column(default=0.0, server_default=text("0.0"))

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

    @declared_attr
    def station(cls) -> Mapped["Station"]:
        return relationship("Station")

    @declared_attr
    def symbol(cls) -> Mapped[Optional["Symbol"]]:
        return relationship("Symbol")

    @declared_attr
    def engine(cls) -> Mapped[Optional["EngineNumber"]]:
        return relationship("EngineNumber")

    @declared_attr
    def verifier(cls) -> Mapped[Optional["User"]]:
        return relationship("User")

class CollationMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date_rec: Mapped[datetime] = mapped_column(TIMESTAMP)
    station_name: Mapped[str] = mapped_column(String)
    symb_name: Mapped[str | None] = mapped_column(String)
    unit_addr: Mapped[str] = mapped_column(String)
    signal_strength: Mapped[float] = mapped_column(Float)
    verified: Mapped[bool] = mapped_column(Boolean)
    first_seen: Mapped[datetime] = mapped_column(TIMESTAMP)
    last_seen: Mapped[datetime] = mapped_column(TIMESTAMP)
    occurrence_count: Mapped[int] = mapped_column(Integer)
    duration: Mapped[timedelta | None] = mapped_column(Interval)
    locomotive_num: Mapped[str | None] = mapped_column(String)


class EOTMixin:
    brake_pressure: Mapped[str] = mapped_column(String(240), default="unknown", server_default="unknown")
    motion: Mapped[str] = mapped_column(String(240), default="unknown", server_default="unknown")
    marker_light: Mapped[str] = mapped_column(String(240), default="unknown", server_default="unknown")
    turbine: Mapped[str] = mapped_column(String(240), default="unknown", server_default="unknown")
    battery_cond: Mapped[str] = mapped_column(String(240), default="unknown", server_default="unknown")
    battery_charge: Mapped[str] = mapped_column(String(240), default="unknown", server_default="unknown")
    arm_status: Mapped[str] = mapped_column(String(240), default="unknown", server_default="unknown")


class EOTRecord(EOTMixin, BaseRecord):
    __tablename__ = "eotrecords"
    __table_args__ = {"extend_existing": True}
    __mapper_args__ = {"polymorphic_identity": "eot", "concrete": True}

    @declared_attr
    def station(cls) -> Mapped["Station"]:
        return relationship("Station", back_populates="eot_records")

    @declared_attr
    def verifier(cls) -> Mapped[Optional["User"]]:
        return relationship("User", back_populates="verified_eot")

    @classmethod
    def get_unique_fields(cls) -> List[str]:
        return [
            cls.brake_pressure,
            cls.motion,
            cls.marker_light,
            cls.turbine,
            cls.battery_cond,
            cls.battery_charge,
            cls.arm_status,
            cls.signal_strength,
        ]


class EOTCollation(EOTMixin, CollationMixin, Base):
    __tablename__ = "eotcollation"
    __table_args__ = {"info": {"is_view": True}}
    
    total_count: Mapped[int] = mapped_column(Integer)


class HOTMixin:
    frame_sync: Mapped[str] = mapped_column(String(240), default="unknown", server_default="unknown")
    command: Mapped[str] = mapped_column(String(240), default="unknown", server_default="unknown")
    checkbits: Mapped[str] = mapped_column(String(240), default="unknown", server_default="unknown")
    parity: Mapped[str] = mapped_column(String(240), default="unknown", server_default="unknown")


class HOTCollation(HOTMixin, CollationMixin, Base):
    __tablename__ = "hotcollation"
    __table_args__ = {"info": {"is_view": True}}
    
    total_count: Mapped[int] = mapped_column(Integer)


class HOTRecord(HOTMixin, BaseRecord):
    __tablename__ = "hotrecords"
    __table_args__ = {"extend_existing": True}
    __mapper_args__ = {"polymorphic_identity": "hot", "concrete": True}
    
    @declared_attr
    def station(cls) -> Mapped["Station"]:
        return relationship("Station", back_populates="hot_records")

    @declared_attr
    def verifier(cls) -> Mapped[Optional["User"]]:
        return relationship("User", back_populates="verified_hot")

    @classmethod
    def get_unique_fields(cls) -> List[str]:
        return [cls.frame_sync, cls.command, cls.checkbits, cls.parity]


class NotificationConfig(Base):
    __tablename__ = "notificationconfig"

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False)
    notification_user_ids: Mapped[List[int]] = mapped_column(ARRAY(Integer))

    station = relationship("Station", back_populates="notifications")


class Pin(Base):
    __tablename__ = "pins"

    id: Mapped[int] = mapped_column(primary_key=True)
    station_location: Mapped[int] = mapped_column(
        ForeignKey("stations.id"), nullable=False
    )
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

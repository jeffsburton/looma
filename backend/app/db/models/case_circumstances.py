
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, String, Boolean, Date, Time
from sqlalchemy.sql import func

from app.db import Base


class CaseCircumstances(Base):
    __tablename__ = "case_circumstances"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False, unique=True)
    date_missing = Column(Date, nullable=True)
    time_missing = Column(Time(timezone=True), nullable=True)
    date_reported = Column(DateTime(timezone=True), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(50), nullable=True)

    # ref_type STATE
    state_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    point_last_seen = Column(Text, nullable=True)

    # ref_type YNU
    have_id_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    # ref_type YNU
    id_taken_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    # ref_type YNU
    have_money_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    # ref_type YNU
    money_taken_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    # ref_type YNU
    have_cc_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    # ref_type YNU
    cc_taken_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)
    vehicle_taken = Column(Boolean, nullable=False, server_default="false")
    vehicle_desc = Column(Text, nullable=True)

    with_whom = Column(Text, nullable=True)
    what_happened = Column(Text, nullable=True)

    clothing_top =  Column(Text, nullable=True)
    clothing_bottom = Column(Text, nullable=True)
    clothing_shoes = Column(Text, nullable=True)
    clothing_outerwear = Column(Text, nullable=True)
    clothing_innerwear = Column(Text, nullable=True)
    bags = Column(Text, nullable=True)
    other_items = Column(Text, nullable=True)

    # ref_type MOBILE
    mobile_carrier_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)
    mobile_carrier_other = Column(Text, nullable=True)

    # ref_type VOIP
    voip_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)
    wifi_only = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
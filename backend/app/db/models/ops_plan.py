from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, Date, String, Time
from sqlalchemy.sql import func

from app.db import Base


class OpsPlan(Base):
    __tablename__ = "ops_plan"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)

    created_by = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)

    forecast = Column(Text, nullable=True)
    temperature = Column(Integer, nullable=True)
    humidity = Column(Integer, nullable=True)
    precipitation = Column(Integer, nullable=True)
    uv_index = Column(Integer, nullable=True)
    winds = Column(Text, nullable=True)

    date = Column(Date, nullable=True)

    team_id = Column(Integer, ForeignKey("team.id", ondelete="CASCADE"), nullable=True)
    op_type_id = Column(Integer, ForeignKey("ref_value.id", ondelete="CASCADE"), nullable=True)
    op_type_other = Column(String(100), nullable=True)
    responsible_agency_id = Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), nullable=True)

    subject_legal_id = Column(Integer, ForeignKey("ref_value.id", ondelete="CASCADE"), nullable=True)

    address = Column(Text, nullable=True)
    city = Column(Text, nullable=True)
    vehicles = Column(Text, nullable=True)
    residence_owner = Column(String(100), nullable=True)

    threat_dogs_id = Column(Integer, ForeignKey("ref_value.id", ondelete="CASCADE"), nullable=True)
    threat_cameras_id = Column(Integer, ForeignKey("ref_value.id", ondelete="CASCADE"), nullable=True)
    threat_weapons_id = Column(Integer, ForeignKey("ref_value.id", ondelete="CASCADE"), nullable=True)
    threat_drugs_id = Column(Integer, ForeignKey("ref_value.id", ondelete="CASCADE"), nullable=True)
    threat_gangs_id = Column(Integer, ForeignKey("ref_value.id", ondelete="CASCADE"), nullable=True)
    threat_assault_id = Column(Integer, ForeignKey("ref_value.id", ondelete="CASCADE"), nullable=True)

    threat_other = Column(Text, nullable=True)

    briefing_time = Column(Time, nullable=True)
    rendevouz_location = Column(Text, nullable=True)
    primary_location = Column(Text, nullable=True)
    comms_channel_id = Column(Integer, ForeignKey("ref_value.id", ondelete="CASCADE"), nullable=True)

    police_phone = Column(String(50), server_default = "911", nullable=False)
    ems_phone = Column(String(50), server_default = "911", nullable=False)

    hospital_er_id = Column(Integer, ForeignKey("hospital_er.id", ondelete="CASCADE"), nullable=True)

    resp_contact_at_door_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=True)
    resp_overwatch_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=True)
    resp_navigation_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=True)
    resp_communications_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=True)
    resp_safety_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=True)
    resp_medical_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

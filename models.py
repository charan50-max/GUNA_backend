from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy import Column, String, Integer, Float, Text
from database import Base

class ContractorMaster(Base):
    __tablename__ = "contractor_master"
    companyid = Column(String, primary_key=True)
    projectscompleted = Column(Integer)
    gstin = Column(String)


class ContractorComplaints(Base):
    __tablename__ = "contractor_complaints"
    companyid = Column(String, primary_key=True)
    gstin = Column(String)
    projectscompleted = Column(Integer)

    complaint_1 = Column(Text)
    complaint_2 = Column(Text)
    complaint_3 = Column(Text)
    complaint_4 = Column(Text)
    complaint_5 = Column(Text)
    complaint_6 = Column(Text)


class DelayProjects(Base):
    __tablename__ = "delay_5projects_detailed"
    companyid = Column(String, primary_key=True)
    gstin = Column(String)
    projectscompleted = Column(Integer)

    p1_estimateddays = Column(Float)
    p1_govtconsenteddelaydays = Column(Float)
    p1_actualdays = Column(Float)

    p2_estimateddays = Column(Float)
    p2_govtconsenteddelaydays = Column(Float)
    p2_actualdays = Column(Float)

    p3_estimateddays = Column(Float)
    p3_govtconsenteddelaydays = Column(Float)
    p3_actualdays = Column(Float)

    p4_estimateddays = Column(Float)
    p4_govtconsenteddelaydays = Column(Float)
    p4_actualdays = Column(Float)

    p5_estimateddays = Column(Float)
    p5_govtconsenteddelaydays = Column(Float)
    p5_actualdays = Column(Float)


class Financials(Base):
    __tablename__ = "financials"
    companyid = Column(String, primary_key=True)
    gstin = Column(String)
    projectscompleted = Column(Integer)

    pat_2020 = Column(Float)
    networth_2020 = Column(Float)
    pat_2021 = Column(Float)
    networth_2021 = Column(Float)
    pat_2022 = Column(Float)
    networth_2022 = Column(Float)
    pat_2023 = Column(Float)
    networth_2023 = Column(Float)
    pat_2024 = Column(Float)
    networth_2024 = Column(Float)


class CostOverrun(Base):
    __tablename__ = "cost_overrun"
    companyid = Column(String, primary_key=True)
    gstin = Column(String)
    projectscompleted = Column(Integer)

    p1_estimatedcost_cr = Column(Float)
    p1_govtconsentedextracost_cr = Column(Float)
    p1_actualcost_cr = Column(Float)

    p2_estimatedcost_cr = Column(Float)
    p2_govtconsentedextracost_cr = Column(Float)
    p2_actualcost_cr = Column(Float)

    p3_estimatedcost_cr = Column(Float)
    p3_govtconsentedextracost_cr = Column(Float)
    p3_actualcost_cr = Column(Float)

    p4_estimatedcost_cr = Column(Float)
    p4_govtconsentedextracost_cr = Column(Float)
    p4_actualcost_cr = Column(Float)

    p5_estimatedcost_cr = Column(Float)
    p5_govtconsentedextracost_cr = Column(Float)
    p5_actualcost_cr = Column(Float)


class OTPFrequency(Base):
    __tablename__ = "otp_frequency"
    companyid = Column(String, primary_key=True)
    gstin = Column(String)
    projectscompleted = Column(Integer)

    p1_ontime = Column(Integer)
    p2_ontime = Column(Integer)
    p3_ontime = Column(Integer)
    p4_ontime = Column(Integer)
    p5_ontime = Column(Integer)

class Official(Base):
    __tablename__ = "officials"

    official_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    department = Column(String)
    state_code = Column(String)


class Tender(Base):
    __tablename__ = "tenders"

    tender_id = Column(String, primary_key=True, index=True)
    official_id = Column(Integer, ForeignKey("officials.official_id"))
    state_code = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(Text)

class TenderBidder(Base):
    __tablename__ = "tender_bidders"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(String, ForeignKey("tenders.tender_id"))
    companyid = Column(String, ForeignKey("contractor_master.companyid"))
    bid_value = Column(Float)
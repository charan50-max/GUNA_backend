from datetime import datetime
from sqlalchemy import func

from scoring_engine import (
    calculate_grv,
    calculate_fin,
    calculate_otp,
    calculate_dly,
    calculate_cov,
    calculate_confidence
)
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
import models

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- MASTER ----------
@app.get("/contractor/{company_id}/master")
def get_master(company_id: str, db: Session = Depends(get_db)):
    return db.query(models.ContractorMaster)\
             .filter(models.ContractorMaster.companyid == company_id)\
             .first()

# ---------- COMPLAINTS ----------
@app.get("/contractor/{company_id}/complaints")
def get_complaints(company_id: str, db: Session = Depends(get_db)):
    return db.query(models.ContractorComplaints)\
             .filter(models.ContractorComplaints.companyid == company_id)\
             .first()

# ---------- DELAY ----------
@app.get("/contractor/{company_id}/delay")
def get_delay(company_id: str, db: Session = Depends(get_db)):
    return db.query(models.DelayProjects)\
             .filter(models.DelayProjects.companyid == company_id)\
             .first()

# ---------- FINANCIALS ----------
@app.get("/contractor/{company_id}/financials")
def get_financials(company_id: str, db: Session = Depends(get_db)):
    return db.query(models.Financials)\
             .filter(models.Financials.companyid == company_id)\
             .first()

# ---------- COST ----------
@app.get("/contractor/{company_id}/cost")
def get_cost(company_id: str, db: Session = Depends(get_db)):
    return db.query(models.CostOverrun)\
             .filter(models.CostOverrun.companyid == company_id)\
             .first()

# ---------- OTP ----------
@app.get("/contractor/{company_id}/otp")
def get_otp(company_id: str, db: Session = Depends(get_db)):
    return db.query(models.OTPFrequency)\
             .filter(models.OTPFrequency.companyid == company_id)\
             .first()

@app.get("/contractor/{company_id}/guna_score")
def get_guna_score(company_id: str, db: Session = Depends(get_db)):

    master = db.query(models.ContractorMaster).filter_by(companyid=company_id).first()
    complaints = db.query(models.ContractorComplaints).filter_by(companyid=company_id).first()
    delay = db.query(models.DelayProjects).filter_by(companyid=company_id).first()
    financial = db.query(models.Financials).filter_by(companyid=company_id).first()
    cost = db.query(models.CostOverrun).filter_by(companyid=company_id).first()
    otp = db.query(models.OTPFrequency).filter_by(companyid=company_id).first()

    if not master or master.projectscompleted in [0,1]:
        return {"GUNA_score": "NEW"}

    grv = calculate_grv(complaints)
    fin = calculate_fin(financial)

    if fin == "NEW":
        return {"GUNA_score": "NEW"}

    otp_score = calculate_otp(otp)
    dly = calculate_dly(delay)
    cov = calculate_cov(cost)

    guna_score = fin + otp_score + dly + cov + grv
    normalized_score = (guna_score + 100) / 2
    confidence = calculate_confidence(master.projectscompleted, financial)

    return {
        "CompanyID": company_id,
        "FIN": round(fin, 2),
        "OTP": round(otp_score, 2),
        "DLY": round(dly, 2),
        "COV": round(cov, 2),
        "GRV": round(grv, 2),
        "GUNA_Score": round(guna_score, 2),
        "Normalized_GUNA_Score": round(normalized_score, 2),
        "Confidence": confidence
    }

@app.post("/official/create")
def create_official(name: str, department: str, state_code: str, db: Session = Depends(get_db)):

    official = models.Official(
        name=name,
        department=department,
        state_code=state_code
    )

    db.add(official)
    db.commit()
    db.refresh(official)

    return official

def generate_tender_id(state_code: str, db: Session):

    year = datetime.now().year

    # Count tenders for same state and year
    count = db.query(models.Tender)\
        .filter(models.Tender.state_code == state_code)\
        .filter(models.Tender.tender_id.contains(str(year)))\
        .count()

    sequence = str(count + 1).zfill(4)

    return f"{state_code}{year}{sequence}"

@app.post("/tender/create/{official_id}")
def create_tender(official_id: int, description: str, db: Session = Depends(get_db)):

    official = db.query(models.Official).filter_by(official_id=official_id).first()

    if not official:
        return {"error": "Official not found"}

    tender_id = generate_tender_id(official.state_code, db)

    tender = models.Tender(
        tender_id=tender_id,
        official_id=official_id,
        state_code=official.state_code,
        description=description
    )

    db.add(tender)
    db.commit()
    db.refresh(tender)

    return tender

@app.get("/tender/{tender_id}/evaluate/{company_id}")
def evaluate_contractor_for_tender(tender_id: str, company_id: str, db: Session = Depends(get_db)):

    tender = db.query(models.Tender).filter_by(tender_id=tender_id).first()
    contractor = db.query(models.ContractorMaster).filter_by(companyid=company_id).first()

    if not tender:
        return {"error": "Tender not found"}

    if not contractor:
        return {"error": "Contractor not found"}

    # Get base guna score
    base = get_guna_score(company_id, db)

    if "Raw_GUNA_Score" not in base:
        return base

    raw_score = base["Normalized_GUNA_Score"]

    contractor_state = contractor.gstin[:2]
    tender_state = tender.state_code

    bonus_applied = False

    if contractor_state == tender_state:
        raw_score += 2
        bonus_applied = True

    normalized = (raw_score + 100) / 2

    return {
        "TenderID": tender_id,
        "CompanyID": company_id,
        "Base_Raw_Score": base["Normalized_GUNA_Score"],
        "State_Bonus_Applied": bonus_applied,
        "Final_Raw_Score": round(raw_score, 2),
        "Final_Normalized_Score": round(normalized, 2),
        "Confidence": base["Confidence"]
    }

@app.post("/tender/{tender_id}/bid/{company_id}")
def submit_bid(tender_id: str, company_id: str, bid_value: float, db: Session = Depends(get_db)):

    if bid_value <= 0:
        return {"error": "Bid must be greater than zero"}

    tender = db.query(models.Tender).filter_by(tender_id=tender_id).first()
    contractor = db.query(models.ContractorMaster).filter_by(companyid=company_id).first()

    if not tender or not contractor:
        return {"error": "Invalid tender or contractor"}

    bidder = models.TenderBidder(
        tender_id=tender_id,
        companyid=company_id,
        bid_value=bid_value
    )

    db.add(bidder)
    db.commit()

    return {"message": "Bid submitted successfully"}

import statistics

@app.get("/tender/{tender_id}/final_table")
def final_tender_table(tender_id: str, db: Session = Depends(get_db)):

    tender = db.query(models.Tender).filter_by(tender_id=tender_id).first()
    if not tender:
        return {"error": "Tender not found"}

    bidders = db.query(models.TenderBidder)\
                .filter_by(tender_id=tender_id)\
                .all()

    if len(bidders) == 0:
        return {"error": "No bidders"}

    contractors_data = []

    # ---- Collect Aggregate Scores ----
    for b in bidders:

        base = get_guna_score(b.companyid, db)

        if "GUNA_Score" not in base:
            continue

        tech_score = base["Normalized_GUNA_Score"]

        contractor = db.query(models.ContractorMaster)\
                       .filter_by(companyid=b.companyid)\
                       .first()

        # ---- State Bonus ----
        if contractor.gstin[:2] == tender.state_code:
            tech_score += 1

        contractors_data.append({
            "companyid": b.companyid,
            "gstin": contractor.gstin,
            "score": tech_score,
            "confidence": base["Confidence"],
            "bid": b.bid_value
        })

    # ---- Handle NEW case ----
    known_scores = [c["score"] for c in contractors_data]

    if len(known_scores) == 0:
        return {"error": "All contractors NEW"}

    median_score = statistics.median(known_scores)

    for c in contractors_data:
        if c["score"] == "NEW":
            c["score"] = median_score

    max_score = max(c["score"] for c in contractors_data)
    min_score = min(c["score"] for c in contractors_data)
    min_bid = min(c["bid"] for c in contractors_data)

    ws = 0.6
    wb = 0.4

    # ---- Base Score ----
    for c in contractors_data:
        score_norm = c["score"] / 100
        bid_norm = (min_bid / c["bid"]) ** 2

        base_score = ws * score_norm + wb * bid_norm

        c["base_score"] = base_score

    # ---- Cost Per Point ----
    cost_per_point_list = []

    for c in contractors_data:
        score_diff = c["score"] - min_score
        bid_diff = c["bid"] - min_bid

        if score_diff > 0:
            cpp = bid_diff / score_diff
            c["cost_per_point"] = cpp
            cost_per_point_list.append(cpp)
        else:
            c["cost_per_point"] = 0

    avg_cpp = sum(cost_per_point_list) / len(cost_per_point_list)
    threshold_multiplier = 1.5
    max_allowed_cpp = avg_cpp * threshold_multiplier

    # ---- Final Score ----
    for c in contractors_data:
        penalty_factor = 1.0

        if c["cost_per_point"] > max_allowed_cpp and max_allowed_cpp != 0:
            excess_ratio = c["cost_per_point"] / max_allowed_cpp
            penalty_factor = 1 / excess_ratio

        final_score = c["base_score"] * penalty_factor

        # Multiply by 100 (as requested)
        c["final_score"] = final_score * 100

    # ---- Sort Descending ----
    ranked = sorted(contractors_data, key=lambda x: x["final_score"], reverse=True)

    for i, r in enumerate(ranked, start=1):
        r["rank"] = i

    return {
        "TenderID": tender_id,
        "Total_Bidders": len(ranked),
        "Results": ranked
    }

@app.delete("/reset_system")
def reset_system(db: Session = Depends(get_db)):

    db.query(models.TenderBidder).delete()
    db.query(models.Tender).delete()
    db.query(models.Official).delete()

    db.commit()

    return {"message": "System reset complete"}
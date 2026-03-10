import numpy as np
import joblib

# Load classifier once (global load for performance)
classifier = joblib.load("complaint_severity_classifier.pkl")


# ---------------- GRV ----------------
def calculate_grv(complaints_row):

    severe = 0
    mild = 0
    low = 0

    complaint_fields = [
        complaints_row.complaint_1,
        complaints_row.complaint_2,
        complaints_row.complaint_3,
        complaints_row.complaint_4,
        complaints_row.complaint_5,
        complaints_row.complaint_6,
    ]

    for text in complaint_fields:
        if text:
            prediction = classifier.predict([text])[0]

            if prediction == "Severe":
                severe += 1
            elif prediction == "Mild":
                mild += 1
            elif prediction == "Low":
                low += 1

    severe = min(severe, 5)
    mild = min(mild, 5)
    low = min(low, 5)

    score = (severe * 7.5) + (mild * 2) + (low * 0.5)
    score = min(score, 50)

    return -score


# ---------------- FIN ----------------
def calculate_fin(financial_row):

    projects_completed = financial_row.projectscompleted
    roe_values = []

    for year in range(2020, 2025):
        pat = getattr(financial_row, f"pat_{year}")
        nw = getattr(financial_row, f"networth_{year}")

        if pat is not None and nw is not None and nw != 0:
            roe = (pat / nw) * 100
            roe_values.append(roe)

    if len(roe_values) <= 1:
        return "NEW"

    avg_roe = np.mean(roe_values)
    fin_score = avg_roe / projects_completed

    fin_score = max(min(fin_score, 50), -50)

    return fin_score


# ---------------- OTP ----------------
def calculate_otp(otp_row):

    projects_completed = otp_row.projectscompleted

    if projects_completed == 0:
        return 0

    on_time_count = (
        otp_row.p1_ontime +
        otp_row.p2_ontime +
        otp_row.p3_ontime +
        otp_row.p4_ontime +
        otp_row.p5_ontime
    )

    score = (on_time_count / projects_completed) * 48
    return min(score, 48)


# ---------------- DLY ----------------
def calculate_dly(delay_row):

    max_delay = 0

    for i in range(1, 6):
        est = getattr(delay_row, f"p{i}_estimateddays")
        gov = getattr(delay_row, f"p{i}_govtconsenteddelaydays")
        actual = getattr(delay_row, f"p{i}_actualdays")

        # Skip if any value missing
        if est is None or gov is None or actual is None:
            continue

        denom = est + gov

        if denom == 0:
            continue

        delay_percent = ((actual - denom) / denom) * 100

        if delay_percent > max_delay:
            max_delay = delay_percent

    max_delay = min(max_delay, 24)
    return -max(max_delay, 0)


# ---------------- COV ----------------
def calculate_cov(cost_row):

    max_cov = 0

    for i in range(1, 6):
        est = getattr(cost_row, f"p{i}_estimatedcost_cr")
        gov = getattr(cost_row, f"p{i}_govtconsentedextracost_cr")
        actual = getattr(cost_row, f"p{i}_actualcost_cr")

        # Skip if any value missing
        if est is None or gov is None or actual is None:
            continue

        denom = est + gov

        if denom == 0:
            continue

        cov_percent = ((actual - denom) / denom) * 100

        if cov_percent > max_cov:
            max_cov = cov_percent

    max_cov = min(max_cov, 24)
    return -max(max_cov, 0)
def calculate_confidence(projects_completed, financial_row):

    # Count financial years available (same logic as ETL)
    financial_years = 0

    for year in range(2020, 2025):
        pat = getattr(financial_row, f"pat_{year}")
        nw = getattr(financial_row, f"networth_{year}")

        if pat is not None and nw is not None:
            financial_years += 1

    min_val = 2
    max_val = 5

    proj_factor = min(max(projects_completed, min_val), max_val)
    fin_factor = min(max(financial_years, min_val), max_val)

    proj_norm = (proj_factor - 2) / 3
    fin_norm = (fin_factor - 2) / 3

    confidence = 0.25 + 0.75 * ((proj_norm + fin_norm) / 2)

    return round(confidence, 2)
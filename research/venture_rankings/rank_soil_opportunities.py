"""Reproducible candidate ranking using existing MIT-licensed PyMCDM.

A decision-aid ONLY. The 0..10 ratings are analyst hypotheses constrained by
cited external evidence in RANKED_SOIL_VENTURE_REVIEW_2026-11-23.md.
No sales receipts or independent chemical predictions are inferred.
Install: pip install pymcdm==1.4.0 numpy
Run: python research/venture_rankings/rank_soil_opportunities.py
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
from pymcdm.methods import TOPSIS, WSM

CRITERIA = [
    "Scientific defensibility", "Solo laptop feasibility", "Buyer trigger evidence",
    "Potential differentiated control", "No-lab-data start", "Career/portfolio fit",
    "Speed to proof",
]
WEIGHTS = np.array([0.23, 0.16, 0.20, 0.13, 0.12, 0.10, 0.06])
ROWS = [
    ("EU Soil Evidence Pack", [9,8,8,5,8,9,7]),
    ("Soil Sampling Priority Map", [8,9,7,4,7,9,8]),
    ("Surface Sealing/Removal Change Audit", [9,9,8,4,9,8,9]),
    ("Bare Soil / Erosion Exposure Alert", [8,9,7,4,8,8,9]),
    ("Lab Sample Provenance + Satellite QA", [9,9,6,4,5,8,7]),
    ("Orchard Pigment / Lab Calibration", [6,8,7,4,4,9,6]),
    ("Carbon Maps for Unsampled Land", [4,7,7,3,3,9,5]),
    ("Satellite Surface Moisture Triage", [6,8,6,4,8,7,7]),
    ("Surface Salinity Risk Screening", [5,7,6,5,6,8,6]),
    ("Lab Nutrients and pH Replacement", [1,5,6,3,2,7,3]),
    ("Bio-chemical Economic Forecasting", [3,5,5,3,4,8,4]),
    ("Water Pigments / Bloom QA", [7,8,7,4,7,8,7]),
    ("Habitat / Phenology Change Watch", [8,9,6,4,9,8,9]),
]
MATRIX = np.array([row[1] for row in ROWS], dtype=float)
TYPES = np.ones(len(CRITERIA), dtype=int)
assert MATRIX.shape == (len(ROWS), len(CRITERIA))
assert abs(float(WEIGHTS.sum())-1.0)<1e-10
assert np.isfinite(MATRIX).all() and (MATRIX>=0).all() and (MATRIX<=10).all()
TOPSIS_F = TOPSIS()
WSM_F = WSM()
ts = np.asarray(TOPSIS_F(MATRIX, WEIGHTS, TYPES),dtype=float)
ws = np.asarray(WSM_F(MATRIX, WEIGHTS, TYPES),dtype=float)
assert np.isfinite(ts).all() and np.isfinite(ws).all()
rng=np.random.default_rng(20261123)
wins=np.zeros(len(ROWS),dtype=int)
for _ in range(200):
    w = rng.dirichlet(WEIGHTS*120)
    t = np.asarray(TOPSIS_F(MATRIX,w,TYPES),dtype=float)
    wins[int(np.argmax(t))]+=1

# Red-team sensitivity: the inputs are judgment scores, not measured performance.
# Treat each criterion score as uncertain by ~1 point, independently.
score_wins=np.zeros(len(ROWS),dtype=int)
for _ in range(400):
    perturbed=np.clip(MATRIX+rng.normal(0,1.0,size=MATRIX.shape),0.1,10.0)
    s=np.asarray(TOPSIS_F(perturbed, WEIGHTS, TYPES),dtype=float)
    score_wins[int(np.argmax(s))]+=1

output={
    "schema":"sbei.venture_rank_analyst_v1",
    "date":"2026-11-23",
    "library":"PyMCDM 1.4.0 (MIT), TOPSIS and Weighted Sum Model (WSM)",
    "score_kind":"subjective decision utility, NOT outcome probability, accuracy, buyer revenue, measured market share, or commercial validation",
    "criteria":CRITERIA, "weights":WEIGHTS.tolist(),"higher_is_better":True,
    "sensitivity":{"runs":200,"seed":20261123,"weights_dirichlet_concentration":120,
                   "note":"Weight robustness is conditional on input scores; independent analyst-score jitter 400 trials (SD=1 point, clipped) separately shows rank sensitivity.","score_jitter_runs":400,"score_jitter_sd":1.0},
    "rows":[
        {"name":ROWS[i][0],"scores":ROWS[i][1],"topsis_preference":round(float(ts[i]),6),
         "wsm_preference":round(float(ws[i]),6),"top_under_weight_variation":int(wins[i]),"top_under_score_uncertainty":int(score_wins[i]),
         "rank":int(1+sum(ts[j]>ts[i] for j in range(len(ROWS))))}
         for i in range(len(ROWS))
    ],
    "hard_gates":{
        "paid_customer_evidence":False,
        "external_competitor_gap_confirmed":False,
        "validated_90_percent_lab_agreement":False,
        "supervisor_approved_scope_change":False,
        "no_send_external_outreach":True
    }
}
output["rows"].sort(key=lambda x:(x["rank"],x["name"]))
print(json.dumps(output,indent=2))

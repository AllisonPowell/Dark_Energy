"""
Minimal checker: compare your recovered best-fit means for LCDM
against official DESI DR2 released chain summaries.
"""
import json
import numpy as np

# Fill these with official DR2 summary values once downloaded.
DESI_LCDM_REF = {
    "H0": None,
    "Omega_m": None,
}

YOUR_RESULTS = {
    "H0": None,
    "Omega_m": None,
}

for k in DESI_LCDM_REF:
    print(k, DESI_LCDM_REF[k], YOUR_RESULTS[k])
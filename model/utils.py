import numpy as np

def validate_physical_region(params):
    if params.Omega_m <= 0:
        return False, "Omega_m must be positive."
    if params.Omega_m + params.V0 >= 1.0:
        return False, f"Omega_m ={params.Omega_m}, V0={params.V0}, Need Omega_m + V0 < 1 for positive scalar kinetic energy today."
    return True, ""
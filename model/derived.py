import numpy as np
from .background import V_linear

def derived_quantities(bg, params):
    phi = bg["phi"]
    y = bg["dphi_dN"]
    E2 = bg["E2"]

    V = V_linear(phi, params.V0, params.V1)
    kinetic = 0.5 * E2 * y**2
    rho_phi = kinetic + V
    p_phi = kinetic - V
    w_phi = p_phi / rho_phi

    return {
        "V": V,
        "kinetic": kinetic,
        "rho_phi": rho_phi,
        "p_phi": p_phi,
        "w_phi": w_phi
    }
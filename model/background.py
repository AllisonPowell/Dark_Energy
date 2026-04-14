import numpy as np
from scipy.integrate import solve_ivp

C_LIGHT = 299792.458  # km/s

def V_linear(phi, V0, V1):
    return V0 + V1 * phi

def E2_of_state(N, phi, dphi_dN, Omega_m, V0, V1):
    V = V_linear(phi, V0, V1)
    denom = 1.0 - 0.5 * dphi_dN**2
    if denom <= 0:
        return np.nan
    num = Omega_m * np.exp(-3.0 * N) + V
    return num / denom

def dlnH_dN(N, phi, dphi_dN, Omega_m, V0, V1):
    E2 = E2_of_state(N, phi, dphi_dN, Omega_m, V0, V1)
    if not np.isfinite(E2) or E2 <= 0:
        return np.nan
    matter_term = Omega_m * np.exp(-3.0 * N) / E2
    return -1.5 * matter_term - 1.5 * dphi_dN**2

def rhs_N(N, yvec, Omega_m, V0, V1):
    phi, dphi_dN = yvec
    E2 = E2_of_state(N, phi, dphi_dN, Omega_m, V0, V1)
    if not np.isfinite(E2) or E2 <= 0:
        return [np.nan, np.nan]

    dlH = dlnH_dN(N, phi, dphi_dN, Omega_m, V0, V1)
    d2phi_dN2 = -(3.0 + dlH) * dphi_dN - V1 / E2
    return [dphi_dN, d2phi_dN2]

def initial_conditions_today(Omega_m, V0):
    """
    Enforce phi(N=0)=0 and choose the rolling-toward-negative-phi branch.
    From E(0)^2=1:
        1 = (Omega_m + V0) / (1 - y0^2/2)
    so
        y0^2/2 = 1 - Omega_m - V0
    """
    kinetic = 1.0 - Omega_m - V0
    if kinetic < 0:
        raise ValueError("Unphysical today: negative scalar kinetic energy.")
    y0_mag = np.sqrt(2.0 * kinetic)
    # choose present rolling toward negative phi, as in the paper
    y0 = -y0_mag
    phi0 = 0.0
    return phi0, y0

def integrate_background(params, z_max=2.5, npts=1200):
    """
    Integrate backward from today N=0 to N_min = -ln(1+z_max).
    """
    N0 = 0.0
    Nmin = -np.log(1.0 + z_max)
    phi0, y0 = initial_conditions_today(params.Omega_m, params.V0)

    grid = np.linspace(N0, Nmin, npts)

    sol = solve_ivp(
        fun=lambda N, y: rhs_N(N, y, params.Omega_m, params.V0, params.V1),
        t_span=(N0, Nmin),
        y0=[phi0, y0],
        t_eval=grid,
        rtol=1e-8,
        atol=1e-10,
        method="RK45"
    )

    if not sol.success:
        raise RuntimeError(sol.message)

    N = sol.t
    phi = sol.y[0]
    dphi_dN = sol.y[1]
    E2 = np.array([E2_of_state(n, p, yp, params.Omega_m, params.V0, params.V1)
                   for n, p, yp in zip(N, phi, dphi_dN)])
    if np.any(~np.isfinite(E2)) or np.any(E2 <= 0):
        raise RuntimeError("Background produced invalid H^2.")

    E = np.sqrt(E2)
    z = np.exp(-N) - 1.0

    return {
        "N": N,
        "z": z,
        "phi": phi,
        "dphi_dN": dphi_dN,
        "E": E,
        "E2": E2
    }
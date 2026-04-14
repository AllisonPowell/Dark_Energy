from dataclasses import dataclass

@dataclass
class ModelParams:
    h: float           # H0 / (100 km/s/Mpc)
    Omega_m: float     # present-day matter fraction
    V0: float          # dimensionless, in units of H0^2
    V1: float          # dimensionless slope, in units of H0^2
    M_B: float = -19.3 # SN nuisance
    rdrag: float = 147.0 # sound horizon in Mpc, free in first implementation
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np

from model.params import ModelParams
from model.background import integrate_background
from model.observables import build_distance_tables
from model.derived import derived_quantities

p = ModelParams(
    h=0.68,
    Omega_m=0.30,
    V0=0.69,
    V1=0.0,
    rdrag=147.0,
)

bg = integrate_background(p, z_max=3.0, npts=2000)
dist = build_distance_tables(bg, p.h)
der = derived_quantities(bg, p)

print("Background computed successfully.")
print("z range:", bg["z"].min(), bg["z"].max())
print("E^2 min/max:", bg["E2"].min(), bg["E2"].max())
print("w_phi at z~0:", der["w_phi"][np.argmin(np.abs(bg["z"]))])

for z in [0.295, 0.510, 0.706, 0.934, 1.321, 1.484, 2.330]:
    da = dist["interp_Dm"](z) / (1.0 + z)
    hz = dist["interp_H"](z)
    print(f"z={z:5.3f}  DA={float(da):12.6f} Mpc   H={float(hz):12.6f} km/s/Mpc")
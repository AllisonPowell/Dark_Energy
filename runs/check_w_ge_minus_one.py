import numpy as np

from model.params import ModelParams
from model.background import integrate_background
from model.derived import derived_quantities

# Replace these with your best-fit values from the chain
p = ModelParams(
    h=0.733,
    Omega_m=0.291,
    V0=0.659,
    V1=1.1,
    M_B=0.0,
    rdrag=147.0,
)

bg = integrate_background(p, z_max=3.0, npts=2000)
der = derived_quantities(bg, p)

z = bg["z"]
w = der["w_phi"]

print("min w =", float(np.min(w)))
print("max w =", float(np.max(w)))

tol = 1e-8
if np.min(w) >= -1 - tol:
    print("Model stays at w >= -1 over the sampled redshift range.")
else:
    print("Found w < -1 somewhere: likely numerical or implementation issue.")



import matplotlib.pyplot as plt

order = np.argsort(z)
plt.plot(z[order], w[order])
plt.axhline(-1.0, linestyle="--")
plt.xlabel("z")
plt.ylabel("w_phi(z)")
plt.title("Best-fit equation of state")
plt.show()
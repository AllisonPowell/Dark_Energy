import numpy as np
from cobaya.likelihood import Likelihood

class CMBCompressed(Likelihood):
    path: str = None
    def initialize(self):
        self.mean = np.loadtxt(self.path + "/mean.txt")
        self.Cinv = np.loadtxt(self.path + "/covinv.txt")

    def get_requirements(self):
        return {}

    def logp(self, **params_values):
        # simplest first version:
        # use sampled or derived values matching the compressed vector
        # e.g. [h, Omega_b h^2, Omega_c h^2, theta_*] in a later upgrade
        theory_vec = np.array([
            params_values["h"],
            params_values["Omega_m"],
            params_values["rdrag"]
        ])
        delta = theory_vec - self.mean
        chi2 = delta @ self.Cinv @ delta
        return -0.5 * chi2
import os
import glob
import numpy as np
import pandas as pd
from cobaya.likelihood import Likelihood


class PantheonPlusSH0ESRepro(Likelihood):
    path = None
    z_min = 0.01  # paper-style cut: keep zHD >= 0.01

    def initialize(self):
        base = self.path

        if os.path.isdir(os.path.join(base, "current")):
            base = os.path.join(base, "current")

        if not os.path.isdir(base):
            raise FileNotFoundError(f"Pantheon+SH0ES likelihood path does not exist: {base}")

        # Prefer the official calibrated SH0ES files
        preferred_data = os.path.join(base, "Pantheon+SH0ES.dat")
        preferred_cov = os.path.join(base, "Pantheon+SH0ES_STAT+SYS.cov")

        if os.path.exists(preferred_data):
            self.data_path = preferred_data
        else:
            data_candidates = sorted(glob.glob(os.path.join(base, "*SH0ES*.dat")))
            if not data_candidates:
                raise FileNotFoundError(
                    f"Could not find Pantheon+SH0ES.dat under {base}"
                )
            self.data_path = data_candidates[0]

        if os.path.exists(preferred_cov):
            self.cov_path = preferred_cov
        else:
            cov_candidates = sorted(glob.glob(os.path.join(base, "*SH0ES*STAT+SYS*.cov")))
            if not cov_candidates:
                raise FileNotFoundError(
                    f"Could not find Pantheon+SH0ES_STAT+SYS.cov under {base}"
                )
            self.cov_path = cov_candidates[0]

        self._load_data()

    def _read_covariance(self, cov_path: str, n_total: int) -> np.ndarray:
        """
        Pantheon+ covariance files are plain text and often stored either as:
        - an n x n matrix
        - or as a flattened array with the first number equal to n
        """
        raw = np.loadtxt(cov_path, dtype=float)

        if raw.ndim == 1:
            if int(raw[0]) == n_total and len(raw) == 1 + n_total * n_total:
                return raw[1:].reshape((n_total, n_total))
            raise ValueError(
                f"Could not interpret 1D covariance format in {cov_path}"
            )

        if raw.ndim == 2:
            if raw.shape == (n_total, n_total):
                return raw
            if raw.shape == (n_total + 1, n_total + 1):
                return raw[1:, 1:]
            raise ValueError(
                f"Unexpected covariance shape {raw.shape} for n_total={n_total}"
            )

        raise ValueError(f"Unexpected covariance ndim={raw.ndim}")

    def _load_data(self):
        # Official Pantheon+SH0ES file is whitespace-delimited with comment lines
        df = pd.read_csv(self.data_path, sep='\s+', comment="#")

        # Required columns for the reproduction branch
        if "zHD" not in df.columns:
            raise ValueError(
                f"Pantheon+SH0ES file missing 'zHD'. Available columns: {list(df.columns)}"
            )

        # Use the SH0ES-calibrated distance modulus column
        if "MU_SH0ES" not in df.columns:
            raise ValueError(
                f"Pantheon+SH0ES file missing 'MU_SH0ES'. Available columns: {list(df.columns)}"
            )

        z_all = df["zHD"].to_numpy(dtype=float)
        mu_all = df["MU_SH0ES"].to_numpy(dtype=float)

        n_total = len(z_all)
        C_all = self._read_covariance(self.cov_path, n_total)

        if C_all.shape != (n_total, n_total):
            raise ValueError(
                f"Covariance shape {C_all.shape} does not match full sample size {n_total}"
            )

        # Paper-style cut: keep only zHD >= z_min
        mask = z_all >= self.z_min

        self.z = z_all[mask]
        self.mu_data = mu_all[mask]

        # Apply the same mask to covariance rows and columns
        self.C = C_all[np.ix_(mask, mask)]

        if self.C.shape != (len(self.z), len(self.z)):
            raise ValueError(
                f"Cut covariance shape {self.C.shape} does not match cut sample size {len(self.z)}"
            )

        self.Cinv = np.linalg.inv(self.C)

    def get_requirements(self):
        return {"luminosity_distance": {"z": self.z}}

    def logp(self, **params_values):
        Dl = self.provider.get_luminosity_distance(self.z)  # Mpc

        # Cosmological distance modulus
        mu_cosmo = 5.0 * np.log10(Dl) + 25.0

        # Keep the same nuisance-parameter convention as your existing code:
        # M_B is an additive offset around the already-calibrated SH0ES distances.
        M_B = params_values.get("M_B", 0.0)
        mu_model = mu_cosmo + M_B

        delta = self.mu_data - mu_model
        chi2 = float(delta @ self.Cinv @ delta)
        return -0.5 * chi2
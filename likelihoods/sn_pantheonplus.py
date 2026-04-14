import os
import glob
import numpy as np
import pandas as pd
from cobaya.likelihood import Likelihood


class PantheonPlus(Likelihood):
    path = None

    def initialize(self):
        base = self.path

        # Allow either data/pantheonplus or data/pantheonplus/current
        if os.path.isdir(os.path.join(base, "current")):
            base = os.path.join(base, "current")

        if not os.path.isdir(base):
            raise FileNotFoundError(f"Pantheon+ likelihood path does not exist: {base}")

        # Prefer the canonical official filenames
        preferred_data = os.path.join(base, "Pantheon+SH0ES.dat")
        preferred_cov = os.path.join(base, "Pantheon+SH0ES_STAT+SYS.cov")

        if os.path.exists(preferred_data):
            self.data_path = preferred_data
        else:
            data_candidates = (
                sorted(glob.glob(os.path.join(base, "*SH0ES*.dat"))) +
                sorted(glob.glob(os.path.join(base, "*.dat"))) +
                sorted(glob.glob(os.path.join(base, "*.txt"))) +
                sorted(glob.glob(os.path.join(base, "*.csv")))
            )
            if not data_candidates:
                raise FileNotFoundError(f"No Pantheon+ data file found under {base}")
            self.data_path = data_candidates[0]

        if os.path.exists(preferred_cov):
            self.cov_path = preferred_cov
        else:
            cov_candidates = (
                sorted(glob.glob(os.path.join(base, "*STAT+SYS*.cov"))) +
                sorted(glob.glob(os.path.join(base, "*cov*.cov"))) +
                sorted(glob.glob(os.path.join(base, "*cov*.txt"))) +
                sorted(glob.glob(os.path.join(base, "*cov*.dat"))) +
                sorted(glob.glob(os.path.join(base, "*.cov")))
            )
            if not cov_candidates:
                raise FileNotFoundError(f"No Pantheon+ covariance file found under {base}")
            self.cov_path = cov_candidates[0]

        self._load_data()

    def _load_data(self):
        # Pantheon+ official file is whitespace-delimited .dat
        if self.data_path.endswith(".csv"):
            df = pd.read_csv(self.data_path)
        else:
            df = pd.read_csv(self.data_path, sep='\s+', comment="#")

        # Official Pantheon+ file commonly has zHD and MU_SH0ES
        if "zHD" not in df.columns:
            raise ValueError(
                f"Pantheon+ file missing 'zHD'. Available columns: {list(df.columns)}"
            )

        if "MU_SH0ES" in df.columns:
            mu_col = "MU_SH0ES"
        elif "MU" in df.columns:
            mu_col = "MU"
        else:
            raise ValueError(
                f"Pantheon+ file missing distance modulus column. "
                f"Available columns: {list(df.columns)}"
            )

        self.z = df["zHD"].to_numpy(dtype=float)
        self.mu_data = df[mu_col].to_numpy(dtype=float)
        n = len(self.z)

        # .cov is a plain text covariance matrix
        self.C = np.loadtxt(self.cov_path, dtype=float)

        # Some covariance files have the dimension in the first entry/row.
        # Handle both possibilities.
        if self.C.ndim == 1:
            # Flattened text file: first element may be n, followed by n*n entries
            arr = self.C
            if int(arr[0]) == n and len(arr) == 1 + n * n:
                self.C = arr[1:].reshape((n, n))
            else:
                raise ValueError(
                    f"Could not interpret 1D Pantheon+ covariance file {self.cov_path}"
                )
        elif self.C.ndim == 2:
            if self.C.shape == (n + 1, n + 1):
                # Sometimes first row/col can encode size; trim if needed
                self.C = self.C[1:, 1:]
            elif self.C.shape == (n, n):
                pass
            else:
                raise ValueError(
                    f"Pantheon+ covariance shape {self.C.shape} does not match "
                    f"number of SNe ({n})"
                )
        else:
            raise ValueError(f"Unexpected covariance array shape: {self.C.shape}")

        if self.C.shape != (n, n):
            raise ValueError(
                f"Pantheon+ covariance shape {self.C.shape} does not match number of SNe ({n})"
            )

        self.Cinv = np.linalg.inv(self.C)

    def get_requirements(self):
        return {"luminosity_distance": {"z": self.z}}

    def logp(self, **params_values):
        Dl = self.provider.get_luminosity_distance(self.z)  # Mpc
        mu_cosmo = 5.0 * np.log10(Dl) + 25.0

        # In this project M_B is treated as an additive SN nuisance offset
        M_B = params_values.get("M_B", 0.0)
        mu_model = mu_cosmo + M_B

        delta = self.mu_data - mu_model
        chi2 = float(delta @ self.Cinv @ delta)
        return -0.5 * chi2
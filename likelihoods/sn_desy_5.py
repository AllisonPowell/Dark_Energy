import glob
import os
import numpy as np
import pandas as pd
from cobaya.likelihood import Likelihood


def _load_inverse_covariance_old(npz_path: str) -> np.ndarray:
    data = np.load(npz_path, allow_pickle=True)
    keys = list(data.keys())

    # Dense matrix stored directly
    for k in keys:
        arr = data[k]
        if isinstance(arr, np.ndarray) and arr.ndim == 2:
            return np.asarray(arr, dtype=float)

    # CSR-style sparse matrix
    csr_keys = {"data", "indices", "indptr", "shape"}
    if csr_keys.issubset(set(keys)):
        vals = np.asarray(data["data"], dtype=float)
        indices = np.asarray(data["indices"], dtype=int)
        indptr = np.asarray(data["indptr"], dtype=int)
        shape = tuple(np.asarray(data["shape"], dtype=int))

        mat = np.zeros(shape, dtype=float)
        for row in range(shape[0]):
            start = indptr[row]
            end = indptr[row + 1]
            cols = indices[start:end]
            mat[row, cols] = vals[start:end]
        return mat

    raise ValueError(
        f"Could not interpret inverse covariance file: {npz_path}. "
        f"Available keys: {keys}"
    )

def _load_inverse_covariance(npz_path: str) -> np.ndarray:
    data = np.load(npz_path, allow_pickle=True)
    
    if "cov" in data and "nsn" in data:
        nsn = int(np.squeeze(data["nsn"]))
        cov_flat = np.asarray(data["cov"], dtype=float)
        
        # Check if the size matches the triangular format
        if cov_flat.size == nsn * (nsn + 1) // 2:
            # Reconstruct the symmetric matrix from upper triangular values
            mat = np.zeros((nsn, nsn))
            indices = np.triu_indices(nsn)
            mat[indices] = cov_flat
            # Mirror the upper triangle to the lower triangle
            mat = mat + mat.T - np.diag(mat.diagonal())
        elif cov_flat.size == nsn * nsn:
            mat = cov_flat.reshape((nsn, nsn))
        else:
            raise ValueError(f"Unknown covariance size {cov_flat.size} for nsn {nsn}")

        return mat

    raise ValueError(f"Missing keys in {npz_path}: {list(data.keys())}")


class DESY5(Likelihood):
    params = {"M_B": None, "Omega_m": None}
    path = None

    def initialize(self):
        base = self.path
        if os.path.isdir(os.path.join(base, "current")):
            base = os.path.join(base, "current")

        if not os.path.isdir(base):
            raise FileNotFoundError(f"DESY5 likelihood path does not exist: {base}")

        hd_candidates = sorted(glob.glob(os.path.join(base, "*HD*.csv")))
        if not hd_candidates:
            raise FileNotFoundError(f"No Hubble diagram CSV found under {base}")
        self.hd_path = hd_candidates[0]

        statsys_candidates = sorted(glob.glob(os.path.join(base, "STAT+SYS*.npz")))
        statonly_candidates = sorted(glob.glob(os.path.join(base, "STATONLY*.npz")))

        if statsys_candidates:
            self.icov_path = statsys_candidates[0]
        elif statonly_candidates:
            self.icov_path = statonly_candidates[0]
        else:
            raise FileNotFoundError(
                f"No covariance npz found under {base}. Expected STAT+SYS.npz or STATONLY.npz"
            )

        self._load_data()

    def _load_data(self):
        # Important: skip comment lines beginning with '#'
        df = pd.read_csv(self.hd_path, sep=r'\s+', comment="#")
        required_cols = {"zHD", "MU"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(
                f"Missing required DESY5 columns {missing} in {self.hd_path}. "
                f"Available columns: {list(df.columns)}"
            )

        self.z = df['zHD'].to_numpy(dtype=float)
        self.mu_data = df['MU'].to_numpy(dtype=float)
        self.n = len(self.z)

        self.Cinv = _load_inverse_covariance(self.icov_path)

        if self.Cinv.shape != (self.n, self.n):
            raise ValueError(
                f"Inverse covariance shape {self.Cinv.shape} does not match number of SNe ({self.n})"
            )

    def get_requirements(self):
        return {"luminosity_distance": {"z": self.z}}

    def logp(self, **params_values):
        Dl = self.provider.get_luminosity_distance(self.z)  # Mpc
        mu_cosmo = 5.0 * np.log10(Dl) + 25.0

        M_B = params_values.get("M_B", 0.0)
        mu_model = mu_cosmo + M_B

        delta = self.mu_data - mu_model
        chi2 = float(delta @ self.Cinv @ delta)
        if np.random.rand() < 0.001: # Prints ~1% of the time
             print(f"chi2 = {chi2}, CHECK: z={self.z[0]:.3f}, Dl={Dl[0]:.2f} Mpc, mu_cosmo={5*np.log10(Dl[0])+25:.2f}")

        return -0.5 * chi2
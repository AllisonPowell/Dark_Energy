import numpy as np
from cobaya.theory import Theory
from cobaya.conventions import Const

from model.params import ModelParams
from model.background import integrate_background
from model.observables import build_distance_tables
from model.derived import derived_quantities
from model.utils import validate_physical_region


class LinearPotentialTheory(Theory):
    params = {
        "h": None,
        "Omega_m": None,
        "V0": None,
        "V1": None,
        "M_B": None,
        "rdrag": None,
    }

    def initialize(self):
        pass

    def get_requirements(self):
        return {}

    def get_can_provide(self):
        return [
            "angular_diameter_distance",
            "luminosity_distance",
            "Hubble",
        ]

    def get_can_provide_params(self):
        return ["w0", "kin0", "rho_phi0"]

    def calculate(self, state, want_derived=True, **params_values_dict):
        p = ModelParams(**params_values_dict)

        ok, msg = validate_physical_region(p)
        if not ok:
            #raise RuntimeError(msg)
            print(msg)

        bg = integrate_background(p, z_max=3.0, npts=2000)
        dist = build_distance_tables(bg, p.h)
        der = derived_quantities(bg, p)

        state["bg"] = bg
        state["dist"] = dist
        state["derived_scalar"] = der

        if want_derived:
            z = np.asarray(bg["z"])
            i0 = np.argmin(np.abs(z))

            state["derived"] = {
                "w0": float(der["w_phi"][i0]),
                "kin0": float(der["kinetic"][i0]),
                "rho_phi0": float(der["rho_phi"][i0]),
            }

    def get_angular_diameter_distance(self, z):
        z = np.atleast_1d(z)
        Dm = self.current_state["dist"]["interp_Dm"](z)
        Da = Dm / (1.0 + z)
        return np.atleast_1d(Da)

    def get_luminosity_distance(self, z):
        z = np.atleast_1d(z)
        Dl = self.current_state["dist"]["interp_Dl"](z)
        return np.atleast_1d(Dl)

    def get_Hubble(self, z, units):
        z = np.atleast_1d(z)
        H_km_s_Mpc = self.current_state["dist"]["interp_H"](z)

        if units in [None, "km/s/Mpc"]:
            return np.atleast_1d(H_km_s_Mpc)

        if units == "1/Mpc":
            return np.atleast_1d(H_km_s_Mpc / Const.c_km_s)

        raise ValueError(f"Unsupported Hubble units requested: {units}")
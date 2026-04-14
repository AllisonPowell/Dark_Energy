import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.interpolate import interp1d

C_LIGHT = 299792.458  # km/s


def H0_km_s_Mpc(h):
    return 100.0 * h


def build_distance_tables(bg, h):
    """
    Build interpolation tables for cosmological distances from the
    background solution returned by integrate_background().

    Parameters
    ----------
    bg : dict
        Must contain arrays:
          - "z"
          - "E"
        where E(z) = H(z)/H0.
    h : float
        Dimensionless Hubble parameter, H0 = 100 h km/s/Mpc.

    Returns
    -------
    dict
        Contains arrays and interpolation functions for:
          - H(z)
          - Dc(z)
          - Dm(z)
          - Dl(z)
          - Dh(z)
    """
    z = np.asarray(bg["z"])
    E = np.asarray(bg["E"])

    # Make sure z is increasing for interpolation/integration
    order = np.argsort(z)
    z = z[order]
    E = E[order]

    H0 = H0_km_s_Mpc(h)
    H = H0 * E

    invH = 1.0 / H

    # Comoving radial distance in Mpc
    Dc = C_LIGHT * cumulative_trapezoid(invH, z, initial=0.0)

    # Flat cosmology
    Dm = Dc

    # Luminosity distance
    Dl = (1.0 + z) * Dm

    # Hubble distance
    Dh = C_LIGHT / H

    return {
        "z": z,
        "H": H,
        "Dc": Dc,
        "Dm": Dm,
        "Dl": Dl,
        "Dh": Dh,
        "interp_H": interp1d(z, H, kind="cubic", bounds_error=False, fill_value="extrapolate"),
        "interp_Dc": interp1d(z, Dc, kind="cubic", bounds_error=False, fill_value="extrapolate"),
        "interp_Dm": interp1d(z, Dm, kind="cubic", bounds_error=False, fill_value="extrapolate"),
        "interp_Dl": interp1d(z, Dl, kind="cubic", bounds_error=False, fill_value="extrapolate"),
        "interp_Dh": interp1d(z, Dh, kind="cubic", bounds_error=False, fill_value="extrapolate"),
    }


def luminosity_distance(z, dist):
    """
    Convenience wrapper: return D_L(z) in Mpc from distance table dict.
    """
    return dist["interp_Dl"](z)


def hubble_distance(z, dist):
    """
    Convenience wrapper: return D_H(z) = c / H(z) in Mpc.
    """
    return dist["interp_Dh"](z)


def transverse_comoving_distance(z, dist):
    """
    Convenience wrapper: return D_M(z) in Mpc.
    """
    return dist["interp_Dm"](z)


def distance_modulus(Dl_Mpc, M_B_offset=0.0):
    """
    Standard distance modulus from luminosity distance in Mpc.
    """
    return 5.0 * np.log10(np.asarray(Dl_Mpc)) + 25.0 + M_B_offset


def bao_predictions(zvals, dist, rdrag):
    """
    Common BAO observables.
    """
    zvals = np.asarray(zvals)
    Dm = dist["interp_Dm"](zvals)
    Dh = dist["interp_Dh"](zvals)
    return {
        "Dm_over_rd": Dm / rdrag,
        "Dh_over_rd": Dh / rdrag,
    }
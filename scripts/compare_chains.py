import glob
import os
import pandas as pd
import numpy as np


def load_chain_metadata(root: str) -> pd.DataFrame:
    param_file = root + ".1.txt"
    if not os.path.exists(param_file):
        raise FileNotFoundError(f"Missing paramnames file: {param_file}")

    with open(param_file, "r", encoding="utf-8") as f:
        paramnames = [line.split()[0] for line in f if line.strip()]

    cols = ["weight", "minuslogpost"] + paramnames
    

    chain_files = sorted(
        fn for fn in glob.glob(root + "*.txt")
        if not fn.endswith(".progress.txt")
    )
    if not chain_files:
        raise FileNotFoundError(f"No chain files found for root: {root}")

    dfs = [pd.read_csv(fn, sep='\s+', comment="#", names=cols)
           for fn in chain_files]
    return pd.concat(dfs, ignore_index=True)


def load_chain(root: str) -> pd.DataFrame:
    param_file = root + ".1.txt"
    if not os.path.exists(param_file):
        raise FileNotFoundError(f"Missing file: {param_file}")

    # 1. Manually extract the column names from the first line
    with open(param_file, "r", encoding="utf-8") as f:
        first_line = f.readline()
        # Remove the '#' and split into individual column names
        cols = first_line.replace('#', '').split()

    chain_files = sorted(
        fn for fn in glob.glob(root + "*.txt")
        if not fn.endswith(".progress.txt")
    )
    
    # 2. Use 'names=cols' and skip the header line (skiprows=1)
    # This prevents Pandas from ignoring the header line via the 'comment' flag
    dfs = [pd.read_csv(fn, sep=r'\s+', names=cols, skiprows=1) 
           for fn in chain_files]
    
    return pd.concat(dfs, ignore_index=True)


def best_row(chain: pd.DataFrame) -> pd.Series:
    return chain.loc[chain["minuslogpost"].idxmin()]


def best_chi2_old(chain: pd.DataFrame):
    row = best_row(chain)
    chi2_cols = [c for c in chain.columns if c.startswith("chi2__")]

    if chi2_cols:
        parts = {c: float(row[c]) for c in chi2_cols}
        total = sum(parts.values())
    else:
        parts = {"chi2_eff": float(2.0 * row["minuslogpost"])}
        total = parts["chi2_eff"]

    return total, parts, row

def best_chi2(chain: pd.DataFrame):
    row = best_row(chain)
    chi2_cols = [c for c in chain.columns if c.startswith("chi2__")]

    # Drop aggregate duplicates like chi2__BAO when a more specific BAO term exists
    filtered = []
    for c in chi2_cols:
        if c == "chi2__BAO" and any(x.startswith("chi2__bao.") for x in chi2_cols):
            continue
        filtered.append(c)

    if filtered:
        parts = {c: float(row[c]) for c in filtered}
        total = sum(parts.values())
    else:
        parts = {"chi2_eff": float(2.0 * row["minuslogpost"])}
        total = parts["chi2_eff"]

    return total, parts, row

def p_v1_positive(chain: pd.DataFrame):
    if "V1" not in chain.columns:
        return np.nan
    w = chain["weight"].to_numpy(dtype=float)
    v1 = chain["V1"].to_numpy(dtype=float)
    return float(w[v1 > 0].sum() / w.sum())


def p_v1_nonpositive(chain):
    w = chain["weight"].to_numpy(dtype=float)
    v1 = chain["V1"].to_numpy(dtype=float)
    return float(w[v1 <= 0].sum() / w.sum())

def report(dynamic_root: str, lcdm_root: str, label: str):
    dyn_chain = load_chain(dynamic_root)
    lcdm_chain = load_chain(lcdm_root)

    dyn_chi2, dyn_parts, dyn_best = best_chi2(dyn_chain)
    lcdm_chi2, lcdm_parts, lcdm_best = best_chi2(lcdm_chain)

    delta = dyn_chi2 - lcdm_chi2
    pv1 = p_v1_positive(dyn_chain)

    print("\n" + "=" * 70)
    print(label.upper())
    print("=" * 70)

    print("\nDynamic model:")
    print(f"  best chi2      = {dyn_chi2:.6f}")
    print(f"  P(V1 > 0)      = {pv1:.9f}")
    print("  best params:")
    for p in ["h", "Omega_m", "V0", "V1", "M_B", "rdrag"]:
        if p in dyn_best.index:
            print(f"    {p:8s} = {dyn_best[p]:.6f}")
    print("  chi2 parts:")
    for k, v in dyn_parts.items():
        print(f"    {k:12s} = {v:.6f}")

    print("\nLCDM comparison:")
    print(f"  best chi2      = {lcdm_chi2:.6f}")
    print("  best params:")
    for p in ["h", "Omega_m", "V0", "M_B", "rdrag"]:
        if p in lcdm_best.index:
            print(f"    {p:8s} = {lcdm_best[p]:.6f}")
    print("  chi2 parts:")
    for k, v in lcdm_parts.items():
        print(f"    {k:12s} = {v:.6f}")

    print("\nComparison:")
    print(f"  Δχ² = χ²_dynamic - χ²_LCDM = {delta:.6f}")
    if delta < 0:
        print("  -> dynamic model fits better")
    elif delta > 0:
        print("  -> LCDM fits better")
    else:
        print("  -> equal best sampled chi2")

    if abs(delta) < 2:
        print("  Interpretation: weak difference")
    elif abs(delta) < 6:
        print("  Interpretation: moderate difference")
    else:
        print("  Interpretation: strong difference")


    mask = dyn_chain["V1"] <= 0
    print("rows with V1 <= 0:", int(mask.sum()))
    print("weighted mass V1 <= 0:", dyn_chain.loc[mask, "weight"].sum())

    p_pos = p_v1_positive(dyn_chain)
    p_neg = p_v1_nonpositive(dyn_chain)
    print(f"P(V1 > 0)  = {p_pos:.12f}")
    print(f"P(V1 <= 0) = {p_neg:.3e}")
    print("min V1 sampled:", dyn_chain["V1"].min())
    print("1% quantile V1:", dyn_chain["V1"].quantile(0.01))
    print("0.1% quantile V1:", dyn_chain["V1"].quantile(0.001))
    w = dyn_chain["weight"].to_numpy(float)
    neff = (w.sum()**2) / (w**2).sum()
    print("N_eff ~", neff)

if __name__ == "__main__":
    report(
        dynamic_root="outputs/linear_potential_bao_pantheon_sh0es_repro",
        lcdm_root="outputs/lcdm_bao_pantheon_sh0es_repro",
        label="Pantheon+ BAO"
    )

    report(
        dynamic_root="outputs/linear_potential_bao_desy5",
        lcdm_root="outputs/lcdm_bao_desy5",
        label="DESY5 BAO"
    )
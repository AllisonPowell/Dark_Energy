import os
import argparse
import numpy as np
import matplotlib.pyplot as plt
from getdist import loadMCSamples, plots


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def posterior_fraction_positive(samples, param_name="V1"):
    names = samples.getParamNames().list()
    idx = names.index(param_name)
    arr = samples.samples[:, idx]
    wts = samples.weights if samples.weights is not None else np.ones(len(arr))
    frac = np.sum(wts[arr > 0]) / np.sum(wts)
    return float(frac)


def get_param_array(samples, param_name="V1"):
    names = samples.getParamNames().list()
    idx = names.index(param_name)
    arr = samples.samples[:, idx]
    wts = samples.weights if samples.weights is not None else np.ones(len(arr))
    return np.asarray(arr), np.asarray(wts)


def weighted_quantile(values, quantiles, sample_weight=None):
    values = np.asarray(values)
    quantiles = np.atleast_1d(quantiles)

    if sample_weight is None:
        sample_weight = np.ones(len(values))
    sample_weight = np.asarray(sample_weight)

    sorter = np.argsort(values)
    values = values[sorter]
    sample_weight = sample_weight[sorter]
    cdf = np.cumsum(sample_weight) / np.sum(sample_weight)

    return np.interp(quantiles, cdf, values)


def make_triangle(root, outdir, label, color="navy"):
    samples = loadMCSamples(root)

    g = plots.get_subplot_plotter()
    g.settings.alpha_filled_add = 0.4
    g.triangle_plot(
        [samples],
        ["h", "Omega_m", "V0", "V1"],
        filled=True,
        contour_colors=[color],
    )

    plt.suptitle(f"{label}: h, Ωm, V0, V1", y=1.02)
    outfile = os.path.join(outdir, f"{label}_triangle.png")
    plt.savefig(outfile, dpi=220, bbox_inches="tight")
    plt.close()
    return outfile


def make_v0_v1(root, outdir, label, color="royalblue"):
    samples = loadMCSamples(root)

    frac_pos = posterior_fraction_positive(samples, "V1")

    g = plots.get_single_plotter()
    g.plot_2d(
        [samples],
        "V0",
        "V1",
        filled=True,
        contour_colors=[color],
    )

    ax = plt.gca()
    ax.axhline(0.0, color="black", linestyle="--", linewidth=1.2)
    ax.set_xlabel(r"$V_0$")
    ax.set_ylabel(r"$V_1$")
    ax.set_title(f"{label}\nSampled posterior support at $V_1>0$: {frac_pos:.4f}")

    outfile = os.path.join(outdir, f"{label}_V0_V1.png")
    plt.savefig(outfile, dpi=220, bbox_inches="tight")
    plt.close()
    return outfile, frac_pos


def make_overlay(root1, root2, outdir, label1="pantheon", label2="desy5"):
    s1 = loadMCSamples(root1)
    s2 = loadMCSamples(root2)

    f1 = posterior_fraction_positive(s1, "V1")
    f2 = posterior_fraction_positive(s2, "V1")

    g = plots.get_single_plotter()
    g.plot_2d(
        [s1, s2],
        "V0",
        "V1",
        filled=False,
        contour_colors=["black", "red"],
        legend_labels=[
            f"{label1} (V1>0: {f1:.4f})",
            f"{label2} (V1>0: {f2:.4f})",
        ],
    )

    ax = plt.gca()
    ax.axhline(0.0, color="black", linestyle="--", linewidth=1.2)
    ax.set_xlabel(r"$V_0$")
    ax.set_ylabel(r"$V_1$")
    ax.set_title("Overlay: $V_0$-$V_1$ constraints")

    outfile = os.path.join(outdir, "overlay_V0_V1.png")
    plt.savefig(outfile, dpi=220, bbox_inches="tight")
    plt.close()
    return outfile


def make_overlay_zoom(root1, root2, outdir, label1="pantheon", label2="desy5",
                      ymin=-0.05, ymax=0.8):
    s1 = loadMCSamples(root1)
    s2 = loadMCSamples(root2)

    g = plots.get_single_plotter()
    g.plot_2d(
        [s1, s2],
        "V0",
        "V1",
        filled=False,
        contour_colors=["black", "red"],
        legend_labels=[label1, label2],
    )

    ax = plt.gca()
    ax.axhline(0.0, color="black", linestyle="--", linewidth=1.2)
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel(r"$V_0$")
    ax.set_ylabel(r"$V_1$")
    ax.set_title("Zoom near $V_1 = 0$")

    outfile = os.path.join(outdir, "overlay_V0_V1_zoom.png")
    plt.savefig(outfile, dpi=220, bbox_inches="tight")
    plt.close()
    return outfile


def make_v1_1d(root, outdir, label, color="deeppink"):
    samples = loadMCSamples(root)
    v1, w = get_param_array(samples, "V1")

    v1_min = np.min(v1)
    q001, q01, q05 = weighted_quantile(v1, [0.001, 0.01, 0.05], w)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(v1, bins=80, weights=w / np.sum(w), color=color, alpha=0.7)
    ax.axvline(0.0, color="black", linestyle="--", linewidth=1.4, label=r"$V_1=0$")
    ax.axvline(v1_min, color="black", linestyle=":", linewidth=1.4, label=f"min = {v1_min:.3f}")
    ax.set_xlabel(r"$V_1$")
    ax.set_ylabel("Posterior mass per bin")
    ax.set_title(
        f"{label}: 1D posterior for $V_1$\n"
        f"0.1% q = {q001:.3f}, 1% q = {q01:.3f}, 5% q = {q05:.3f}"
    )
    ax.legend(frameon=False)

    outfile = os.path.join(outdir, f"{label}_V1_1d.png")
    plt.savefig(outfile, dpi=220, bbox_inches="tight")
    plt.close()
    return outfile


def make_v1_1d_overlay(root1, root2, outdir, label1="pantheon", label2="desy5"):
    s1 = loadMCSamples(root1)
    s2 = loadMCSamples(root2)

    v1_1, w1 = get_param_array(s1, "V1")
    v1_2, w2 = get_param_array(s2, "V1")

    fig, ax = plt.subplots(figsize=(7, 4.5))

    ax.hist(
        v1_1, bins=80, weights=w1 / np.sum(w1),
        histtype="step", linewidth=2.0, color="black", label=label1
    )
    ax.hist(
        v1_2, bins=80, weights=w2 / np.sum(w2),
        histtype="step", linewidth=2.0, color="red", label=label2
    )

    ax.axvline(0.0, color="black", linestyle="--", linewidth=1.4, label=r"$V_1=0$")
    ax.set_xlabel(r"$V_1$")
    ax.set_ylabel("Posterior mass per bin")
    ax.set_title(r"Overlay: 1D posterior for $V_1$")
    ax.legend(frameon=False)

    outfile = os.path.join(outdir, "overlay_V1_1d.png")
    plt.savefig(outfile, dpi=220, bbox_inches="tight")
    plt.close()
    return outfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pantheon-root", required=True)
    parser.add_argument("--desy5-root", required=True)
    parser.add_argument("--outdir", default="outputs/bonus_plots")
    args = parser.parse_args()

    ensure_dir(args.outdir)

    made = []

    made.append(make_triangle(args.pantheon_root, args.outdir, "pantheon", color="deeppink"))
    made.append(make_triangle(args.desy5_root, args.outdir, "desy5", color="red"))

    p_v0v1, p_frac = make_v0_v1(args.pantheon_root, args.outdir, "pantheon", color="deeppink")
    d_v0v1, d_frac = make_v0_v1(args.desy5_root, args.outdir, "desy5", color="red")
    made.extend([p_v0v1, d_v0v1])

    made.append(make_overlay(args.pantheon_root, args.desy5_root, args.outdir))
    made.append(make_overlay_zoom(args.pantheon_root, args.desy5_root, args.outdir))
    made.append(make_v1_1d(args.pantheon_root, args.outdir, "pantheon", color="deeppink"))
    made.append(make_v1_1d(args.desy5_root, args.outdir, "desy5", color="red"))
    made.append(make_v1_1d_overlay(args.pantheon_root, args.desy5_root, args.outdir))

    print("\nGenerated plot files:")
    for f in made:
        print(f"  {f}")

    print("\nSummary:")
    print(f"  Pantheon sampled posterior support at V1>0: {p_frac:.6f}")
    print(f"  DESY5 sampled posterior support at V1>0:   {d_frac:.6f}")

if __name__ == "__main__":
    main()
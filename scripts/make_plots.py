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
    ax.set_title(f"{label}\nPosterior mass with $V_1>0$: {frac_pos:.4f}")

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
        contour_colors=["deeppink", "royalblue"],
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pantheon-root", required=True)
    parser.add_argument("--desy5-root", required=True)
    parser.add_argument("--outdir", default="outputs/plots")
    args = parser.parse_args()

    ensure_dir(args.outdir)

    made = []

    made.append(make_triangle(args.pantheon_root, args.outdir, "pantheon", color="deeppink"))
    made.append(make_triangle(args.desy5_root, args.outdir, "desy5", color="royalblue"))

    p_v0v1, p_frac = make_v0_v1(args.pantheon_root, args.outdir, "pantheon", color="deeppink")
    d_v0v1, d_frac = make_v0_v1(args.desy5_root, args.outdir, "desy5", color="royalblue")
    made.extend([p_v0v1, d_v0v1])

    made.append(make_overlay(args.pantheon_root, args.desy5_root, args.outdir))

    print("\nGenerated plot files:")
    for f in made:
        print(f"  {f}")

    print("\nSummary:")
    print(f"  Pantheon+ posterior mass with V1>0: {p_frac:.6f}")
    print(f"  DESY5 posterior mass with V1>0:     {d_frac:.6f}")


if __name__ == "__main__":
    main()
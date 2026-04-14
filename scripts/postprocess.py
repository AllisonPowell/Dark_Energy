from getdist import loadMCSamples, plots
import matplotlib.pyplot as plt
import sys

root = sys.argv[1]
g = plots.get_subplot_plotter()
samples = loadMCSamples(root)
g.triangle_plot(samples, ["Omega_m", "V0", "V1", "h"], filled=True)
plt.savefig(root + "_triangle.png", dpi=180, bbox_inches="tight")
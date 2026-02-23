# Scientific Computing Exercise Set #1
Vibrating string (1D wave equation) and time-dependent diffusion (2D diffusion + steady-state Laplace solvers).

This repository contains the notebooks used to generate the results and figures for the report.

## Repository contents
- `1.1.ipynb` – Tasks A–C: 1D wave equation (snapshots + animation)
- `1.2.ipynb` – Tasks D–G: 2D diffusion (heatmaps + transient profiles vs analytic)
- `methods.ipynb` – Tasks H–L: steady-state solvers (Jacobi/GS/SOR) + internal objects (sink/insulator)

## Quickstart (Conda)
```bash
# clone
git clone https://github.com/TimonJasarevic/SC_Assignments
cd SC_Assignments

# create and activate environment
conda env create -f environment.yml
conda activate sc-ex1

# run notebooks
jupyter lab
```

## Reproducing results (notebooks)
Open the notebooks in the order below and run **Restart Kernel & Run All**:

1. `1.1.ipynb` (Tasks A–C)
2. `1.2.ipynb` (Tasks D–G)
3. `methods.ipynb` (Tasks H–L)

### Figure mapping (report)
The exact figure filenames in the LaTeX report are produced by exporting the corresponding notebook outputs:
- **Wave snapshots**: `1.1.ipynb` (Tasks A–B)  
- **Wave animation**: `1.1.ipynb` (Task C)  
- **Diffusion transient profiles vs analytic**: `1.2.ipynb` (Task E)  
- **Diffusion heatmap snapshots**: `1.2.ipynb` (Task F)  
- **Convergence comparison (Jacobi vs GS vs SOR)**: `methods.ipynb` (Tasks H–I)  
- **SOR omega sweep / optimal omega**: `methods.ipynb` (Task J)  
- **Internal objects (sink / insulator)**: `methods.ipynb` (Tasks K–L)

> Note: The notebooks currently display figures inline. If you want the repo to auto-save PNGs with fixed names (for LaTeX),
add `plt.savefig("...png", dpi=300, bbox_inches="tight")` in the plotting cells.

## Determinism
No random components are used in the simulations. Results are deterministic given the package versions in `environment.yml`.

## Environment
The conda environment is specified in `environment.yml` (Python, NumPy, SciPy, Matplotlib, Numba, and Jupyter).

## Hardware
All experiments run on a standard CPU, no GPU required.
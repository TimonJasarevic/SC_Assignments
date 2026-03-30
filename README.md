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
conda activate sc-

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

# Scientific Computing Exercise Set #2
Dielectric Breakdown Model (DBM), Monte Carlo Diffusion-Limited Aggregation (DLA), and Gray-Scott reaction-diffusion.

This repository contains the notebooks used to generate the results and figures for the report.

## Repository contents
- `GM_DLA.ipynb` - Tasks A-B: Laplacian growth / DBM, SOR optimization, and vectorized Red-Black SOR benchmarking
- `MC_DLA.ipynb` - Tasks C-D: Monte Carlo DLA and sticking probability experiments
- `GS_DLA.ipynb` - Task E: Gray-Scott reaction-diffusion parameter sweep

## Quickstart (Conda)
```bash
# clone
git clone https://github.com/TimonJasarevic/SC_Assignments
cd SC_Assignments

# create and activate environment
conda env create -f environment.yml
conda activate sc-assignments

# run notebooks
jupyter lab
```

## Reproducing results (notebooks)
Open the notebooks in the order below and run Restart Kernel & Run All:

1. `GM_DLA.ipynb` (Tasks A-B)
2. `MC_DLA.ipynb` (Tasks C-D)
3. `GS_DLA.ipynb` (Task E)

## Figure mapping (report)
The exact figures in the LaTeX report are produced by the following notebooks:
- Laplacian growth clusters for different eta: `GM_DLA.ipynb` (Task A)
- SOR performance vs omega: `GM_DLA.ipynb` (Task A)
- Sequential vs vectorized Red-Black SOR timing comparison: `GM_DLA.ipynb` (Task B)
- Monte Carlo DLA cluster snapshot: `MC_DLA.ipynb` (Task C)
- Sticking probability p_s vs particles needed to reach the top: `MC_DLA.ipynb` (Task D)
- Gray-Scott final V-concentration plots for several (f, k) values: `GS_DLA.ipynb` (Task E)

Note: The notebooks currently display figures inline. If you want the repo to auto-save PNGs with fixed names for LaTeX, add `plt.savefig("...png", dpi=300, bbox_inches="tight")` in the plotting cells.

## Determinism
The DBM and Monte Carlo DLA notebooks contain stochastic components. Fixed random seeds are used in the reported experiments so results are reproducible for the package versions listed in `environment.yml`. The Gray-Scott simulations also use a fixed seed for the added initial noise.

## Environment
The conda environment is specified in `environment.yml` and includes Python, NumPy, SciPy, Matplotlib, tqdm, and Jupyter.

## Hardware
All experiments run on a standard CPU, no GPU required.

# Scientific Computing Exercise Set #3

Open challenge assignment: Kármán vortex street with three numerical methods, and WiFi router placement using the Helmholtz equation.

This repository contains the code used to generate the results and figures for the report.

## Repository contents

* `Challenge_A.ipynb` - Challenge A: Kármán vortex street using three methods:

  * Finite Difference Method (FDM)
  * Finite Element Method (FEM, using NGSolve)
  * Lattice Boltzmann Method (LBM)
* `Challange_B.py` - Challenge B: WiFi router optimization in a 2D floor plan using a Helmholtz solver with coarse-to-fine search and signal-strength evaluation at the prescribed measurement points

## Quickstart (Conda)

```bash
# clone
git clone https://github.com/TimonJasarevic/SC_Assignments
cd SC_Assignments

# create and activate environment
conda env create -f environment.yml
conda activate sc-assignments

# run notebook / script
jupyter lab
python Challange_B.py
```

## Reproducing results

### Challenge A

Open `Challenge_A.ipynb` and run **Restart Kernel & Run All**.

The notebook contains three sections:

1. **Finite Difference**
2. **Finite Element Method**
3. **LBM**

These correspond directly to the three methods requested in Assignment Set 3 for the Kármán vortex street challenge.

### Challenge B

Run:

```bash
python Challenge_B.py
```

This script:

* builds the room and wall masks
* solves the Helmholtz equation on a Cartesian grid
* evaluates signal strength by averaging in a small disk around the four measurement points
* performs a coarse-to-fine search over router locations
* prints the best router position and per-room scores
* plots the final signal-strength field

## Figure mapping (report)

The main report figures are produced by the following files:

* **Challenge A stability comparison and method experiments**: `Challenge_A.ipynb`
* **WiFi signal strength heatmap / best router location**: `Challange_B.py`
* **Per-room signal strengths and total score**: `Challange_B.py` console output / report tables

## Assignment-specific notes

### Challenge A

Assignment Set 3 asks for the same flow problem to be solved with:

1. finite difference,
2. finite element using NGSolve,
3. lattice Boltzmann,

and compares how high the Reynolds number can go while remaining stable.

### Challenge B

The router optimization challenge uses the scalar Helmholtz equation with:

* Gaussian source amplitude (A = 10^4)
* source width (\sigma = 0.2) m
* air refractive index (1.0)
* wall refractive index (2.5 + 0.5j)
* signal evaluation by averaging in a disk of radius (5) cm around the four measurement locations

The current implementation uses:

* optimization frequency: **0.8 GHz**
* coarse grid spacing: **0.05 m**
* refined grid spacing: **0.0125 m**
* coarse-to-fine router search with local refinement

## Determinism

Challenge A and Challenge B are deterministic for fixed parameter settings. No random components are used in the current WiFi optimization script.

## Environment

The conda environment should include at least:

* Python
* NumPy
* SciPy
* Matplotlib
* Jupyter
* NGSolve / Netgen

## Hardware

All experiments were run on a standard CPU. The WiFi optimization problem becomes computationally expensive at physically realistic WiFi frequencies, which is why motivated approximations and scaled visualization settings are used.

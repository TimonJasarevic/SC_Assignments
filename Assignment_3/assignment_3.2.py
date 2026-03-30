from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import matplotlib.pyplot as plt


@dataclass
class Rect:
    x0: float
    x1: float
    y0: float
    y1: float

    def contains(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        return (x >= self.x0) & (x <= self.x1) & (y >= self.y0) & (y <= self.y1)


class Room:
    def __init__(
        self,
        width: float = 10.0,
        height: float = 8.0,
        dx: float = 0.05,
        wall_thickness: float = 0.15,
    ) -> None:
        self.width = width
        self.height = height
        self.dx = dx
        self.dy = dx
        self.wall_thickness = wall_thickness

        self.measurement_points = {
            "Living room": (1.0, 5.0),
            "Kitchen": (2.0, 1.0),
            "Bathroom": (9.0, 1.0),
            "Bedroom 1": (9.0, 7.0),
        }

        wt = wall_thickness
        hw = wt / 2.0

        self.internal_walls: List[Rect] = [
            Rect(0.0, 3.0, 3.0 - hw, 3.0 + hw),
            Rect(4.0, 6.0, 3.0 - hw, 3.0 + hw),
            Rect(7.0, 10.0, 3.0 - hw, 3.0 + hw),
            Rect(6.0 - hw, 6.0 + hw, 3.0, 8.0),
            Rect(2.5 - hw, 2.5 + hw, 0.0, 2.0),
            Rect(7.0 - hw, 7.0 + hw, 0.0, 1.5),
            Rect(7.0 - hw, 7.0 + hw, 2.5, 3.0),
        ]

        self._build_grid()
        self._build_masks()

    def _build_grid(self) -> None:
        self.x = np.arange(0.0, self.width + 0.5 * self.dx, self.dx)
        self.y = np.arange(0.0, self.height + 0.5 * self.dy, self.dy)
        self.Nx = len(self.x)
        self.Ny = len(self.y)
        self.X, self.Y = np.meshgrid(self.x, self.y, indexing="xy")

    def _build_masks(self) -> None:
        wall_mask = np.zeros((self.Ny, self.Nx), dtype=bool)
        for rect in self.internal_walls:
            wall_mask |= rect.contains(self.X, self.Y)

        self.wall_mask = wall_mask
        self.air_mask = ~wall_mask

        self.boundary_mask = np.zeros((self.Ny, self.Nx), dtype=bool)
        self.boundary_mask[0, :] = True
        self.boundary_mask[-1, :] = True
        self.boundary_mask[:, 0] = True
        self.boundary_mask[:, -1] = True

    def refine(self, new_dx: float) -> "Room":
        return Room(
            width=self.width,
            height=self.height,
            dx=new_dx,
            wall_thickness=self.wall_thickness,
        )

    def valid_router_mask(self, min_dist_to_measurements: float = 0.5) -> np.ndarray:
        valid = self.air_mask.copy()
        valid[self.boundary_mask] = False

        for _, (x, y) in self.measurement_points.items():
            dist = np.sqrt((self.X - x) ** 2 + (self.Y - y) ** 2)
            valid &= dist >= min_dist_to_measurements

        return valid

    def candidate_points(
        self,
        stride: int = 1,
        min_dist_to_measurements: float = 0.5,
    ) -> List[tuple[int, int]]:
        valid = self.valid_router_mask(min_dist_to_measurements=min_dist_to_measurements)
        pts: List[tuple[int, int]] = []

        for j in range(0, self.Ny, stride):
            for i in range(0, self.Nx, stride):
                if valid[j, i]:
                    pts.append((j, i))

        return pts

    def plot_geometry(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        if ax is None:
            _, ax = plt.subplots(figsize=(8, 6))

        img = np.zeros((self.Ny, self.Nx))
        img[self.wall_mask] = 1.0

        ax.imshow(
            img,
            origin="lower",
            extent=[0, self.width, 0, self.height],
            cmap="Greys",
            alpha=0.7,
            aspect="equal",
        )

        for name, (x, y) in self.measurement_points.items():
            ax.plot(x, y, "bo", ms=5)
            ax.text(x + 0.08, y + 0.08, name, fontsize=8)

        ax.set_title("Room geometry")
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")
        return ax


class HelmholtzSolver:
    c0 = 3e8

    def __init__(
        self,
        room: Room,
        frequency_hz: float = 1e8,
        source_amplitude: float = 1e4,
        source_sigma: float = 0.2,
        n_air: complex = 1.0 + 0.0j,
        n_wall: complex = 2.5 + 0.5j,
    ) -> None:
        self.room = room
        self.frequency_hz = frequency_hz
        self.source_amplitude = source_amplitude
        self.source_sigma = source_sigma
        self.n_air = n_air
        self.n_wall = n_wall

        self.k0 = 2.0 * np.pi * self.frequency_hz / self.c0
        self.n_grid = np.where(room.wall_mask, self.n_wall, self.n_air)
        self.k_grid = self.k0 * self.n_grid

    def idx(self, j: int, i: int) -> int:
        return j * self.room.Nx + i

    def _connected_air_mask_from_source(
        self,
        xr: float,
        yr: float,
        max_radius_sigma: float = 3.0,
    ) -> np.ndarray:
        i0 = int(np.argmin(np.abs(self.room.x - xr)))
        j0 = int(np.argmin(np.abs(self.room.y - yr)))

        connected = np.zeros((self.room.Ny, self.room.Nx), dtype=bool)

        if not self.room.air_mask[j0, i0]:
            return connected

        max_radius = max_radius_sigma * self.source_sigma
        max_radius2 = max_radius ** 2

        stack = [(j0, i0)]
        connected[j0, i0] = True

        while stack:
            j, i = stack.pop()

            for dj, di in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                jn = j + dj
                in_ = i + di

                if jn < 0 or jn >= self.room.Ny or in_ < 0 or in_ >= self.room.Nx:
                    continue

                if connected[jn, in_]:
                    continue

                if not self.room.air_mask[jn, in_]:
                    continue

                dx = self.room.X[jn, in_] - xr
                dy = self.room.Y[jn, in_] - yr
                if dx * dx + dy * dy > max_radius2:
                    continue

                connected[jn, in_] = True
                stack.append((jn, in_))

        return connected

    def build_source(self, xr: float, yr: float) -> np.ndarray:
        sigma2 = self.source_sigma ** 2
        f = self.source_amplitude * np.exp(
            -((self.room.X - xr) ** 2 + (self.room.Y - yr) ** 2) / (2.0 * sigma2)
        )

        connected_air = self._connected_air_mask_from_source(xr, yr, max_radius_sigma=3.0)
        f = np.where(connected_air, f, 0.0)

        return f.astype(np.complex128)

    def assemble_system(self, source: np.ndarray) -> tuple[sp.csr_matrix, np.ndarray]:
        Nx, Ny = self.room.Nx, self.room.Ny
        h = self.room.dx
        N = Nx * Ny

        A = sp.lil_matrix((N, N), dtype=np.complex128)
        b = np.zeros(N, dtype=np.complex128)

        for j in range(Ny):
            for i in range(Nx):
                p = self.idx(j, i)
                kij = self.k_grid[j, i]

                if j == 0:
                    A[p, self.idx(j, i)] = -(1.0 / h) + 1j * kij
                    A[p, self.idx(j + 1, i)] = 1.0 / h
                    continue

                if j == Ny - 1:
                    A[p, self.idx(j - 1, i)] = -1.0 / h
                    A[p, self.idx(j, i)] = (1.0 / h) - 1j * kij
                    continue

                if i == 0:
                    A[p, self.idx(j, i)] = -(1.0 / h) + 1j * kij
                    A[p, self.idx(j, i + 1)] = 1.0 / h
                    continue

                if i == Nx - 1:
                    A[p, self.idx(j, i - 1)] = -1.0 / h
                    A[p, self.idx(j, i)] = (1.0 / h) - 1j * kij
                    continue

                A[p, self.idx(j, i)] = (-4.0 / h**2) + kij**2
                A[p, self.idx(j, i - 1)] = 1.0 / h**2
                A[p, self.idx(j, i + 1)] = 1.0 / h**2
                A[p, self.idx(j - 1, i)] = 1.0 / h**2
                A[p, self.idx(j + 1, i)] = 1.0 / h**2
                b[p] = source[j, i]

        return A.tocsr(), b

    def solve(self, xr: float, yr: float) -> np.ndarray:
        source = self.build_source(xr, yr)
        A, b = self.assemble_system(source)
        u = spla.spsolve(A, b)
        return u.reshape((self.room.Ny, self.room.Nx))

    def average_signal_in_disk(
        self,
        signal: np.ndarray,
        xc: float,
        yc: float,
        radius: float = 0.05,
    ) -> float:
        dist = np.sqrt((self.room.X - xc) ** 2 + (self.room.Y - yc) ** 2)
        mask = dist <= radius

        if not np.any(mask):
            i = np.argmin(np.abs(self.room.x - xc))
            j = np.argmin(np.abs(self.room.y - yc))
            return float(signal[j, i])

        return float(np.mean(signal[mask]))

    def score_measurement_points(
        self,
        u: np.ndarray,
        radius: float = 0.05,
    ) -> tuple[dict, float]:
        signal = np.abs(u)
        scores = {}
        total = 0.0

        for name, (x, y) in self.room.measurement_points.items():
            s = self.average_signal_in_disk(signal, x, y, radius=radius)
            scores[name] = s
            total += s

        return scores, total


class RouterOptimizer:
    def __init__(self, room: Room, solver: HelmholtzSolver) -> None:
        self.room = room
        self.solver = solver

    def evaluate_candidates(
        self,
        candidates: List[tuple[int, int]],
        radius: float = 0.05,
        verbose_every: int = 10,
    ) -> List[dict]:
        results: List[dict] = []

        for idx, (j, i) in enumerate(candidates, start=1):
            xr = self.room.x[i]
            yr = self.room.y[j]

            u = self.solver.solve(xr, yr)
            scores, total = self.solver.score_measurement_points(u, radius=radius)

            results.append(
                {
                    "i": i,
                    "j": j,
                    "x": xr,
                    "y": yr,
                    "u": u,
                    "scores": scores,
                    "total": total,
                }
            )

            if verbose_every > 0 and idx % verbose_every == 0:
                print(f"  evaluated {idx}/{len(candidates)} candidates")

        results.sort(key=lambda r: r["total"], reverse=True)
        return results

    def local_neighborhood(
        self,
        center_i: int,
        center_j: int,
        radius_cells: int = 1,
        min_dist_to_measurements: float = 0.5,
    ) -> List[tuple[int, int]]:
        valid = self.room.valid_router_mask(min_dist_to_measurements=min_dist_to_measurements)
        pts: List[tuple[int, int]] = []

        jmin = max(0, center_j - radius_cells)
        jmax = min(self.room.Ny, center_j + radius_cells + 1)
        imin = max(0, center_i - radius_cells)
        imax = min(self.room.Nx, center_i + radius_cells + 1)

        for j in range(jmin, jmax):
            for i in range(imin, imax):
                if valid[j, i]:
                    pts.append((j, i))

        return pts

    def coarse_to_fine_search(
        self,
        coarse_stride: int = 20,
        top_k: int = 3,
        local_radius_cells: int = 1,
        radius: float = 0.05,
        min_dist_to_measurements: float = 0.5,
        refine_dx: Optional[float] = 0.025,
        refine_radius_cells: int = 2,
    ) -> dict:
        print("Stage 1: coarse search")
        coarse_candidates = self.room.candidate_points(
            stride=coarse_stride,
            min_dist_to_measurements=min_dist_to_measurements,
        )
        coarse_results = self.evaluate_candidates(coarse_candidates, radius=radius)

        top = coarse_results[:top_k]
        print("\nTop coarse candidates:")
        for r in top:
            print(f"  ({r['x']:.2f}, {r['y']:.2f})  total={r['total']:.6e}")

        print("\nStage 2: local search")
        local_candidates: List[tuple[int, int]] = []
        seen = set()

        for r in top:
            pts = self.local_neighborhood(
                r["i"],
                r["j"],
                radius_cells=local_radius_cells,
                min_dist_to_measurements=min_dist_to_measurements,
            )
            for pt in pts:
                if pt not in seen:
                    seen.add(pt)
                    local_candidates.append(pt)

        local_results = self.evaluate_candidates(local_candidates, radius=radius, verbose_every=0)
        best = local_results[0]
        best_room = self.room
        best_solver = self.solver
        refined_results = None

        print(f"Best after local search: ({best['x']:.2f}, {best['y']:.2f})  total={best['total']:.6e}")

        if refine_dx is not None and refine_dx < self.room.dx:
            print("\nStage 3: refined-grid search")

            refined_room = self.room.refine(refine_dx)
            refined_solver = HelmholtzSolver(
                refined_room,
                frequency_hz=self.solver.frequency_hz,
                source_amplitude=self.solver.source_amplitude,
                source_sigma=self.solver.source_sigma,
                n_air=self.solver.n_air,
                n_wall=self.solver.n_wall,
            )
            refined_optimizer = RouterOptimizer(refined_room, refined_solver)

            i0 = int(np.argmin(np.abs(refined_room.x - best["x"])))
            j0 = int(np.argmin(np.abs(refined_room.y - best["y"])))

            refined_candidates = refined_optimizer.local_neighborhood(
                i0,
                j0,
                radius_cells=refine_radius_cells,
                min_dist_to_measurements=min_dist_to_measurements,
            )

            refined_results = refined_optimizer.evaluate_candidates(
                refined_candidates,
                radius=radius,
                verbose_every=0,
            )

            best = refined_results[0]
            best_room = refined_room
            best_solver = refined_solver

            print(f"Best after refined search: ({best['x']:.2f}, {best['y']:.2f})  total={best['total']:.6e}")

        return {
            "best": best,
            "room": best_room,
            "solver": best_solver,
            "coarse_results": coarse_results,
            "local_results": local_results,
            "refined_results": refined_results,
        }


def plot_field(room: Room, u: np.ndarray, xr: float, yr: float, title: str = "WiFi signal coverage") -> None:
    signal_db = 20 * np.log10(np.abs(u) + 1e-12)

    fig, ax = plt.subplots(figsize=(9, 6))

    im = ax.imshow(
        signal_db,
        origin="lower",
        extent=[0, room.width, 0, room.height],
        cmap="jet",
        aspect="equal",
        vmin=-40,
        vmax=0,
    )
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Signal strength [dB]")

    wall_overlay = np.ma.masked_where(~room.wall_mask, room.wall_mask.astype(float))
    ax.imshow(
        wall_overlay,
        origin="lower",
        extent=[0, room.width, 0, room.height],
        cmap="gray",
        alpha=0.35,
        aspect="equal",
    )

    for name, (x, y) in room.measurement_points.items():
        ax.plot(x, y, "wo", ms=5, markeredgecolor="k")
        ax.text(
            x + 0.08,
            y + 0.08,
            name,
            fontsize=8,
            color="w",
            bbox=dict(boxstyle="round,pad=0.15", fc="k", alpha=0.5),
        )

    ax.plot(xr, yr, "w*", ms=14, markeredgecolor="k", label=f"Router ({xr:.2f}, {yr:.2f})")
    ax.legend(loc="upper right")

    ax.set_title(title)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_xlim(0, room.width)
    ax.set_ylim(0, room.height)
    plt.tight_layout()
    plt.show()
    


def main() -> None:
    room = Room(dx=0.05)
    solver = HelmholtzSolver(
        room,
        frequency_hz=0.8e9,
        source_amplitude=1e4,
        source_sigma=0.2,
    )

    optimizer = RouterOptimizer(room, solver)
    result = optimizer.coarse_to_fine_search(
        coarse_stride=8,
        top_k=3,
        local_radius_cells=2,
        radius=0.05,
        min_dist_to_measurements=0.5,
        refine_dx=0.0125,
        refine_radius_cells=2,
    )

    best = result["best"]
    best_room = result["room"]

    print("\nBest router position")
    print("--------------------")
    print(f"x = {best['x']:.4f} m")
    print(f"y = {best['y']:.4f} m")
    print(f"total score = {best['total']:.8e}")
    print("per-room scores:")
    for name, value in best["scores"].items():
        print(f"  {name:12s}: {value:.8e}")

    plot_field(
        best_room,
        best["u"],
        best["x"],
        best["y"],
        title=f"Best router position: ({best['x']:.2f}, {best['y']:.2f})",
    )


if __name__ == "__main__":
    main()  
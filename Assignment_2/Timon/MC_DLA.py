import numpy as np
from enum import Enum
import matplotlib.pyplot as plt


class Tile_Type(Enum):
    EMPTY_CELL = 0
    CLUSTER = 1
    CLUSTER_NEIGHBOUR = 2

class MC_Grid():
    def __init__(self, grid_size, sticking_prob):
        self.grid_size = grid_size
        self.sticking_prob = sticking_prob

        self.grid = np.zeros((grid_size, grid_size), dtype=np.int8)

        # initial seed
        self.grid[0, grid_size // 2] = Tile_Type.CLUSTER.value
        self._set_cluster_neighbours(grid_size // 2, 0)

        self.walkers = []

    def get_walker_amount(self):
        return len(self.walkers)

    def insert_walker(self):
        start_x = np.random.choice(self.grid_size)
        start_y = self.grid_size - 1
        self.walkers.append((start_x, start_y))

    def _set_cluster_neighbours(self, x_cluster, y_cluster):
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx = (x_cluster + dx) % self.grid_size
            ny = y_cluster + dy

            if 0 <= ny < self.grid_size:
                tile = Tile_Type(int(self.grid[ny, nx]))
                if tile == Tile_Type.EMPTY_CELL:
                    self.grid[ny, nx] = Tile_Type.CLUSTER_NEIGHBOUR.value
        
    def random_walk(self, walker_idx):

        def _set_cluster(x_walker, y_walker):
            self.grid[y_walker, x_walker] = Tile_Type.CLUSTER.value
            self._set_cluster_neighbours(x_cluster=x_walker, y_cluster=y_walker)
            del self.walkers[walker_idx]

        def _random_move_set(x, y, moves=[0,1,2,3]):
            match np.random.choice(moves):
                # LEFT MOVE
                case 0:
                    x -= 1
                # RIGHT MOVE
                case 1:
                    x += 1
                # DOWN MOVE
                case 2:
                    y -= 1
                # UP MOVE
                case 3:
                    y += 1
            return x, y

        (x_walker, y_walker) = self.walkers[walker_idx]

        x_next, y_next = _random_move_set(x=x_walker, y=y_walker, moves=[0,1,2,3])

        # x-axis boundary wrapping
        if x_next == -1 or x_next == self.grid_size:
            x_next %= self.grid_size
        
        # y-axis boundary control
        if y_next == -1 or y_next == self.grid_size:
            del self.walkers[walker_idx]
            return
        
        match Tile_Type(int(self.grid[y_next, x_next])):
            case Tile_Type.EMPTY_CELL:
                self.walkers[walker_idx] = (x_next, y_next)
            case Tile_Type.CLUSTER:
                return
            case Tile_Type.CLUSTER_NEIGHBOUR:
                if np.random.random() < self.sticking_prob:
                    _set_cluster(x_next, y_next)
                    return
                self.walkers[walker_idx] = (x_next, y_next)
    

    def show(self, show_walkers=True):
        plt.figure()
        plt.imshow(self.grid, origin="lower", interpolation="nearest")
        if show_walkers and self.walkers:
            xs, ys = zip(*self.walkers)
            plt.scatter(xs, ys, s=10)
            plt.xlim(-0.5, self.grid_size - 0.5)
            plt.ylim(-0.5, self.grid_size - 0.5)
        else:
            plt.xlim(-0.5, self.grid_size - 0.5)
            plt.ylim(-0.5, self.grid_size - 0.5)

        plt.colorbar(label="Tile type (0 empty, 1 cluster, 2 neighbour)")
        plt.title("MC Grid")
        plt.xlabel("x")
        plt.ylabel("y")
        plt.show()


def main():
    np.random.seed(0)

    grid_size = 10
    g = MC_Grid(grid_size, sticking_prob=1)

    n_steps = 5000000
    insert_every = 2
    show_every = 1

    plt.ion()
    fig, ax = plt.subplots()

    im = ax.imshow(g.grid, origin="lower", interpolation="nearest")

    sc = None
    fig.colorbar(im, ax=ax, label="Tile type (0 empty, 1 cluster, 2 neighbour)")
    ax.set_title("MC Grid")
    ax.set_xlabel("x")
    ax.set_ylabel("y")

    ax.set_xlim(-0.5, grid_size - 0.5)
    ax.set_ylim(-0.5, grid_size - 0.5)
    ax.set_aspect("equal", adjustable="box")

    for t in range(n_steps):
        # if t % insert_every == 0:
        #     g.insert_walker()

        if g.get_walker_amount() == 0:
            g.insert_walker()

        for i in range(len(g.walkers) - 1, -1, -1):
            g.random_walk(i)

        if (t + 1) % show_every == 0:
            im.set_data(g.grid)

            # update walkers overlay
            if sc is not None:
                sc.remove()
                sc = None
            if g.walkers:
                xs, ys = zip(*g.walkers)

                # size in points^2 so one marker roughly fills one grid cell
                fig.canvas.draw() 
                bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
                ax_w_in, ax_h_in = bbox.width, bbox.height
                cell_w_pt = (ax_w_in * fig.dpi) / grid_size * 72 / fig.dpi
                cell_h_pt = (ax_h_in * fig.dpi) / grid_size * 72 / fig.dpi
                side_pt = min(cell_w_pt, cell_h_pt)
                s_cell = side_pt ** 2

                sc = ax.scatter(xs, ys, s=s_cell, marker="s", color="white", clip_on=True)

            ax.set_title(f"MC Grid, step {t+1}, walkers {len(g.walkers)}")
            fig.canvas.draw()
            fig.canvas.flush_events()
            plt.pause(0.001)

    plt.ioff()
    plt.show()

if __name__ == "__main__":
    main()
# mobility_simulator.py
import numpy as np

class Cell:
    def __init__(self, cell_id, x, y, radius=300, max_load=100):
        self.cell_id = cell_id
        self.x = x
        self.y = y
        self.radius = radius
        self.load = 0
        self.max_load = max_load
        self.is_outage = False

class UE:
    def __init__(self, ue_id, x, y):
        self.ue_id = ue_id
        self.x = x
        self.y = y
        self.speed = np.random.uniform(0.5, 15)  # m/s
        self.dest_x = np.random.uniform(0, 1000)
        self.dest_y = np.random.uniform(0, 1000)
        self.rrc_state = "RRC_CONNECTED"
        self.serving_cell = None

    def move(self, dt=1.0):
        dx = self.dest_x - self.x
        dy = self.dest_y - self.y
        dist = np.sqrt(dx**2 + dy**2)
        if dist < self.speed * dt:
            self.x, self.y = self.dest_x, self.dest_y
            self.dest_x = np.random.uniform(0, 1000)
            self.dest_y = np.random.uniform(0, 1000)
            self.speed = np.random.uniform(0.5, 15)
        else:
            self.x += (dx/dist) * self.speed * dt
            self.y += (dy/dist) * self.speed * dt

class MobilitySimulator:
    def __init__(self, n_cells=7, n_ues=20):
        self.cells = self._create_hex_grid(n_cells)
        self.ues = [UE(i, np.random.uniform(0,1000), np.random.uniform(0,1000)) for i in range(n_ues)]

    def _create_hex_grid(self, n):
        # Hexagonal cell layout
        positions = [(500,500),(500,800),(800,650),(800,350),(500,200),(200,350),(200,650)]
        return [Cell(i, positions[i][0], positions[i][1]) for i in range(min(n, len(positions)))]

    def get_serving_cell(self, ue):
        distances = [np.sqrt((ue.x-c.x)**2 + (ue.y-c.y)**2) for c in self.cells]
        return self.cells[np.argmin(distances)]

    def step(self):
        for ue in self.ues:
            ue.move()
            ue.serving_cell = self.get_serving_cell(ue)
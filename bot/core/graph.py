import math
import heapq

class WaypointGraph:
    def __init__(self):
        # Format: {node_id: (x, y)}
        self.nodes = {} 
        # Format: {node_id: [neighbor_id1, neighbor_id2, ...]}
        self.edges = {}

    def from_dict(self, graph_dict: dict):
        self.nodes = graph_dict.get("nodes")
        self.edges = graph_dict.get("edges")

        return self

    def add_node(self, node_id, position):
        self.nodes[node_id] = tuple(position)
        if node_id not in self.edges:
            self.edges[node_id] = []

    def add_connection(self, id1, id2, bidirection=True):
        if id2 not in self.edges[id1]:
            self.edges[id1].append(id2)
        if bidirection and id1 not in self.edges[id2]:
            self.edges[id2].append(id1)

    def get_closest_node(self, current_pos):
        """Finds the node ID closest to the bot's current (x, y)."""
        closest_id = None
        min_dist = float('inf')

        for node_id, pos in self.nodes.items():
            dist = math.dist(current_pos, pos)
            if dist < min_dist:
                min_dist = dist
                closest_id = node_id
        
        return closest_id, min_dist

    def find_path(self, start_id, end_id):
        """A* Pathfinding to get list of coordinates."""
        start_id = str(start_id)
        end_id = str(end_id)
        queue = [(0, start_id)]
        came_from = {start_id: None}
        cost_so_far = {start_id: 0}

        while queue:
            _, current = heapq.heappop(queue)

            if current == end_id:
                break

            for next_node in self.edges.get(current, []):
                next_node = str(next_node)
                new_cost = cost_so_far[current] + math.dist(self.nodes[current], self.nodes[next_node])
                
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + math.dist(self.nodes[next_node], self.nodes[end_id])
                    heapq.heappush(queue, (priority, next_node))
                    came_from[next_node] = current

        return self._reconstruct_path(came_from, start_id, end_id)

    def _reconstruct_path(self, came_from, start, end):
        if end not in came_from:
            return None # No path found
        
        current = end
        path = []
        while current != start:
            path.append(self.nodes[current])
            current = came_from[current]
        path.append(self.nodes[start])
        path.reverse()
        return path # Returns list of (x, y) tuples
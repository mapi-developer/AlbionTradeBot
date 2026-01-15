import math
import time
import sys, os
from ..core import InputSender

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.net import WaypointGraph

test_graph_dict = {
    "nodes": {
        1: [225, -209],
        2: [225, -199],
        3: [225, -188]
    },
    "edges": {
        1: [2],
        2: [1, 3],
        3: [2]
    }
}

class KeyboardTravelManager:
    current_location_graph: WaypointGraph
    
    def __init__(self, bot):
        self.bot = bot
        self.input = InputSender()
        self.current_keys = []
        self.current_location_graph = WaypointGraph().from_dict(test_graph_dict)

    def get_player_position(self):
        """Safely gets the current position from the sniffer."""
        return self.bot.sniffer.current_position

    def release_all_keys(self):
        """Releases any currently held movement keys."""
        for key in ['up', 'down', 'left', 'right']:
            self.input.key_up(key) # You need to ensure InputSender has key_up/key_down
        self.current_keys = []

    def update_movement_keys(self, target_angle):
        """
        Determines the best key combination for the given angle and presses them.
        """
        # Define the 8 directional sectors
        # Format: (Target Angle, [List of Keys])
        directions = [
            (357, ['down', 'right']), # North-East
            (42,  ['right']),       # East
            (87,  ['up', 'right']),# South-East
            (132, ['up']),        # South
            (177, ['up', 'left']), # South-West
            (222, ['left']),        # West
            (267, ['down', 'left']),  # North-West
            (312, ['down'])           # North
        ]

        # Find the direction with the smallest angular difference
        best_keys = []
        min_diff = 360

        for angle, keys in directions:
            # Calculate difference accounting for 0/360 wrap
            diff = abs(angle - target_angle)
            if diff > 180:
                diff = 360 - diff
            
            if diff < min_diff:
                min_diff = diff
                best_keys = keys

        # Optimize inputs: Only change if keys are different
        if set(best_keys) != set(self.current_keys):
            # print(f"[Move] Switching to {best_keys} (Target Angle: {target_angle:.0f})")
            
            # Release keys that are no longer needed
            for key in self.current_keys:
                if key not in best_keys:
                    self.input.key_up(key)
            
            # Press new keys
            for key in best_keys:
                if key not in self.current_keys:
                    self.input.key_down(key)
            
            self.current_keys = best_keys

    def move_to_position(self, target_pos, tolerance=1.5, timeout=15):
        """
        Navigates to a point using keyboard arrows.
        """
        start_time = time.time()
        
        try:
            while True:
                # 1. Get Position
                current_pos = self.get_player_position()
                if not current_pos:
                    time.sleep(0.1)
                    continue

                # 2. Check Distance
                dx = target_pos[0] - current_pos[0]
                dy = target_pos[1] - current_pos[1]
                dist = math.hypot(dx, dy)

                if dist <= tolerance:
                    self.release_all_keys()
                    return True

                if time.time() - start_time > timeout:
                    print(f"[Move] Timeout reaching {target_pos}")
                    self.release_all_keys()
                    return False

                # 3. Calculate Angle
                # math.atan2 returns radians. We convert to degrees.
                # Result is -180 to 180. We normalize to 0-360.
                angle_rad = math.atan2(dy, dx)
                target_angle = math.degrees(angle_rad)
                if target_angle < 0:
                    target_angle += 360

                # 4. Update Keys
                self.update_movement_keys(target_angle)
                
                # Small sleep to save CPU
                time.sleep(0.05)

        except KeyboardInterrupt:
            self.release_all_keys()
            raise

    def travel_to_node(self, target_node_id: int):
        closest_node_id = self.current_location_graph.get_closest_node(self.get_player_position())
        print(closest_node_id)
        path = self.current_location_graph.find_path(closest_node_id[0], target_node_id)
        for waypoint in path:
            self.move_to_position(waypoint)
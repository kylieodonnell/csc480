from time import sleep
from gdpc import Editor, Block, geometry
import numpy as np
import math
import matplotlib.pyplot as plt


class House:
    def __init__(self, editor, coordinates_min, coordinates_max, direction, list_block):
        self.editor = editor
        self.coordinates_min = coordinates_min
        self.coordinates_max = coordinates_max
        self.skeleton = []

        size = [(coordinates_max[i] - coordinates_min[i]) + 10 for i in range(3)]

        self.grid3d = np.zeros(size, dtype=[('bool', bool), ('int', int)])

        self.nbEtage = (coordinates_max[1] - coordinates_min[1]) // 5

        self.direction = direction

        self.entranceWall = None

        self.blocks = list_block

        self.entranceCo = None

        self.wall = Block(list_block["wall"])
        self.roof = Block(list_block["roof"])
        self.roof_slab = Block(list_block["roof_slab"])
        self.door = Block(list_block["door"])
        self.window = Block(list_block["window"])
        self.entrance = Block(list_block["entrance"])
        self.stairs = Block(list_block["stairs"])
        self.celling = Block(list_block["celling"])
        self.floor = Block(list_block["floor"])
        self.celling_slab = Block(list_block["celling_slab"])
        self.gardenOutline = Block(list_block["garden_outline"])
        self.garden_floor = Block(list_block["garden_floor"])

    def createHouseSkeleton(self):
        self.delete()
        x_min, y_min, z_min = self.coordinates_min
        x_max, y_max, z_max = self.coordinates_max

        # Perimeter dimensions
        perimeter_width = x_max - x_min
        perimeter_depth = z_max - z_min
        height = y_max - y_min

        # Initial room placement at the center
        start_x = x_min + perimeter_width // 4
        start_z = z_min + perimeter_depth // 4

        initial_room = (start_x, start_z, perimeter_width // 2, perimeter_depth // 2, height)
        if self.place_room(initial_room):
            if self.backtrack(initial_room, 3):  # Start with 3 additional rooms
                print("House skeleton created successfully.")
            else:
                print("Failed to create the house skeleton.")
        else:
            print("Failed to place the initial room.")

    def place_room(self, room):
        x, z, width, depth, height = room
        if not self.is_valid_room(x, z, width, depth):
            return False

        x_plan3d = x - self.coordinates_min[0]
        z_plan3d = z - self.coordinates_min[2]

        # Place room on the grid
        for i in range(0, width):
            for j in range(0, depth):
                self.editor.placeBlock((x + i, self.coordinates_min[1], z + j), self.floor)
                self.grid3d[x_plan3d + i, 0, z_plan3d + j] = True, 1

        self.skeleton.append(room)
        return True

    def is_valid_room(self, x, z, width, depth):
        x_min = self.coordinates_min[0]
        z_min = self.coordinates_min[2]
        x_max = self.coordinates_max[0]
        z_max = self.coordinates_max[2]

        if x < x_min or z < z_min or x + width > x_max or z + depth > z_max:
            return False

        x_plan3d = x - x_min
        z_plan3d = z - z_min

        # Check for overlap with existing rooms
        for i in range(0, width):
            for j in range(0, depth):
                if self.grid3d[x_plan3d + i, 0, z_plan3d + j]['bool']:
                    return False
        return True

    def backtrack(self, current_room, rooms_left):
        if rooms_left == 0:
            return True  # All rooms placed successfully

        x, z, width, depth, height = current_room
        for new_width in range(5, width + 1):
            for new_depth in range(5, depth + 1):
                for new_x in range(x - new_width + 1, x + width):
                    for new_z in range(z - new_depth + 1, z + depth):
                        new_room = (new_x, new_z, new_width, new_depth, height)

                        # Pruning: Skip this branch if space is too small
                        if not self.can_fit_additional_rooms(new_room, rooms_left):
                            continue

                        if self.place_room(new_room):
                            if self.backtrack(new_room, rooms_left - 1):
                                return True
                            # Undo room placement if backtracking fails
                            self.remove_room(new_room)

        return False  # No valid configuration found

    def can_fit_additional_rooms(self, current_room, rooms_left):
        """
        Pruning heuristic: Determine if the remaining space can fit the required number of rooms.
        """
        x, z, width, depth, height = current_room
        remaining_width = self.coordinates_max[0] - (x + width)
        remaining_depth = self.coordinates_max[2] - (z + depth)

        # Simple heuristic: check if the remaining space can at least fit the minimum required rooms
        min_room_size = 5 * 5 
        available_space = remaining_width * remaining_depth

        if available_space < rooms_left * min_room_size:
            return False

        # Further pruning: Check if the available space is reasonably usable
        # For example, we could check if the area is too narrow to place any more rooms.
        if remaining_width < 5 or remaining_depth < 5:
            return False

        return True

    def remove_room(self, room):
        x, z, width, depth, height = room
        x_plan3d = x - self.coordinates_min[0]
        z_plan3d = z - self.coordinates_min[2]

        # Remove room from the grid
        for i in range(0, width):
            for j in range(0, depth):
                self.grid3d[x_plan3d + i, 0, z_plan3d + j] = False, 0
                self.editor.placeBlock((x + i, self.coordinates_min[1], z + j), Block("air"))

        self.skeleton.remove(room)

    def delete(self):
        geometry.placeCuboid(self.editor, self.coordinates_min,
                             self.coordinates_max, Block("air"))

    def putWallOnSkeleton(self):
        for k in range(len(self.skeleton)):
            x, z, width, depth, height = self.skeleton[k]

            if k != 0:
                x += 1
                z += 1
                width -= 2
                depth -= 2
            x_plan3d = x - self.coordinates_min[0]
            z_plan3d = z - self.coordinates_min[2]
            for i in range(-1, width + 1):
                for j in range(-1, depth + 1):
                    for y in range(0, height):
                        if i == -1 or i == width or j == -1 or j == depth:
                            if not (self.grid3d[x_plan3d + i, y, z_plan3d + j]['bool']) and not (
                                    self.grid3d[x_plan3d + i, y, z_plan3d + j]['int'] == 1) or (
                                    self.grid3d[x_plan3d + i, y, z_plan3d + j]['bool'] and
                                    self.grid3d[x_plan3d + i, y, z_plan3d + j]['int'] == 2) or y == 0:
                                self.editor.placeBlock(
                                    (x + i, self.coordinates_min[1] + y, z + j), self.wall)
                                self.grid3d[x_plan3d + i,
                                            y, z_plan3d + j] = True

    def getAdjacentWalls(self):

        main_rect = self.skeleton[0]
        x_main, z_main, width_main, depth_main, heigt_main = main_rect
        adjacent_walls = []
        width_main -= 1
        depth_main -= 1

        for k in range(1, len(self.skeleton)):
            x, z, width, depth, heigt = self.skeleton[k]

            walls = [(x, z, x + width - 1, z), (x, z, x, z + depth - 1),
                     (x, z + depth - 1, x + width - 1, z + depth - 1), (x + width - 1, z, x + width - 1, z + depth - 1)]
            for wall in walls:
                x1, z1, x2, z2 = wall
                if (x_main <= x1 <= x_main + width_main or x_main <= x2 <= x_main + width_main) and (
                        z_main - 1 == z1 or z_main + depth_main + 1 == z1):
                    x1 = max(x1, x_main - 1)
                    x2 = min(x2, x_main + width_main + 1)
                    if abs(x2 - x1) > 1:
                        adjacent_walls.append((x1, z1, x2, z2))
                elif (z_main <= z1 <= z_main + depth_main or z_main <= z2 <= z_main + depth_main) and (
                        x_main - 1 == x1 or x_main + width_main + 1 == x1):
                    z1 = max(z1, z_main - 1)
                    z2 = min(z2, z_main + depth_main + 1)
                    if abs(z2 - z1) > 1:
                        adjacent_walls.append((x1, z1, x2, z2))

        return adjacent_walls

    def placeDoor(self):
        walls = self.getAdjacentWalls()
        for wall in walls:
            for i in range(self.nbEtage):
                x_min, z_min, x_max, z_max = wall
                if x_min == x_max:
                    width = z_max - z_min
                    if width % 2 != 0:
                        door_pos = width // 2
                        for y in range(self.coordinates_min[1] + 1 + i * 4, self.coordinates_min[1] + 3 + i * 4):
                            self.editor.placeBlock(
                                (x_min, y, z_min + door_pos), Block("air"))
                            self.editor.placeBlock(
                                (x_min, y, z_min + door_pos + 1), Block("air"))
                    else:
                        door_pos = width // 2
                        for y in range(self.coordinates_min[1] + 1 + i * 4, self.coordinates_min[1] + 3 + i * 4):
                            self.editor.placeBlock(
                                (x_min, y, z_min + door_pos), Block("air"))
                else:
                    width = x_max - x_min
                    if width % 2 != 0:
                        door_pos = width // 2
                        for y in range(self.coordinates_min[1] + 1 + i * 4, self.coordinates_min[1] + 3 + i * 4):
                            self.editor.placeBlock(
                                (x_min + door_pos, y, z_min), Block("air"))
                            self.editor.placeBlock(
                                (x_min + door_pos + 1, y, z_min), Block("air"))

                    else:
                        door_pos = width // 2
                        for y in range(self.coordinates_min[1] + 1 + i * 4, self.coordinates_min[1] + 3 + i * 4):
                            self.editor.placeBlock(
                                (x_min + door_pos, y, z_min), Block("air"))

    def placeRoof(self):
        for k in range(len(self.skeleton) - 1, -1, -1):
            x, z, width, depth, height = self.skeleton[k]

            if k != 0:
                x += 1
                z += 1
                width -= 2
                depth -= 2
                if width < depth:
                    if width <= 5:
                        n = 1
                    elif width <= 10:
                        n = 2
                    else:
                        n = 3
                else:
                    if depth <= 5:
                        n = 1
                    elif depth <= 10:
                        n = 2
                    else:
                        n = 3
            else:

                if width > depth:
                    n = width // 4
                else:
                    n = depth // 4

            x_plan3d = x - self.coordinates_min[0]
            z_plan3d = z - self.coordinates_min[2]

            print(width, depth, n)

            if width < depth:

                if n > 1:
                    for k in range(n):
                        for i in range(-1, depth + 1):
                            for y in range(-1, width // 2 + 1 - k):
                                self.editor.placeBlock(
                                    (x + y + k + 2, self.coordinates_max[1] + k, z + i), self.roof)
                                self.editor.placeBlock(
                                    (x + width - y - 1 - k - 2, self.coordinates_max[1] + k, z + i), self.roof)
                else:
                    if width % 2 == 0:
                        for i in range(-1, depth + 1):
                            for y in range(2):
                                self.editor.placeBlock(
                                    (x + width//2 - 1 + y, self.coordinates_max[1] + n - 1, z + i), self.roof)
                    else:
                        for i in range(-1, depth + 1):
                            self.editor.placeBlock(
                                (x + width // 2, self.coordinates_max[1] + n - 1, z + i), self.roof)
            else:
                if n > 1:
                    for k in range(n):
                        for i in range(-1, width + 1):
                            for y in range(-1, depth // 2 + 1 - k):
                                self.editor.placeBlock(
                                    (x + i, self.coordinates_max[1] + k, z + y + k + 2), self.roof)
                                self.editor.placeBlock(
                                    (x + i, self.coordinates_max[1] + k, z + depth - y - 1 - k - 2), self.roof)
                else:
                    if depth % 2 == 0:
                        for i in range(-1, width + 1):
                            for y in range(2):
                                self.editor.placeBlock(
                                    (x + i, self.coordinates_max[1] + n - 1, z + depth // 2 - 1 + y), self.roof)
                    else:
                        for i in range(-1, width + 1):
                            self.editor.placeBlock(
                                (x + i, self.coordinates_max[1] + n - 1, z + depth // 2), self.roof)

            print('-----------------------------------')

            for i in range(-1, width + 1):
                for j in range(-1, depth + 1):
                    if width < depth:
                        if width % 2 != 0:
                            if (i == width // 2):
                                self.editor.placeBlock((x + i, self.coordinates_max[1] + n, z + j),
                                                       Block(self.blocks["roof_slab"], {"type": "bottom"}))
                                self.grid3d[x_plan3d + i,
                                            height + n, z_plan3d + j] = True
                                if j == -1:
                                    if not self.grid3d[x_plan3d + i, height + n, z_plan3d + j - 1]:
                                        self.editor.placeBlock((x + i, self.coordinates_max[1] + n, z + j - 1),
                                                               Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                        self.grid3d[x_plan3d + i, height +
                                                    n, z_plan3d + j - 1] = True
                                    if not self.grid3d[x_plan3d + i, height + n - 1, z_plan3d + j - 1]:
                                        self.editor.placeBlock((x + i, self.coordinates_max[1] + n - 1, z + j - 1),
                                                               Block(self.blocks["celling_slab"], {"type": "top"}))
                                        self.grid3d[x_plan3d + i, height +
                                                    n - 1, z_plan3d + j - 1] = True

                                elif j == depth:
                                    if not self.grid3d[x_plan3d + i, height + n, z_plan3d + j + 1]:
                                        self.editor.placeBlock((x + i, self.coordinates_max[1] + n, z + j + 1),
                                                               Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                        self.grid3d[x_plan3d + i, height +
                                                    n, z_plan3d + j + 1] = True
                                    if not self.grid3d[x_plan3d + i, height + n - 1, z_plan3d + j + 1]:
                                        self.editor.placeBlock((x + i, self.coordinates_max[1] + n - 1, z + j + 1),
                                                               Block(self.blocks["celling_slab"], {"type": "top"}))
                                        self.grid3d[x_plan3d + i, height +
                                                    n - 1, z_plan3d + j + 1] = True

                    else:
                        if depth % 2 != 0:
                            if (j == depth // 2):
                                self.editor.placeBlock((x + i, self.coordinates_max[1] + n, z + j),
                                                       Block(self.blocks["roof_slab"], {"type": "bottom"}))
                                self.grid3d[x_plan3d + i,
                                            height + n, z_plan3d + j] = True
                                if i == -1:
                                    if not self.grid3d[x_plan3d + i - 1, height + n, z_plan3d + j]:
                                        self.editor.placeBlock((x + i - 1, self.coordinates_max[1] + n, z + j),
                                                               Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                        self.grid3d[x_plan3d + i - 1,
                                                    height + n, z_plan3d + j] = True
                                    if not self.grid3d[x_plan3d + i - 1, height + n - 1, z_plan3d + j]:
                                        self.editor.placeBlock((x + i - 1, self.coordinates_max[1] + n - 1, z + j),
                                                               Block(self.blocks["celling_slab"], {"type": "top"}))
                                        self.grid3d[x_plan3d + i - 1,
                                                    height + n - 1, z_plan3d + j] = True

                                elif i == width:
                                    if not self.grid3d[x_plan3d + i + 1, height + n, z_plan3d + j]:
                                        self.editor.placeBlock((x + i + 1, self.coordinates_max[1] + n, z + j),
                                                               Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                        self.grid3d[x_plan3d + i + 1,
                                                    height + n, z_plan3d + j] = True
                                    if not self.grid3d[x_plan3d + i + 1, height + n - 1, z_plan3d + j]:
                                        self.editor.placeBlock((x + i + 1, self.coordinates_max[1] + n - 1, z + j),
                                                               Block(self.blocks["celling_slab"], {"type": "top"}))
                                        self.grid3d[x_plan3d + i + 1,
                                                    height + n - 1, z_plan3d + j] = True

            if width < depth:

                h = 0
                for i in range(-1, width // 2):
                    for j in range(-1, depth + 1):
                        if i != -1:
                            if h % 1 == 0:
                                self.editor.placeBlock((x + i, math.ceil(self.coordinates_max[1] + h), z + j),
                                                       Block(self.blocks["roof_slab"], {"type": "top"}))
                                self.editor.placeBlock((x + width - 1 - i, math.ceil(self.coordinates_max[1] + h), z + j),
                                                       Block(self.blocks["roof_slab"], {"type": "top"}))
                                self.grid3d[x_plan3d + i,
                                            round(height + h), z_plan3d + j] = True
                                self.grid3d[x_plan3d + width - 1 - i,
                                            round(height + h), z_plan3d + j] = True

                                if j == -1:

                                    self.editor.placeBlock((x + i, math.ceil(self.coordinates_max[1] + h), z + j - 1),
                                                           self.celling)
                                    self.editor.placeBlock((x + width - 1 - i, math.ceil(self.coordinates_max[1] + h), z + j - 1),
                                                           self.celling)
                                    self.grid3d[x_plan3d + i,
                                                round(height + h), z_plan3d + j - 1] = True
                                    self.grid3d[x_plan3d + width - 1 - i,
                                                round(height + h), z_plan3d + j - 1] = True
                                elif j == depth:
                                    self.editor.placeBlock((x + i, math.ceil(self.coordinates_max[1] + h), z + j + 1),
                                                           self.celling)
                                    self.editor.placeBlock((x + width - 1 - i, math.ceil(self.coordinates_max[1] + h), z + j + 1),
                                                           self.celling)
                                    self.grid3d[x_plan3d + i,
                                                round(height + h), z_plan3d + j + 1] = True
                                    self.grid3d[x_plan3d + width - 1 - i,
                                                round(height + h), z_plan3d + j + 1] = True
                            else:
                                self.editor.placeBlock((x + i, math.ceil(self.coordinates_max[1] + h), z + j),
                                                       Block(self.blocks["roof_slab"], {"type": "bottom"}))
                                self.editor.placeBlock((x + width - 1 - i, math.ceil(self.coordinates_max[1] + h), z + j),
                                                       Block(self.blocks["roof_slab"], {"type": "bottom"}))
                                self.editor.placeBlock(
                                    (x + i, math.ceil(self.coordinates_max[1] + h-0.5), z + j), self.roof)
                                self.editor.placeBlock((x + width - 1 - i, math.ceil(self.coordinates_max[1] + h-0.5), z + j),
                                                       self.roof)

                                self.grid3d[x_plan3d + i,
                                            round(height + h + 0.5), z_plan3d + j] = True
                                self.grid3d[x_plan3d + width - 1 - i,
                                            round(height + h + 0.5), z_plan3d + j] = True
                                self.grid3d[x_plan3d + i,
                                            round(height + h - 0.5), z_plan3d + j] = True
                                self.grid3d[x_plan3d + width - 1 - i,
                                            round(height + h - 0.5), z_plan3d + j] = True

                                if j == -1:
                                    self.editor.placeBlock((x + i, math.ceil(self.coordinates_max[1] + h), z + j - 1),
                                                           Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                    self.editor.placeBlock((x + width - 1 - i, math.ceil(self.coordinates_max[1] + h), z + j - 1),
                                                           Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                    self.editor.placeBlock((x + i, math.ceil(self.coordinates_max[1] + h-1), z + j - 1),
                                                           Block(self.blocks["celling_slab"], {"type": "top"}))
                                    self.editor.placeBlock(
                                        (x + width - 1 - i,
                                         math.ceil(self.coordinates_max[1] + h-1), z + j - 1),
                                        Block(self.blocks["celling_slab"], {"type": "top"}))

                                    self.grid3d[x_plan3d + i,
                                                round(height + h - 1), z_plan3d + j - 1] = True
                                    self.grid3d[
                                        x_plan3d + width - 1 - i, round(height + h - 1), z_plan3d + j - 1] = True
                                    self.grid3d[x_plan3d + i,
                                                round(height + h), z_plan3d + j - 1] = True
                                    self.grid3d[x_plan3d + width - 1 - i,
                                                round(height + h), z_plan3d + j - 1] = True
                                elif j == depth:
                                    self.editor.placeBlock((x + i, math.ceil(self.coordinates_max[1] + h), z + j + 1),
                                                           Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                    self.editor.placeBlock((x + width - 1 - i, math.ceil(self.coordinates_max[1] + h), z + j + 1),
                                                           Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                    self.editor.placeBlock((x + i, math.ceil(self.coordinates_max[1] + h-1), z + j + 1),
                                                           Block(self.blocks["celling_slab"], {"type": "top"}))
                                    self.editor.placeBlock(
                                        (x + width - 1 - i,
                                         math.ceil(self.coordinates_max[1] + h-1), z + j + 1),
                                        Block(self.blocks["celling_slab"], {"type": "top"}))

                                    self.grid3d[x_plan3d + i,
                                                round(height + h - 1), z_plan3d + j + 1] = True
                                    self.grid3d[
                                        x_plan3d + width - 1 - i, round(height + h - 1), z_plan3d + j + 1] = True
                                    self.grid3d[x_plan3d + i,
                                                round(height + h), z_plan3d + j + 1] = True
                                    self.grid3d[x_plan3d + width - 1 - i,
                                                round(height + h), z_plan3d + j + 1] = True
                        else:
                            self.editor.placeBlock((x + i, math.ceil(self.coordinates_max[1] + h), z + j),
                                                   Block(self.blocks["roof_slab"], {"type": "bottom"}))
                            self.editor.placeBlock((x + width - 1 - i, math.ceil(self.coordinates_max[1] + h), z + j),
                                                   Block(self.blocks["roof_slab"], {"type": "bottom"}))

                            self.grid3d[x_plan3d + i,
                                        round(height + h), z_plan3d + j] = True
                            self.grid3d[x_plan3d + width - 1 - i,
                                        round(height + h), z_plan3d + j] = True

                            if j == -1:
                                self.editor.placeBlock((x + i, math.ceil(self.coordinates_max[1] + h), z + j - 1),
                                                       Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                self.editor.placeBlock((x + width - 1 - i, math.ceil(self.coordinates_max[1] + h), z + j - 1),
                                                       Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                if not self.grid3d[x_plan3d + i, height + h - 1, z_plan3d + j - 1]:
                                    self.editor.placeBlock((x + i, math.ceil(self.coordinates_max[1] + h-1), z + j - 1),
                                                           Block(self.blocks["celling_slab"], {"type": "top"}))
                                    self.grid3d[x_plan3d + i, height +
                                                h - 1, z_plan3d + j - 1] = True
                                if not self.grid3d[x_plan3d + width - 1 - i, height + h - 1, z_plan3d + j - 1]:
                                    self.editor.placeBlock(
                                        (x + width - 1 - i,
                                         math.ceil(self.coordinates_max[1] + h-1), z + j - 1),
                                        Block(self.blocks["celling_slab"], {"type": "top"}))
                                    self.grid3d[x_plan3d + width - 1 - i,
                                                height + h - 1, z_plan3d + j - 1] = True

                                self.grid3d[x_plan3d + i,
                                            round(height + h - 1), z_plan3d + j - 1] = True
                                self.grid3d[x_plan3d + width - 1 - i,
                                            round(height + h - 1), z_plan3d + j - 1] = True
                            elif j == depth:
                                self.editor.placeBlock((x + i, math.ceil(self.coordinates_max[1] + h), z + j + 1),
                                                       Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                self.editor.placeBlock((x + width - 1 - i, math.ceil(self.coordinates_max[1] + h), z + j + 1),
                                                       Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                if not self.grid3d[x_plan3d + i, height + h - 1, z_plan3d + j + 1]:
                                    self.editor.placeBlock((x + i, math.ceil(self.coordinates_max[1] + h-1), z + j + 1),
                                                           Block(self.blocks["celling_slab"], {"type": "top"}))
                                    self.grid3d[x_plan3d + i, height +
                                                h - 1, z_plan3d + j + 1] = True
                                if not self.grid3d[x_plan3d + width - 1 - i, height + h - 1, z_plan3d + j + 1]:
                                    self.editor.placeBlock(
                                        (x + width - 1 - i,
                                         math.ceil(self.coordinates_max[1] + h-1), z + j + 1),
                                        Block(self.blocks["celling_slab"], {"type": "top"}))
                                    self.grid3d[x_plan3d + width - 1 - i,
                                                height + h - 1, z_plan3d + j + 1] = True

                                self.grid3d[x_plan3d + i,
                                            round(height + h - 1), z_plan3d + j + 1] = True
                                self.grid3d[x_plan3d + width - 1 - i,
                                            round(height + h - 1), z_plan3d + j + 1] = True
                    if i != -1:
                        h += 0.5
            else:

                h = 0
                for i in range(-1, depth // 2):
                    for j in range(-1, width + 1):
                        if i != -1:
                            if h % 1 == 0:
                                self.editor.placeBlock((x + j, math.ceil(self.coordinates_max[1] + h), z + i),
                                                       Block(self.blocks["roof_slab"], {"type": "top"}))
                                self.editor.placeBlock((x + j, math.ceil(self.coordinates_max[1] + h), z + depth - 1 - i),
                                                       Block(self.blocks["roof_slab"], {"type": "top"}))

                                self.grid3d[x_plan3d + j,
                                            round(height + h), z_plan3d + i] = True
                                self.grid3d[x_plan3d + j,
                                            round(height + h), z_plan3d + depth - 1 - i] = True

                                if j == -1:
                                    self.editor.placeBlock((x + j - 1, math.ceil(self.coordinates_max[1] + h), z + i),
                                                           self.celling)
                                    self.editor.placeBlock((x + j - 1, math.ceil(self.coordinates_max[1] + h), z + depth - 1 - i),
                                                           self.celling)

                                    self.grid3d[x_plan3d + j - 1,
                                                round(height + h), z_plan3d + i] = True
                                    self.grid3d[x_plan3d + j - 1,
                                                round(height + h), z_plan3d + depth - 1 - i] = True
                                elif j == width:
                                    self.editor.placeBlock((x + j + 1, math.ceil(self.coordinates_max[1] + h), z + i),
                                                           self.celling)
                                    self.editor.placeBlock((x + j + 1, math.ceil(self.coordinates_max[1] + h), z + depth - 1 - i),
                                                           self.celling)

                                    self.grid3d[x_plan3d + j + 1,
                                                round(height + h), z_plan3d + i] = True
                                    self.grid3d[x_plan3d + j + 1,
                                                round(height + h), z_plan3d + depth - 1 - i] = True

                            else:
                                self.editor.placeBlock((x + j, math.ceil(self.coordinates_max[1] + h), z + i),
                                                       Block(self.blocks["roof_slab"], {"type": "bottom"}))
                                self.editor.placeBlock((x + j, math.ceil(self.coordinates_max[1] + h), z + depth - 1 - i),
                                                       Block(self.blocks["roof_slab"], {"type": "bottom"}))
                                self.editor.placeBlock(
                                    (x + j, math.ceil(self.coordinates_max[1] + h - 0.5), z + i), self.roof)
                                self.editor.placeBlock((x + j, math.ceil(self.coordinates_max[1] + h - 0.5), z + depth - 1 - i),
                                                       self.roof)

                                self.grid3d[x_plan3d+j,
                                            round(height + h + 0.5), z_plan3d + i] = True
                                self.grid3d[x_plan3d+j, round(
                                    height + h + 0.5), z_plan3d + depth - 1 - i] = True
                                self.grid3d[x_plan3d+j,
                                            round(height + h - 0.5), z_plan3d + i] = True
                                self.grid3d[x_plan3d+j,
                                            round(height + h - 0.5), z_plan3d+depth - 1 - i] = True

                                if j == -1:
                                    self.editor.placeBlock((x + j - 1, math.ceil(self.coordinates_max[1] + h), z + i),
                                                           Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                    self.editor.placeBlock((x + j - 1, math.ceil(self.coordinates_max[1] + h), z + depth - 1 - i),
                                                           Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                    self.editor.placeBlock((x + j - 1, math.ceil(self.coordinates_max[1] + h - 1), z + i),
                                                           Block(self.blocks["celling_slab"], {"type": "top"}))
                                    self.editor.placeBlock(
                                        (x + j - 1, math.ceil(
                                            self.coordinates_max[1] + h-1), z + depth - 1 - i),
                                        Block(self.blocks["celling_slab"], {"type": "top"}))

                                    self.grid3d[x_plan3d+j-1,
                                                round(height + h), z_plan3d + i] = True
                                    self.grid3d[x_plan3d+j-1,
                                                round(height + h), z_plan3d+depth - 1 - i] = True
                                    self.grid3d[x_plan3d+j-1,
                                                round(height + h - 1), z_plan3d + i] = True
                                    self.grid3d[x_plan3d+j-1, round(
                                        height + h - 1), z_plan3d+depth - 1 - i] = True
                                elif j == width:
                                    self.editor.placeBlock((x + j + 1, math.ceil(self.coordinates_max[1] + h), z + i),
                                                           Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                    self.editor.placeBlock((x + j + 1, math.ceil(self.coordinates_max[1] + h), z + depth - 1 - i),
                                                           Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                    self.editor.placeBlock((x + j + 1, math.ceil(self.coordinates_max[1] + h-1), z + i),
                                                           Block(self.blocks["celling_slab"], {"type": "top"}))
                                    self.editor.placeBlock(
                                        (x + j + 1, math.ceil(
                                            self.coordinates_max[1] + h-1), z + depth - 1 - i),
                                        Block(self.blocks["celling_slab"], {"type": "top"}))

                                    self.grid3d[x_plan3d+j+1,
                                                round(height + h), z_plan3d + i] = True
                                    self.grid3d[x_plan3d+j+1,
                                                round(height + h), z_plan3d + depth - 1 - i] = True
                                    self.grid3d[x_plan3d+j+1,
                                                round(height + h - 1), z_plan3d+i] = True
                                    self.grid3d[x_plan3d+j+1, round(
                                        height + h - 1), z_plan3d + depth - 1 - i] = True
                        else:
                            self.editor.placeBlock((x + j, math.ceil(self.coordinates_max[1] + h), z + i),
                                                   Block(self.blocks["roof_slab"], {"type": "bottom"}))
                            self.editor.placeBlock((x + j, math.ceil(self.coordinates_max[1] + h), z + depth - 1 - i),
                                                   Block(self.blocks["roof_slab"], {"type": "bottom"}))

                            self.grid3d[x_plan3d+j,
                                        round(height + h), z_plan3d+i] = True
                            self.grid3d[x_plan3d+j,
                                        round(height + h), z_plan3d+depth - 1 - i] = True

                            if j == -1:
                                self.editor.placeBlock((x + j - 1, math.ceil(self.coordinates_max[1] + h), z + i),
                                                       Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                self.editor.placeBlock((x + j - 1, math.ceil(self.coordinates_max[1] + h), z + depth - 1 - i),
                                                       Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                if not self.grid3d[x_plan3d+j-1, height + h - 1, z_plan3d+i]:
                                    self.editor.placeBlock((x + j - 1, math.ceil(self.coordinates_max[1] + h-1), z + i),
                                                           Block(self.blocks["celling_slab"], {"type": "top"}))
                                    self.grid3d[x_plan3d+j-1,
                                                height + h - 1, z_plan3d+i] = True
                                if not self.grid3d[x_plan3d+j-1, height + h - 1, z_plan3d+depth - 1 - i]:
                                    self.editor.placeBlock(
                                        (x + j - 1, math.ceil(
                                            self.coordinates_max[1] + h-1), z + depth - 1 - i),
                                        Block(self.blocks["celling_slab"], {"type": "top"}))
                                    self.grid3d[x_plan3d+j-1, height +
                                                h - 1, z_plan3d+depth - 1 - i] = True

                                self.grid3d[x_plan3d+j-1,
                                            round(height + h), z_plan3d+i] = True
                                self.grid3d[x_plan3d+j-1,
                                            round(height + h), z_plan3d + depth - 1 - i] = True
                            elif j == width:
                                self.editor.placeBlock((x + j + 1, math.ceil(self.coordinates_max[1] + h), z + i),
                                                       Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                self.editor.placeBlock((x + j + 1, math.ceil(self.coordinates_max[1] + h), z + depth - 1 - i),
                                                       Block(self.blocks["celling_slab"], {"type": "bottom"}))
                                if not self.grid3d[x_plan3d+j+1, height + h - 1, z_plan3d + i]:
                                    self.editor.placeBlock((x + j + 1, math.ceil(self.coordinates_max[1] + h-1), z + i),
                                                           Block(self.blocks["celling_slab"], {"type": "top"}))
                                    self.grid3d[x_plan3d+j+1,
                                                height + h - 1, z_plan3d+i] = True
                                if not self.grid3d[x_plan3d+j+1, height + h - 1, z_plan3d + depth - 1 - i]:
                                    self.editor.placeBlock(
                                        (x + j + 1, math.ceil(
                                            self.coordinates_max[1] + h-1), z + depth - 1 - i),
                                        Block(self.blocks["celling_slab"], {"type": "top"}))
                                    self.grid3d[x_plan3d+j+1, height + h -
                                                1, z_plan3d + depth - 1 - i] = True

                                self.grid3d[x_plan3d+j+1,
                                            round(height + h), z_plan3d+i] = True
                                self.grid3d[x_plan3d+j+1,
                                            round(height + h), z_plan3d+depth - 1 - i] = True

                            self.grid3d[x_plan3d+j,
                                        round(height + h), z_plan3d+i] = True
                            self.grid3d[x_plan3d+j,
                                        round(height + h), z_plan3d + depth - 1 - i] = True

                    if i != -1:
                        h += 0.5

            QUARTZ_SLAB = Block(self.blocks["celling_slab"], {"type": "top"})

            for i in range(-2, width + 2):
                for j in range(-2, depth + 2):
                    if i == -2 or i == width + 1 or j == -2 or j == depth + 1:
                        if not self.grid3d[x_plan3d + i, height - 1, z_plan3d + j]['bool']:
                            if width < depth:
                                if i == -2 or i == width + 1:
                                    self.editor.placeBlock(
                                        (x + i, self.coordinates_max[1] - 1, z + j), QUARTZ_SLAB)

                            else:
                                if j == -2 or j == depth + 1:
                                    self.editor.placeBlock(
                                        (x + i, self.coordinates_max[1] - 1, z + j), QUARTZ_SLAB)

    def putCelling(self):
        for k in range(0, len(self.skeleton)):
            x, z, width, depth, height = self.skeleton[k]

            if k != 0:
                x += 1
                z += 1
                width -= 2
                depth -= 2
            x_plan3d = x - self.coordinates_min[0]
            z_plan3d = z - self.coordinates_min[2]
            for y in range(1, self.nbEtage + 1):
                for i in range(0, width):
                    for j in range(0, depth):
                        self.editor.placeBlock(
                            (x + i, self.coordinates_min[1] + 4 * y, z + j), self.celling)
                        self.grid3d[x_plan3d + i, 4 * y, z_plan3d + j] = True

    def getAllExterneWalls(self):
        walls = []
        adjacent_walls = self.getAdjacentWalls()
        for k in range(0, len(self.skeleton)):
            x, z, width, depth, height = self.skeleton[k]
            if k == 0:
                x -= 1
                z -= 1
                width += 2
                depth += 2

            walls.append((x, z, x + width - 1, z))
            walls.append((x, z, x, z + depth - 1))
            walls.append((x, z + depth - 1, x + width - 1, z + depth - 1))
            walls.append((x + width - 1, z, x + width - 1, z + depth - 1))

        walls_to_keep = []
        for wall in walls:
            remove_wall = False
            for adj_wall in adjacent_walls:
                if self.isInsideWall(wall, adj_wall):
                    remove_wall = True
                    break
            if not remove_wall:
                walls_to_keep.append(wall)

        return walls_to_keep

    def isInsideWall(self, big_wall, small_wall):
        x1, z1, x2, z2 = big_wall
        x3, z3, x4, z4 = small_wall
        if x1 == x2 == x3 == x4:
            return x1 == x3 and z1 <= z3 and z4 <= z2
        elif z1 == z2 == z3 == z4:
            return z1 == z3 and x1 <= x3 and x4 <= x2

    def placeWindowOnWall(self, wall, axis, is_x):
        for l in range(self.nbEtage):
            if axis % 2 == 0:
                if axis == 4:
                    if is_x:
                        self.editor.placeBlock(
                            (wall[0] + 2, self.coordinates_min[1] + 2 + l * 4, wall[1]), self.window)
                        self.editor.placeBlock(
                            (wall[0] + 3, self.coordinates_min[1] + 2 + l * 4, wall[1]), self.window)
                    else:
                        self.editor.placeBlock(
                            (wall[0], self.coordinates_min[1] + 2 + l * 4, wall[1] + 3), self.window)
                        self.editor.placeBlock(
                            (wall[0], self.coordinates_min[1] + 2 + l * 4, wall[1] + 2), self.window)
                else:
                    for i in range(0, math.ceil(axis / 4)):
                        if is_x:
                            self.editor.placeBlock((wall[0] + 1 + i * 4, self.coordinates_min[1] + 2 + l * 4, wall[1]),
                                                   self.window)
                            self.editor.placeBlock((wall[0] + 2 + i * 4, self.coordinates_min[1] + 2 + l * 4, wall[1]),
                                                   self.window)
                        else:
                            self.editor.placeBlock((wall[0], self.coordinates_min[1] + 2 + l * 4, wall[1] + 1 + i * 4),
                                                   self.window)
                            self.editor.placeBlock((wall[0], self.coordinates_min[1] + 2 + l * 4, wall[1] + 2 + i * 4),
                                                   self.window)
            else:
                if axis <= 5:
                    for i in range(0, axis):
                        if is_x:
                            self.editor.placeBlock((wall[0] + 1 + i, self.coordinates_min[1] + 2 + l * 4, wall[1]),
                                                   self.window)
                        else:
                            self.editor.placeBlock((wall[0], self.coordinates_min[1] + 2 + l * 4, wall[1] + 1 + i),
                                                   self.window)
                else:
                    for i in range(0, math.ceil(axis / 2)):
                        if is_x:
                            self.editor.placeBlock((wall[0] + i * 2 + 1, self.coordinates_min[1] + 2 + l * 4, wall[1]),
                                                   self.window)

                        else:
                            self.editor.placeBlock((wall[0], self.coordinates_min[1] + 2 + l * 4, wall[1] + i * 2 + 1),
                                                   self.window)

    def placeWindow(self):
        walls = self.getAllExterneWalls()
        for wall in walls:
            x1, z1, x2, z2 = wall
            x = abs(x2 - x1) - 1
            z = abs(z2 - z1) - 1
            if x1 == x2:
                self.placeWindowOnWall(wall, z, False)
            elif z1 == z2:
                self.placeWindowOnWall(wall, x, True)

    def placeStairs(self):
        x, z, width, depth, height = self.skeleton[0]
        x_moy = x + width // 2
        z_moy = z + depth // 2
        slab_up = Block(self.blocks["stairs_slab"], {"type": "top"})
        slab_down = Block(self.blocks["stairs_slab"], {"type": "bottom"})
        for i in range(0, self.nbEtage - 1):
            for k in range(3):
                for l in range(3):
                    self.editor.placeBlock((x_moy - 1 + k, self.coordinates_min[1] + 4 * (i + 1), z_moy - 1 + l),
                                           Block("air"))

            for j in range(1, 5):
                self.editor.placeBlock(
                    (x_moy, self.coordinates_min[1] + 4 * i + j, z_moy), self.floor)

            self.editor.placeBlock(
                (x_moy - 1, self.coordinates_min[1] + 1 + 4 * i, z_moy - 1), slab_down)
            self.editor.placeBlock(
                (x_moy, self.coordinates_min[1] + 1 + 4 * i, z_moy - 1), slab_up)
            self.editor.placeBlock(
                (x_moy + 1, self.coordinates_min[1] + 2 + 4 * i, z_moy - 1), slab_down)
            self.editor.placeBlock(
                (x_moy + 1, self.coordinates_min[1] + 2 + 4 * i, z_moy), slab_up)
            self.editor.placeBlock(
                (x_moy + 1, self.coordinates_min[1] + 3 + 4 * i, z_moy + 1), slab_down)

            self.editor.placeBlock(
                (x_moy, self.coordinates_min[1] + 3 + 4 * i, z_moy + 1), slab_up)
            self.editor.placeBlock(
                (x_moy - 1, self.coordinates_min[1] + 4 + 4 * i, z_moy + 1), slab_down)
            self.editor.placeBlock(
                (x_moy - 1, self.coordinates_min[1] + 4 + 4 * i, z_moy), slab_up)

    def WallFacingDirection(self):

        if self.direction == "N":
            closest_wall = min(self.skeleton, key=lambda wall: wall[1])
            wall = (closest_wall[0], closest_wall[1],
                    closest_wall[0] + closest_wall[2], closest_wall[1])
        elif self.direction == "S":
            closest_wall = max(
                self.skeleton, key=lambda wall: wall[1] + wall[3])
            wall = (closest_wall[0], closest_wall[1] + closest_wall[3], closest_wall[0] + closest_wall[2],
                    closest_wall[1] + closest_wall[3])
        elif self.direction == "E":
            closest_wall = max(
                self.skeleton, key=lambda wall: wall[0] + wall[2])
            wall = (closest_wall[0] + closest_wall[2], closest_wall[1], closest_wall[0] + closest_wall[2],
                    closest_wall[1] + closest_wall[3])
        elif self.direction == "W":
            closest_wall = min(self.skeleton, key=lambda wall: wall[0])
            wall = (closest_wall[0], closest_wall[1],
                    closest_wall[0], closest_wall[1] + closest_wall[3])
        else:
            return []

        if closest_wall != self.skeleton[0]:
            if wall[0] == wall[2]:
                wall = (wall[0] - 1, wall[1] + 1, wall[2] - 1, wall[3] - 2)

            elif wall[1] == wall[3]:

                wall = (wall[0] + 1, wall[1] - 1, wall[2] - 2, wall[3] - 1)
        else:
            if wall[0] == wall[2]:
                if self.direction == "W":
                    wall = (wall[0] - 2, wall[1], wall[2] - 2, wall[3])
                else:
                    wall = (wall[0], wall[1] + 1, wall[2], wall[3] - 2)

            elif wall[1] == wall[3]:

                if self.direction == "N":
                    wall = (wall[0] + 1, wall[1] - 2, wall[2] - 2, wall[3] - 2)
                else:
                    wall = (wall[0] + 1, wall[1], wall[2] - 2, wall[3])

        return wall

    def placeEntrance(self):
        wall = self.WallFacingDirection()

        self.entranceWall = wall
        match self.direction:
            case "W":
                if (wall[3] - wall[1]) % 2 != 0:
                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1] + 1, (wall[1] + wall[3]) // 2 + 1),
                                           Block("air"))
                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1] + 2, (wall[1] + wall[3]) // 2 + 1),
                                           Block("air"))
                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1] + 1, (wall[1] + wall[3]) // 2),
                                           Block("air"))
                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1] + 2, (wall[1] + wall[3]) // 2),
                                           Block("air"))

                    self.editor.placeBlock((wall[0], self.coordinates_min[1], (wall[1] + wall[3]) // 2),
                                           Block(self.blocks["stairs"], {"facing": "east"}))
                    self.editor.placeBlock((wall[0], self.coordinates_min[1], (wall[1] + wall[3]) // 2 + 1),
                                           Block(self.blocks["stairs"], {"facing": "east"}))
                    self.editor.placeBlock((wall[0], self.coordinates_min[1], (wall[1] + wall[3]) // 2 - 1),
                                           Block(self.blocks["stairs"], {"facing": "south"}))
                    self.editor.placeBlock((wall[0], self.coordinates_min[1], (wall[1] + wall[3]) // 2 + 2),
                                           Block(self.blocks["stairs"], {"facing": "north"}))

                    self.editor.placeBlock((wall[0], self.coordinates_min[1] + 3, (wall[1] + wall[3]) // 2),
                                           Block(self.blocks["stairs"], {"facing": "east", "half": "top"}))
                    self.editor.placeBlock((wall[0], self.coordinates_min[1] + 3, (wall[1] + wall[3]) // 2 + 1),
                                           Block(self.blocks["stairs"], {"facing": "east", "half": "top"}))
                    self.editor.placeBlock((wall[0], self.coordinates_min[1] + 3, (wall[1] + wall[3]) // 2 - 1),
                                           Block(self.blocks["stairs"], {"facing": "south", "half": "top"}))
                    self.editor.placeBlock((wall[0], self.coordinates_min[1] + 3, (wall[1] + wall[3]) // 2 + 2),
                                           Block(self.blocks["stairs"], {"facing": "north", "half": "top"}))

                    self.entranceCo = (
                        (wall[1] + wall[3]) // 2, (wall[1] + wall[3]
                                                   ) // 2 + 2, (wall[1] + wall[3]) // 2 + 1,
                        (wall[1] + wall[3]) // 2 - 1)

                else:
                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1] + 1, (wall[1] + wall[3]) // 2),
                                           Block("air"))
                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1] + 2, (wall[1] + wall[3]) // 2),
                                           Block("air"))

                    self.editor.placeBlock((wall[0], self.coordinates_min[1], (wall[1] + wall[3]) // 2),
                                           Block(self.blocks["stairs"], {"facing": "east"}))
                    self.editor.placeBlock((wall[0], self.coordinates_min[1], (wall[1] + wall[3]) // 2 + 1),
                                           Block(self.blocks["stairs"], {"facing": "north"}))
                    self.editor.placeBlock((wall[0], self.coordinates_min[1], (wall[1] + wall[3]) // 2 - 1),
                                           Block(self.blocks["stairs"], {"facing": "south"}))

                    self.editor.placeBlock((wall[0], self.coordinates_min[1] + 3, (wall[1] + wall[3]) // 2),
                                           Block(self.blocks["stairs"], {"facing": "east", "half": "top"}))
                    self.editor.placeBlock((wall[0], self.coordinates_min[1] + 3, (wall[1] + wall[3]) // 2 + 1),
                                           Block(self.blocks["stairs"], {"facing": "north", "half": "top"}))
                    self.editor.placeBlock((wall[0], self.coordinates_min[1] + 3, (wall[1] + wall[3]) // 2 - 1),
                                           Block(self.blocks["stairs"], {"facing": "south", "half": "top"}))

                    self.entranceCo = (
                        (wall[1] + wall[3]) // 2, (wall[1] + wall[3]
                                                   ) // 2 + 1, (wall[1] + wall[3]) // 2 + 1,
                        (wall[1] + wall[3]) // 2 - 1)

            case "N":
                if (wall[2] - wall[0]) % 2 != 0:
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 + 1,
                         self.coordinates_min[1] + 1, wall[1] + 1),
                        Block("air"))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 + 1,
                         self.coordinates_min[1] + 2, wall[1] + 1),
                        Block("air"))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2, self.coordinates_min[1] + 1, wall[1] + 1), Block("air"))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2, self.coordinates_min[1] + 2, wall[1] + 1), Block("air"))

                    self.editor.placeBlock((wall[0] + (wall[2] - wall[0]) // 2, self.coordinates_min[1], wall[1]),
                                           Block(self.blocks["stairs"], {"facing": "south"}))
                    self.editor.placeBlock((wall[0] + (wall[2] - wall[0]) // 2 + 1, self.coordinates_min[1], wall[1]),
                                           Block(self.blocks["stairs"], {"facing": "south"}))
                    self.editor.placeBlock((wall[0] + (wall[2] - wall[0]) // 2 - 1, self.coordinates_min[1], wall[1]),
                                           Block(self.blocks["stairs"], {"facing": "east"}))
                    self.editor.placeBlock((wall[0] + (wall[2] - wall[0]) // 2 + 2, self.coordinates_min[1], wall[1]),
                                           Block(self.blocks["stairs"], {"facing": "west"}))

                    self.editor.placeBlock((wall[0] + (wall[2] - wall[0]) // 2, self.coordinates_min[1] + 3, wall[1]),
                                           Block(self.blocks["stairs"], {"facing": "south", "half": "top"}))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 + 1,
                         self.coordinates_min[1] + 3, wall[1]),
                        Block(self.blocks["stairs"], {"facing": "south", "half": "top"}))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 - 1,
                         self.coordinates_min[1] + 3, wall[1]),
                        Block(self.blocks["stairs"], {"facing": "east", "half": "top"}))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 + 2,
                         self.coordinates_min[1] + 3, wall[1]),
                        Block(self.blocks["stairs"], {"facing": "west", "half": "top"}))

                    self.entranceCo = (wall[0] + (wall[2] - wall[0]) // 2, wall[0] + (wall[2] - wall[0]) // 2 + 2,
                                       wall[0] + (wall[2] - wall[0]) // 2 + 1, wall[0] + (wall[2] - wall[0]) // 2 - 1)

                else:
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2, self.coordinates_min[1] + 1, wall[1] + 1), Block("air"))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2, self.coordinates_min[1] + 2, wall[1] + 1), Block("air"))

                    self.editor.placeBlock((wall[0] + (wall[2] - wall[0]) // 2, self.coordinates_min[1], wall[1]),
                                           Block(self.blocks["stairs"], {"facing": "south"}))
                    self.editor.placeBlock((wall[0] + (wall[2] - wall[0]) // 2 + 1, self.coordinates_min[1], wall[1]),
                                           Block(self.blocks["stairs"], {"facing": "west"}))
                    self.editor.placeBlock((wall[0] + (wall[2] - wall[0]) // 2 - 1, self.coordinates_min[1], wall[1]),
                                           Block(self.blocks["stairs"], {"facing": "east"}))

                    self.editor.placeBlock((wall[0] + (wall[2] - wall[0]) // 2, self.coordinates_min[1] + 3, wall[1]),
                                           Block(self.blocks["stairs"], {"facing": "south", "half": "top"}))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 + 1,
                         self.coordinates_min[1] + 3, wall[1]),
                        Block(self.blocks["stairs"], {"facing": "west", "half": "top"}))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 - 1,
                         self.coordinates_min[1] + 3, wall[1]),
                        Block(self.blocks["stairs"], {"facing": "east", "half": "top"}))

                    self.entranceCo = (wall[0] + (wall[2] - wall[0]) // 2, wall[0] + (wall[2] - wall[0]) // 2 + 1,
                                       wall[0] + (wall[2] - wall[0]) // 2 + 1, wall[0] + (wall[2] - wall[0]) // 2 - 1)

            case "E":
                if (wall[3] - wall[1]) % 2 != 0:
                    self.editor.placeBlock((wall[0], self.coordinates_min[1] + 1, (wall[1] + wall[3]) // 2 + 1),
                                           Block("air"))
                    self.editor.placeBlock((wall[0], self.coordinates_min[1] + 2, (wall[1] + wall[3]) // 2 + 1),
                                           Block("air"))
                    self.editor.placeBlock((wall[0], self.coordinates_min[1] + 1, (wall[1] + wall[3]) // 2),
                                           Block("air"))
                    self.editor.placeBlock((wall[0], self.coordinates_min[1] + 2, (wall[1] + wall[3]) // 2),
                                           Block("air"))

                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1], (wall[1] + wall[3]) // 2),
                                           Block(self.blocks["stairs"], {"facing": "west"}))
                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1], (wall[1] + wall[3]) // 2 + 1),
                                           Block(self.blocks["stairs"], {"facing": "west"}))
                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1], (wall[1] + wall[3]) // 2 - 1),
                                           Block(self.blocks["stairs"], {"facing": "south"}))
                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1], (wall[1] + wall[3]) // 2 + 2),
                                           Block(self.blocks["stairs"], {"facing": "north"}))

                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1] + 3, (wall[1] + wall[3]) // 2),
                                           Block(self.blocks["stairs"], {"facing": "west", "half": "top"}))
                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1] + 3, (wall[1] + wall[3]) // 2 + 1),
                                           Block(self.blocks["stairs"], {"facing": "west", "half": "top"}))
                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1] + 3, (wall[1] + wall[3]) // 2 - 1),
                                           Block(self.blocks["stairs"], {"facing": "south", "half": "top"}))
                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1] + 3, (wall[1] + wall[3]) // 2 + 2),
                                           Block(self.blocks["stairs"], {"facing": "north", "half": "top"}))

                    self.entranceCo = (
                        (wall[1] + wall[3]) // 2, (wall[1] + wall[3]
                                                   ) // 2 + 2, (wall[1] + wall[3]) // 2 + 1,
                        (wall[1] + wall[3]) // 2 - 1)
                else:
                    self.editor.placeBlock((wall[0], self.coordinates_min[1] + 1, (wall[1] + wall[3]) // 2),
                                           Block("air"))
                    self.editor.placeBlock((wall[0], self.coordinates_min[1] + 2, (wall[1] + wall[3]) // 2),
                                           Block("air"))

                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1], (wall[1] + wall[3]) // 2),
                                           Block(self.blocks["stairs"], {"facing": "west"}))
                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1], (wall[1] + wall[3]) // 2 + 1),
                                           Block(self.blocks["stairs"], {"facing": "north"}))
                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1], (wall[1] + wall[3]) // 2 - 1),
                                           Block(self.blocks["stairs"], {"facing": "south"}))

                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1] + 3, (wall[1] + wall[3]) // 2),
                                           Block(self.blocks["stairs"], {"facing": "west", "half": "top"}))
                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1] + 3, (wall[1] + wall[3]) // 2 + 1),
                                           Block(self.blocks["stairs"], {"facing": "north", "half": "top"}))
                    self.editor.placeBlock((wall[0] + 1, self.coordinates_min[1] + 3, (wall[1] + wall[3]) // 2 - 1),
                                           Block(self.blocks["stairs"], {"facing": "south", "half": "top"}))

                    self.entranceCo = (
                        (wall[1] + wall[3]) // 2, (wall[1] + wall[3]
                                                   ) // 2 + 1, (wall[1] + wall[3]) // 2 + 1,
                        (wall[1] + wall[3]) // 2 - 1)

            case "S":
                print(wall)
                if (wall[2] - wall[0]) % 2 != 0:
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 + 1, self.coordinates_min[1] + 1, wall[1]), Block("air"))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 + 1, self.coordinates_min[1] + 2, wall[1]), Block("air"))
                    self.editor.placeBlock((wall[0] + (wall[2] - wall[0]) // 2, self.coordinates_min[1] + 1, wall[1]),
                                           Block("air"))
                    self.editor.placeBlock((wall[0] + (wall[2] - wall[0]) // 2, self.coordinates_min[1] + 2, wall[1]),
                                           Block("air"))

                    self.editor.placeBlock((wall[0] + (wall[2] - wall[0]) // 2, self.coordinates_min[1], wall[1] + 1),
                                           Block(self.blocks["stairs"], {"facing": "north"}))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 + 1,
                         self.coordinates_min[1], wall[1] + 1),
                        Block(self.blocks["stairs"], {"facing": "north"}))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 - 1,
                         self.coordinates_min[1], wall[1] + 1),
                        Block(self.blocks["stairs"], {"facing": "east"}))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 + 2,
                         self.coordinates_min[1], wall[1] + 1),
                        Block(self.blocks["stairs"], {"facing": "west"}))

                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2,
                         self.coordinates_min[1] + 3, wall[1] + 1),
                        Block(self.blocks["stairs"], {"facing": "north", "half": "top"}))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 + 1,
                         self.coordinates_min[1] + 3, wall[1] + 1),
                        Block(self.blocks["stairs"], {"facing": "north", "half": "top"}))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 - 1,
                         self.coordinates_min[1] + 3, wall[1] + 1),
                        Block(self.blocks["stairs"], {"facing": "east", "half": "top"}))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 + 2,
                         self.coordinates_min[1] + 3, wall[1] + 1),
                        Block(self.blocks["stairs"], {"facing": "west", "half": "top"}))

                    self.entranceCo = (wall[0] + (wall[2] - wall[0]) // 2, wall[0] + (wall[2] - wall[0]) // 2 + 2,
                                       wall[0] + (wall[2] - wall[0]) // 2 + 1, wall[0] + (wall[2] - wall[0]) // 2 - 1)
                else:
                    self.editor.placeBlock((wall[0] + (wall[2] - wall[0]) // 2, self.coordinates_min[1] + 1, wall[1]),
                                           Block("air"))
                    self.editor.placeBlock((wall[0] + (wall[2] - wall[0]) // 2, self.coordinates_min[1] + 2, wall[1]),
                                           Block("air"))

                    self.editor.placeBlock((wall[0] + (wall[2] - wall[0]) // 2, self.coordinates_min[1], wall[1] + 1),
                                           Block(self.blocks["stairs"], {"facing": "north"}))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 + 1,
                         self.coordinates_min[1], wall[1] + 1),
                        Block(self.blocks["stairs"], {"facing": "west"}))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 - 1,
                         self.coordinates_min[1], wall[1] + 1),
                        Block(self.blocks["stairs"], {"facing": "east"}))

                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2,
                         self.coordinates_min[1] + 3, wall[1] + 1),
                        Block(self.blocks["stairs"], {"facing": "north", "half": "top"}))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 + 1,
                         self.coordinates_min[1] + 3, wall[1] + 1),
                        Block(self.blocks["stairs"], {"facing": "west", "half": "top"}))
                    self.editor.placeBlock(
                        (wall[0] + (wall[2] - wall[0]) // 2 - 1,
                         self.coordinates_min[1] + 3, wall[1] + 1),
                        Block(self.blocks["stairs"], {"facing": "east", "half": "top"}))

                    self.entranceCo = (wall[0] + (wall[2] - wall[0]) // 2, wall[0] + (wall[2] - wall[0]) // 2 + 1,
                                       wall[0] + (wall[2] - wall[0]) // 2 + 1, wall[0] + (wall[2] - wall[0]) // 2 - 1)
            case _:
                pass

    def placeGardenOutline(self):
        x_min, y_min, z_min = self.coordinates_min
        x_max, y_max, z_max = self.coordinates_max
        for i in range(x_min, x_max):
            for y in range(z_min, z_max):
                if i == x_min or i == x_max - 1 or y == z_min or y == z_max - 1:
                    match self.direction:
                        case "N":
                            if not (i in self.entranceCo and y == z_min):
                                self.editor.placeBlock(
                                    (i, y_min - 1, y), Block("oak_log"))
                                self.editor.placeBlock(
                                    (i, y_min, y), self.gardenOutline)
                                self.editor.placeBlock(
                                    (i, y_min + 1, y), self.gardenOutline)
                                self.editor.placeBlock(
                                    (i, y_min + 2, y), self.gardenOutline)
                        case "S":
                            if not (i in self.entranceCo and y == z_max - 1):
                                self.editor.placeBlock(
                                    (i, y_min - 1, y), Block("oak_log"))
                                self.editor.placeBlock(
                                    (i, y_min, y), self.gardenOutline)
                                self.editor.placeBlock(
                                    (i, y_min + 1, y), self.gardenOutline)
                                self.editor.placeBlock(
                                    (i, y_min + 2, y), self.gardenOutline)
                        case "E":
                            if not (i == x_max - 1 and y in self.entranceCo):
                                self.editor.placeBlock(
                                    (i, y_min - 1, y), Block("oak_log"))
                                self.editor.placeBlock(
                                    (i, y_min, y), self.gardenOutline)
                                self.editor.placeBlock(
                                    (i, y_min + 1, y), self.gardenOutline)
                                self.editor.placeBlock(
                                    (i, y_min + 2, y), self.gardenOutline)

                        case "W":
                            if not (i == x_min and y in self.entranceCo):
                                self.editor.placeBlock(
                                    (i, y_min - 1, y), Block("oak_log"))
                                self.editor.placeBlock(
                                    (i, y_min, y), self.gardenOutline)
                                self.editor.placeBlock(
                                    (i, y_min + 1, y), self.gardenOutline)
                                self.editor.placeBlock(
                                    (i, y_min + 2, y), self.gardenOutline)

                        case _:
                            self.editor.placeBlock(
                                (i, y_min - 1, y), self.garden_floor)

                else:
                    self.editor.placeBlock(
                        (i, y_min - 1, y), self.garden_floor)

    def build(self):
        self.createHouseSkeleton()
        self.putWallOnSkeleton()
        self.placeDoor()
        self.placeRoof()
        self.putCelling()
        self.placeWindow()
        self.placeEntrance()
        self.placeGardenOutline()
        if self.nbEtage > 1:
            self.placeStairs()


if __name__ == "__main__":
    editor = Editor(buffering=True)
    buildArea = editor.getBuildArea()
    coordinates_min = [min(buildArea.begin[i], buildArea.last[i])
                       for i in range(3)]
    coordinates_max = [max(buildArea.begin[i], buildArea.last[i])
                       for i in range(3)]

    # blocks = {
    #     "wall": "blackstone",
    #     "roof": "blackstone",
    #     "roof_slab": "blackstone_slab",
    #     "door": "oak_door",
    #     "window": "glass_pane",
    #     "entrance": "oak_door",
    #     "stairs": "quartz_stairs",
    #     "stairs_slab": "quartz_slab",
    #     "celling": "quartz_block",
    #     "floor": "quartz_block",
    #     "celling_slab": "quartz_slab",
    #     "garden_outline": "oak_leaves",
    #     "garden_floor": "grass_block"
    # }

    blocks = {
        "wall": "stripped_oak_log",
        "roof": "smooth_stone",
        "roof_slab": "oak_slab",
        "door": "oak_door",
        "window": "glass_pane",
        "entrance": "oak_door",
        "stairs": "oak_stairs",
        "stairs_slab": "birch_slab",
        "celling": "stripped_oak_log",
        "floor": "stripped_oak_log",
        "celling_slab": "quartz_slab",
        "garden_outline": "oak_leaves",
        "garden_floor": "grass_block"
    }

    for i in range(1):
        house = House(editor, coordinates_min, coordinates_max, "W", blocks)

        house.build()

        new_coordinates_min = (
            coordinates_max[0] + 20, coordinates_min[1], coordinates_min[2])
        new_coordinates_max = (
            coordinates_max[0] + 10 + 40, coordinates_max[1], coordinates_max[2])
        coordinates_min = new_coordinates_min
        coordinates_max = new_coordinates_max

    # delete(editor, coordinates_min, coordinates_max)
    editor.flushBuffer()

import random as rd
from gdpc import Editor, Block, geometry
from utils.functions import *
from utils.Enums import BALCONY_BORDER_RADIUS, COLLUMN_STYLE
from buildings.geometry.Point import Point
from buildings.geometry.Vertice import Vertice

class Balcony:
    def __init__(self, rdata, max_width: int, windows, collumn_style: COLLUMN_STYLE):
        self.rdata = rdata
        self.windows = windows
        self.max_width = max_width
        self.collumn_style = collumn_style
        self.length = self.get_len()
        self.has_multiple = self.has_multiple()
        self.has_details = self.has_details()
        self.border_radius = self.has_border_radius()
        self.follow_window = not self.windows.ypadding > 3
        self.structure = self.get_structures()
        self.editor, self.materials = None, None

    def build(self, editor: Editor, materials: list[str]):
        self.editor = editor
        self.materials = materials
        place_block = editor.placeBlock  # Reduce attribute access in loops
        mat3, mat4 = materials[3], materials[4]
        
        for s in self.structure:
            s.fill(editor, materials[0])
            self.build_rembard(s, place_block, mat3)
            self.build_details(s, place_block, mat4)
            self.build_border_radius(s, place_block, mat3, mat4)

    def build_rembard(self, s: Vertice, place_block, mat3):
        x1, x2 = s.point1.x, s.point2.x
        length = self.length

        geometry.placeCuboid(self.editor, (x1, 1, -1), (x1, 1, -length), Block(mat3))
        geometry.placeCuboid(self.editor, (x2, 1, -1), (x2, 1, -length), Block(mat3))
        geometry.placeCuboid(self.editor, (x1, 1, -length), (x2, 1, -length), Block(mat3))

    def build_details(self, s: Vertice, place_block, mat4):
        if not self.has_details:
            return
        x1, x2 = s.point1.x, s.point2.x
        length = self.length

        geometry.placeCuboid(self.editor, (x1, 0, -1), (x1, 0, -length), Block(mat4, {"facing": "east", "half": "top"}))
        geometry.placeCuboid(self.editor, (x2, 0, -1), (x2, 0, -length), Block(mat4, {"facing": "west", "half": "top"}))
        geometry.placeCuboid(self.editor, (x1, 0, -length), (x2, 0, -length), Block(mat4, {"facing": "south", "half": "top"}))

    def build_border_radius(self, s: Vertice, place_block, mat3, mat4):
        if self.border_radius == BALCONY_BORDER_RADIUS.NONE:
            return

        x1, x2 = s.point1.x, s.point2.x
        length = self.length

        geometry.placeCuboid(self.editor, (x1, 0, -length), (x1, 1, -length), Block("air"))
        geometry.placeCuboid(self.editor, (x2, 0, -length), (x2, 1, -length), Block("air"))
        place_block((x1 + 1, 1, -length + 1), Block(mat3))
        place_block((x2 - 1, 1, -length + 1), Block(mat3))

        if self.has_details:
            place_block((x1, 0, -length + 1), Block(mat4, {"facing": "south", "half": "top"}))
            place_block((x1 + 1, 0, -length), Block(mat4, {"facing": "east", "half": "top"}))
            place_block((x2, 0, -length + 1), Block(mat4, {"facing": "south", "half": "top"}))
            place_block((x2 - 1, 0, -length), Block(mat4, {"facing": "west", "half": "top"}))

            if self.border_radius == BALCONY_BORDER_RADIUS.FULL:
                place_block((x1 + 1, 0, -length + 1), Block(mat4, {"facing": "east", "half": "top"}))
                place_block((x2 - 1, 0, -length + 1), Block(mat4, {"facing": "west", "half": "top"}))

    def get_structures(self) -> list[Vertice]:
        attach_points = self.get_attach_points()
        min_wid = self.rdata["size"]["min_width"]
        min_gap = self.rdata["multiple"]["min_gap"]
        growth_chance = self.rdata["growth"]
        midpoint = len(attach_points) // 2

        structures = []
        centered = True
        x1, x2 = midpoint, midpoint

        while x1 > 0:
            x1 -= 1
            if centered:
                x2 += 1
                if x2 >= len(attach_points):
                    break
            leng = attach_points[x2] - attach_points[x1] - 1

            if leng < min_wid:
                continue
            if x1 == 0 or growth_chance < rd.random():
                self.append_structure(structures, x1, x2, attach_points, centered)
                if not self.has_multiple:
                    break
                else:
                    centered = False
                    gap = rd.randint(min_gap, attach_points[x1] - min_wid)
                    if x1 - gap < 0:
                        break
                    x2 = x1 - gap
                    x1 = x2 - min_wid + 1

        return structures

    def get_attach_points(self) -> list[int]:
        padding = 0 if self.collumn_style.value < 2 else 1
        points = [i + padding for i in range(self.max_width)]
        if self.follow_window:
            pad = self.windows.padding
            for w in self.windows.windows:
                points = [p for p in points if not (pad + w.x1 <= p <= pad + w.x2)]
        return points

    def append_structure(self, structures: list[Vertice], x1: int, x2: int, attach_points: list[int], centered: bool):
        structures.append(Vertice(Point(x=attach_points[x1]), Point(x=attach_points[x2], z=-self.length)))
        if not centered:
            structures.append(Vertice(Point(x=attach_points[-x1]), Point(x=attach_points[-x2], z=-self.length)))

    def has_multiple(self) -> bool:
        return self.max_width >= self.rdata["multiple"]["min_width"] and self.rdata["multiple"]["proba"] >= rd.random()

    def has_details(self) -> bool:
        return self.rdata["details"] >= rd.random()

    def has_border_radius(self) -> bool:
        return BALCONY_BORDER_RADIUS.NONE if self.length < 2 else select_random(self.rdata["border_radius"], BALCONY_BORDER_RADIUS)

    def get_len(self) -> int:
        return rd.randint(self.rdata["size"]["min_len"], self.rdata["size"]["max_len"])

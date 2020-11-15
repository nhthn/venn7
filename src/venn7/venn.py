import json
import logging
import math
import os
import pathlib
import subprocess

import numpy as np
import shapely.geometry
import shapely.affinity

import venn7.bezier
from venn7.bezier import MetafontBezier
from venn7.bezier import MetafontSpline
from venn7.bezier import BezierPath

ROOT = pathlib.Path(os.path.realpath(__file__)).parent

class VennDiagram:
    """A simple, polar symmetric monotone Venn diagram represented with a
    compact matrix encoding.

    Reference: Cao et al. "Symmetric Monoton Venn Diagrams with Seven Curves."

    Glossary
    --------

    simple: only two curves may intersect at any point (no triple intersections).
    polar symmetric: n-fold rotational symmetry, where n is the order of the diagram.
    monotone: every k-region (region intersecting exactly k curves) is adjacent to a
    k-1-region if possible and a k+1-region if possible.
    matrix encoding: an (n-1) by (2^n - 2)/n matrix of 1's and 0's. There is exactly
    one 1 in every column, the rest are zeros. Each 1 indicates a crossing over of
    two curves.
    compact matrix encoding: a list giving the 1-indexed row position of the 1 in each
    column.
    """

    def __init__(self, n, weave_code):
        self.n = n

        self.condensed_code = self.parse_weave_code(weave_code)
        self.code = [y for x in self.condensed_code for y in x]

        self.validate_basic()
        self.validate_venn()

    def parse_weave_code(self, weave_code):
        rows = weave_code.strip().split()
        matrix = []
        for i, row in enumerate(rows):
            interpolated_row = "0".join(row)
            if i % 2 == 0:
                interpolated_row = "0" + interpolated_row
            else:
                interpolated_row = interpolated_row + "0"
            interpolated_row = [int(x) for x in interpolated_row]
            matrix.append(interpolated_row)

        code = []
        for column in range(len(matrix[0])):
            code_entry = []
            for row in range(len(matrix)):
                if matrix[row][column] == 1:
                    code_entry.append(row + 1)
            code.append(code_entry)
        return code

    def validate_basic(self):
        """Check for basic errors in the matrix code."""
        n = self.n
        expected_length = (2 ** n - 2) // n
        if len(self.code) != expected_length:
            raise ValueError(f"Wrong length: code should be of length {expected_length}")

        last_x = self.code[-1]
        for x in self.code:
            if last_x == x:
                raise ValueError("Immediate repetitions are not allowed in code")
            last_x = x

        for k in range(1, n - 1):
            expected = math.comb(n, k) // n
            count = 0
            for x in self.code:
                if x == k:
                    count += 1
            if count != expected:
                raise ValueError(f"Expected {expected} instances of {k}")

    def validate_venn(self):
        """Check that this is in fact a Venn diagram."""
        n = self.n

        # I am not sure if this validation code is correct, sorry
        ranks = [False] * (2 ** n)
        ranks[0] = ranks[-1] = True
        p = list(range(n))
        for swap_row in self.full_code():
            a = swap_row
            b = swap_row - 1
            p[a], p[b] = p[b], p[a]
            rank = sum([2 ** x for x in p[swap_row:]])
            if ranks[rank]:
                raise ValueError(f"Duplicate rank {rank}")
            ranks[rank] = True
        if not all(ranks):
            raise ValueError(f"Not all ranks represented")

    def condense(self):
        """Condense adjacent swaps"""
        pass

    def full_code(self):
        """Return the code duplicated n times."""
        full_code = []
        for i in range(self.n):
            full_code += self.code
        return full_code

    def get_spline(self, index=0):
        grid_points = []
        row, column = 0, index * len(self.condensed_code)
        for i in range(self.n):
            for swap_rows in self.condensed_code:
                if row + 1 in swap_rows:
                    grid_points.append((row + 1, column))
                    row += 1
                elif row in swap_rows:
                    grid_points.append((row, column))
                    row -= 1
                column += 1

        grid_points_2 = []
        for i in range(len(grid_points)):
            r0, c0 = grid_points[(i - 1) % len(grid_points)]
            r1, c1 = grid_points[i]
            r2, c2 = grid_points[(i + 1) % len(grid_points)]
            if not (
                (c1 - c0) % len(grid_points) == 1
                and (c2 - c1) % len(grid_points) == 1
                and r2 - r1 == r1 - r0
            ):
                grid_points_2.append((r1, c1))
        grid_points = grid_points_2

        tensions = []
        for i in range(len(grid_points)):
            r1, c1 = grid_points[i]
            r2, c2 = grid_points[(i + 1) % len(grid_points)]
            if abs(r1 - r2) == abs(c1 - c2):
                tensions.append(1.8)
            else:
                tensions.append(1.0)

        inner_radius = 30
        spacing = 5

        control_points = []
        for row, column in grid_points:
            radius = inner_radius + spacing * row
            theta = column * 2 * math.pi / (self.n * len(self.condensed_code))
            x = radius * math.cos(theta)
            y = radius * math.sin(theta)
            control_points.append((x, y))

        spline = MetafontSpline(control_points, tensions)

        # Fudge factor to avoid perfectly coincident endpoints, which cause
        # issues for Boolean ops.
        spline = spline.translate(np.array([1e-4, 0]))

        return spline

    def get_polygon(self, index=0):
        """Get the shape of a single curve as a polygon."""
        spline = self.get_spline(index)
        resolution = 10
        points = []
        for bezier in spline.beziers:
            for i in range(resolution):
                points.append(bezier(i / resolution))
        return points

    def check_regions(self):
        """Approximate this Venn diagram with polygons and use Shapely to check
        that the diagram is valid."""
        original_curve = shapely.geometry.Polygon(self.get_polygon())
        curves = []
        for i in range(self.n):
            angle = 2 * math.pi * i / self.n
            curve = shapely.affinity.rotate(
                original_curve, angle, origin=(0, 0), use_radians=True
            )
            curves.append(curve)

        # Region at index 0 is an empty set.
        regions = [[]]
        for rank in range(1, 2 ** self.n):
            curves_included = []
            curves_excluded = []
            tmp_rank = rank
            for i in range(self.n):
                if tmp_rank % 2 == 0:
                    curves_excluded.append(curves[i])
                else:
                    curves_included.append(curves[i])
                tmp_rank //= 2

            region = curves_included[0]
            for curve in curves_included[1:]:
                region = region.intersection(curve)
            for curve in curves_excluded:
                region = region.difference(curve)

            assert not region.is_empty

    def export_json(self):
        result = {
            "n": self.n,
            "curve": self.get_spline().as_svg_path(),
        }

        process = subprocess.run(
            ["node", str(ROOT / "venn_boolean.js")],
            check=True,
            capture_output=True,
            input=json.dumps(result),
            encoding="utf-8",
        )
        result["regions"] = json.loads(process.stdout)

        return result

    def plot(self):
        import matplotlib.pyplot as plt
        import matplotlib.patches
        import matplotlib.collections

        fig, ax = plt.subplots()
        polygons = [matplotlib.patches.Polygon(self.get_polygon(i)) for i in range(diagram.n)]
        patches = matplotlib.collections.PatchCollection(polygons, alpha=0.2)
        ax.add_collection(patches)
        plt.xlim(-100, 100)
        plt.ylim(-100, 100)
        plt.show()

DIAGRAMS = {
    "victoria": VennDiagram(7, "100000 110010 110111 101111 001101 000100"),
    "adelaide": VennDiagram(7, "10000 11010 11111 11111 01101 00100"),
    "massey": VennDiagram(7, "100000 110001 110111 111110 111000 010000"),
    "manawatu": VennDiagram(7, "1000000 1000101 1101101 0111011 0011010 0010000"),
    "palmerston_north": VennDiagram(7, "1000000 1100010 1110110 1011101 0001101 0000100"),
    "hamilton": VennDiagram(7, "10000 10101 11111 11111 11010 10000")
}

if __name__ == "__main__":
    import json
    diagrams_json = {}
    for name, diagram in DIAGRAMS.items():
        diagrams_json[name] = diagram.export_json()

    with open("app/venn_diagrams.js", "w") as f:
        f.write("const venn_diagrams = ");
        json.dump(diagrams_json, f)
        f.write(";");

    DIAGRAMS["victoria"].plot()

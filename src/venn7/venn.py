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
    """A simple symmetric monotone Venn diagram. The diagram is encoded discretely
    using a set of "row swaps." Creation of path data is performed on the fly.

    See README for more info.

    Parameters
    ----------

    n : int
        The order of the Venn diagram. Must be prime.

    matrix_encoding_string : str
        A string containing whitespace-separated rows of the "matrix encoding."
        See README for example.
    """

    def __init__(self, n, matrix_encoding_string, name=None, renderer_args=None):
        self.name = name
        self.n = n

        self.row_swaps = self.parse_matrix_encoding_string(
            matrix_encoding_string
        )
        self.flattened_row_swaps = [y for x in self.row_swaps for y in x]

        self.renderer_args = renderer_args
        if self.renderer_args is None:
            self.renderer_args = {}

        self.validate_basic()
        self.validate_venn()

    def parse_matrix_encoding_string(self, matrix_encoding_string):
        rows = matrix_encoding_string.strip().splitlines()
        matrix = [[int(c) for c in line.strip()] for line in rows]

        row_swaps = []
        for column in range(len(matrix[0])):
            entry = []
            for row in range(len(matrix)):
                if matrix[row][column] == 1:
                    entry.append(row + 1)
            row_swaps.append(entry)
        return row_swaps

    def validate_basic(self):
        """Check for basic errors in the matrix flattened_row_swaps."""
        n = self.n
        expected_length = (2 ** n - 2) // n
        if len(self.flattened_row_swaps) != expected_length:
            raise ValueError(
                f"Wrong length: flattened_row_swaps should be of length {expected_length}"
            )

        last_x = self.flattened_row_swaps[-1]
        for x in self.flattened_row_swaps:
            if last_x == x:
                raise ValueError(
                    "Immediate repetitions are not allowed in flattened_row_swaps"
                )
            last_x = x

        for k in range(1, n - 1):
            expected = math.comb(n, k) // n
            count = 0
            for x in self.flattened_row_swaps:
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
        for swap_row in self.full_flattened_row_swaps():
            a = swap_row
            b = swap_row - 1
            p[a], p[b] = p[b], p[a]
            rank = sum([2 ** x for x in p[swap_row:]])
            if ranks[rank]:
                raise ValueError(f"Duplicate rank {rank}")
            ranks[rank] = True
        if not all(ranks):
            raise ValueError(f"Not all ranks represented")

    def full_flattened_row_swaps(self):
        """Return the flattened_row_swaps duplicated n times."""
        full_flattened_row_swaps = []
        for i in range(self.n):
            full_flattened_row_swaps += self.flattened_row_swaps
        return full_flattened_row_swaps

    def get_spline(self, index=0):
        renderer = VennDiagramRenderer(self, **self.renderer_args)
        return renderer.get_spline()

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
            "name": self.name,
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
        polygons = [
            matplotlib.patches.Polygon(self.get_polygon(i)) for i in range(diagram.n)
        ]
        patches = matplotlib.collections.PatchCollection(polygons, alpha=0.2)
        ax.add_collection(patches)
        plt.xlim(-100, 100)
        plt.ylim(-100, 100)
        plt.show()


class VennDiagramRenderer:
    """A class that renders discrete Venn diagrams to splines."""

    def __init__(
        self,
        venn_diagram,
        inner_radius=30,
        spacing=5,
        tension_diagonal=3.0,
        tension_default=1.0,
    ):
        self.n = venn_diagram.n
        self.row_swaps = venn_diagram.row_swaps

        self.inner_radius = inner_radius
        self.spacing = spacing
        self.tension_diagonal = tension_diagonal
        self.tension_default = tension_default

        # Avoid perfectly coincident endpoints, which causes
        # issues for Boolean ops.
        self.fudge_factor = 1e-4

    def _get_curve_points_on_cylinder(self, index):
        """Get the set of control points (not Bezier but Metafont control
        points) if the Venn diagram were unraveled on a cylinder. All these
        points lie on a grid.

        Each point is of the form (x, y, type). x is the circular coordinate
        which wraps around from 0 to len(self.row_swaps). y is the other,
        non-circular component which ranges from 0 to self.n - 1 inclusive.

        type is a string used to tag points with information about the point.
        This method generates two:

        - intersection_+ means that the curve is going up at this point.
        - intersection_- means that the curve is going down at this point.
        """
        points = []
        row, column = 0, index * len(self.row_swaps)
        for i in range(self.n):
            for swap_rows in self.row_swaps:
                if row + 1 in swap_rows:
                    points.append((row + 1, column, "intersection_+"))
                    row += 1
                elif row in swap_rows:
                    points.append((row, column, "intersection_-"))
                    row -= 1
                column += 1
        return points

    def _add_arc_points(self, points):
        """Given a set of control points on the cylinder, find pairs of points
        that are horizontal and insert new arc points to help round out the
        curve in that region. It is assumed that all points are intersection type.
        """
        squash_factor = len(self.row_swaps)

        result = []
        for i in range(len(points)):
            r1, c1, type_1 = point = points[i]
            r2, c2, type_2 = points[(i + 1) % len(points)]
            result.append(point)
            if r1 == r2 and r1 == self.n - 1:
                radius = (c2 - c1) % len(self.n * self.row_swaps) * 0.5
                column = c1 + radius
                if type_1 == "intersection_+" and type_2 == "intersection_-":
                    arc_direction = 1
                    type_ = "arc_+"
                elif type_1 == "intersection_-" and type_2 == "intersection_+":
                    arc_direction = -1
                    type_ = "arc_-"
                else:
                    raise RuntimeError
                vertical_radius = arc_direction * radius * 0.5
                ratio = 0.6
                result.append((r1 + vertical_radius * ratio, column - radius * ratio, type_))
                result.append((r1 + vertical_radius, column, type_))
                result.append((r1 + vertical_radius * ratio, column + radius * ratio, type_))
        return result

    def _get_tensions(self, points):
        """Given a set of control points on the cylinder, determine whether
        each pair of points is diagonal or horizontal. If they are diagonal and
        both are of "intersection" type, their tension is set to
        ``tension_diagonal``. Otherwise, their tension is ``tension_default``.
        Collect a list of all tensions and return it.
        """
        tensions = []
        for i in range(len(points)):
            r1, c1, type_1 = points[i]
            r2, c2, type_2 = points[(i + 1) % len(points)]
            if (
                type_1.startswith("intersection_") and type_2.startswith("intersection_")
                and type_1 == type_2
            ):
                tensions.append(self.tension_diagonal)
            else:
                tensions.append(self.tension_default)
        return tensions

    def _convert_cylinder_points_to_polar(self, cylinder_points):
        polar_points = []
        for row, column, __ in cylinder_points:
            radius = self.inner_radius + self.spacing * row
            theta = column * 2 * math.pi / (self.n * len(self.row_swaps))
            x = radius * math.cos(theta)
            y = radius * math.sin(theta)
            polar_points.append((x, y))
        return polar_points

    def _normalize_rotation_and_scaling(self, spline):
        """Given a spline, rotate and uniformly scale it so that its furthest
        point from the origin is transformed to (0, -50)."""
        x, y = spline.get_furthest_point_from((0, 0))
        angle = np.arctan2(y, x)
        scale = np.hypot(x, y)
        return spline.transform(
            venn7.bezier.get_rotation_matrix(-np.pi * 0.5 - angle) * 50 / scale
        )

    def get_spline(self, index=0):
        """Render a single curve of the Venn diagram to a BezierSpline
        and return the result.

        Parameters
        ----------

        index : int
            Which curve to return. For a symmetric Venn diagram, indices
            other than 0 are rotations of each other.
        """
        cylinder_points = self._get_curve_points_on_cylinder(index)
        cylinder_points = self._add_arc_points(cylinder_points)
        tensions = self._get_tensions(cylinder_points)

        control_points = self._convert_cylinder_points_to_polar(cylinder_points)
        spline = MetafontSpline(control_points, tensions)

        spline = self._normalize_rotation_and_scaling(spline)
        spline = spline.translate(np.array([self.fudge_factor, 0]))

        return spline


DIAGRAMS_LIST = [
    "victoria",
    "adelaide",
    "massey",
    "manawatu",
    "palmerston_north",
    "hamilton",
    "5",
]

DIAGRAMS = {
    "victoria": VennDiagram(
        7,
        """
        010000000000
        101000001000
        010100010101
        100010101010
        000001010001
        000000100000
        """,
        "Victoria",
        ),
    "adelaide": VennDiagram(
        7,
        """
        0100000000
        1010001000
        0101010101
        1010101010
        0001010001
        0000100000
        """,
        "Adelaide",
    ),
    "massey": VennDiagram(
        7,
        """
        010000000000
        101000000010
        010100010101
        101010101000
        010101000000
        001000000000
        """,
        "Massey",
    ),
    "manawatu": VennDiagram(
        7,
        """
        00001000000000
        10000000100100
        01010001010001
        00101010001010
        00000100100100
        01000000000000
        """,
        "Manawatu",
    ),
    "palmerston_north": VennDiagram(
        7,
        """
        10000000000000
        00100000001010
        01010100010100
        10001010100010
        00000001000101
        00000000010000
        """,
        "Palmerston North",
    ),
    "hamilton": VennDiagram(
        7,
        """
        0010000000
        1000100010
        0101010101
        1010101010
        0101000100
        0000000001
        """,
        "Hamilton",
    ),
    "5": VennDiagram(
        5,
        """
        1000
        0101
        1010
        0001
        """,
        "Symmetrical 5-Venn diagram",
        renderer_args={
            "inner_radius": 10,
            "spacing": 8,
            "tension_diagonal": 1,
            "tension_default": 1,
        },
    ),
}

if __name__ == "__main__":
    import json
    import sys

    diagrams_json = {}
    diagrams_json["diagrams_list"] = DIAGRAMS_LIST
    for name, diagram in DIAGRAMS.items():
        diagrams_json[name] = diagram.export_json()

    with open(sys.argv[1], "w") as f:
        f.write("const venn_diagrams = ")
        json.dump(diagrams_json, f)
        f.write(";")

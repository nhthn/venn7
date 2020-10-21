import math
from spline import Spline

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

    def __init__(self, n, code):
        self.n = n
        self.code = code
        self.validate_basic()
        self.validate_venn()

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

    def condensed_code(self):
        """Return a variant of the code where swaps are merged together
        vertically. Easiest to explain with examples:

        [1, 2, 3, 4, 3, 2] -> [[1], [2], [3], [4], [3], [2]]
        [1, 2, 4, 3, 2] -> [[1], [2, 4], [3], [2]]
        [1, 2, 3, 4, 1, 2, 3, 2] -> [[1], [2], [1, 3], [2, 4], [3], [2]]
        """
        # Locate first discontinuity.
        for i in range(len(self.code)):
            current = self.code[i]
            previous = self.code[(i - 1) % len(self.code)]
            if abs(current - previous) > 1:
                discontinuity_index = i
                break
        else:
            # No discontinuities at all... not sure if this is possible.
            raise ValueError("This shouldn't happen")
        # Rotate code to first discontinuity.
        code = self.code[discontinuity_index:] + self.code[:discontinuity_index]

        # Step 1: split into chunks.
        chunks = []
        for i in range(len(code)):
            current = code[i]
            previous = code[(i - 1) % len(self.code)]
            if abs(current - previous) > 1:
                chunks.append([])
            chunks[-1].append(current)

        print(chunks)

    def make_spline(self, index=0):
        """Produce a nice curved shape."""
        unraveled_points = []
        row, column = 0, index * ((2 ** self.n - 2) // self.n)
        for swap_row in self.full_code():
            if row == swap_row - 1:
                row += 1
                unraveled_points.append((swap_row, column, -0.25 * math.pi))
            elif row == swap_row:
                row -= 1
                unraveled_points.append((swap_row, column, 0.25 * math.pi))
            column += 1

        inner_radius = 20
        spacing = 10

        # Stage 2: Cartesian coordinates
        control_points = []
        for row, column, angle in unraveled_points:
            radius = inner_radius + spacing * row
            theta = column * 2 * math.pi / (2 ** self.n - 2)
            new_angle = angle + theta + math.pi * 0.5
            x = radius * math.cos(theta)
            y = radius * math.sin(theta)
            control_points.append((x, y, new_angle))

        # Stage 3: Splines
        splines = []
        for i in range(len(control_points)):
            x_1, y_1, theta_1 = control_points[i]
            x_2, y_2, theta_2 = control_points[(i + 1) % len(control_points)]
            spline = Spline(x_1, y_1, x_2, y_2, theta_1, theta_2)
            splines.append(spline)

        # Stage 4: Final points
        points = []
        for spline in splines:
            for i in range(10):
                points.append(spline.curve(i / 10))

        return points

    def make_polyline(self, index=0):
        """Produce an ugly polygonal shape."""
        # Stage 1: "combinatorial points"
        row, column = 0, index * ((2 ** self.n - 2) // self.n)
        combinatorial_points = [(row, column)]
        for swap_row in self.full_code():
            if row == swap_row - 1:
                row += 1
            elif row == swap_row:
                row -= 1
            column += 1
            combinatorial_points.append((row, column))

        inner_radius = 30
        spacing = 10

        # Stage 2: polar coordinates
        polar_points = [
            (
                inner_radius + spacing * row,
                column * 2 * math.pi / (2 ** self.n - 2)
            )
            for row, column in combinatorial_points
        ]

        # Stage 3: Cartesian coordinates
        points = [
            (r * math.cos(theta), r * math.sin(theta))
            for r, theta in polar_points
        ]

        return points


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    from matplotlib.collections import PatchCollection

    # Victoria
    diagram = VennDiagram(7, [1, 3, 2, 3, 4, 5, 4, 3, 6, 5, 4, 2, 3, 4, 3, 5, 4, 2])

    fig, ax = plt.subplots()
    polygons = [Polygon(diagram.make_spline(i)) for i in range(diagram.n)]
    patches = PatchCollection(polygons, alpha=0.2)
    ax.add_collection(patches)
    plt.xlim(-100, 100)
    plt.ylim(-100, 100)
    plt.show()

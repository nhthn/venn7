import json
import math
import subprocess
import numpy as np
import numpy.polynomial as polynomial
import sympy
import sympy.polys.polytools


class DegenerateBezierError(Exception):
    pass


class CubicBezier:

    def __init__(self, control_points):
        self.control_points = np.array(control_points)

    @classmethod
    def from_beziertool_json(cls, bezier_json):
        supporting_curve_json = bezier_json["supporting_curve"]
        supporting_curve = cls([
            (point["x"], point["y"])
            for point in supporting_curve_json["control_points"]
        ])
        t_source = bezier_json["t_source"]
        t_target = bezier_json["t_target"]
        if np.allclose(t_source, t_target):
            raise DegenerateBezierError
        return supporting_curve.clip(t_source, t_target)

    @staticmethod
    def f(t, x0, x1, x2, x3):
        s = 1 - t
        return (
            s * s * s * x0
            + 3 * t * s * s * x1
            + 3 * t * t * s * x2
            + t * t * t * x3
        )

    def __call__(self, t):
        x = self.f(t, *self.control_points[:, 0])
        y = self.f(t, *self.control_points[:, 1])
        return np.squeeze(np.vstack([x, y]).T)

    def clip(self, t_1, t_2):
        """Return a new CubicBezier that is the result of truncating this one's
        parameter to the interval [t_1, t_2]."""
        c = [sympy.Symbol(f"c{i}") for i in range(4)]
        t = sympy.Symbol("t")

        # We have the equation
        # f(t, c0', c1', c2', c3') = f(t_1 + t * (t_2 - t_1), c0, c1, c2, c3).
        # c0-3 are known but and c0-3' are unknown. Two polynomials are equal
        # if their coefficients are equal. Identify the linear combinations of
        # c and c' variables in the coefficients of t-terms, and produce the
        # matrix equation L c' = R c which can be solved with a linear systems
        # solver. Two 4x4 systems must be solved, one for x-coordinates and
        # one for y-coordinates.

        # In SymPy, polynomials cannot have variables in coefficients, so the
        # polynomial in t is treated as a multivariate polynomial. When using
        # coeff_monomial to exact coefficients, we have to treat c-variables
        # as dependent variables on the polynomial.

        rhs_poly = sympy.poly(self.f(t_1 + t * (t_2 - t_1), *c))
        rhs_matrix = np.zeros((4, 4))
        for i in range(4):
            for j in range(4):
                rhs_matrix[i, j] = rhs_poly.coeff_monomial(t ** i * c[j])

        # Note: lhs_matrix is constant, and equal to:
        #      1  0  0  0
        #     -3  3  0  0
        #      3 -6  3  0
        #     -1  3 -3  1
        # but it's more fun to derive from first principles.

        lhs_poly = sympy.poly(self.f(t, *c))
        lhs_matrix = np.zeros((4, 4))
        for i in range(4):
            for j in range(4):
                lhs_matrix[i, j] = lhs_poly.coeff_monomial(t ** i * c[j])

        x = np.linalg.solve(lhs_matrix, rhs_matrix @ self.control_points[:, 0])
        y = np.linalg.solve(lhs_matrix, rhs_matrix @ self.control_points[:, 1])

        return CubicBezier(np.vstack([x, y]).T)

    def as_json(self):
        points_json = []
        for i in range(3):
            points_json.append({
                "x": self.control_points[i, 0],
                "y": self.control_points[i, 1]
            })
        return points_json


class MetafontBezier(CubicBezier):
    """A cubic Bezier initialized using METAFONT-style specifications rather
    than control points. A METAFONT Bezier is specified by its two endpoints,
    the direction of the curve at the endpoints as angles, and two "tension"
    parameters.

    Angles are always given in radians. If relative_angles is True, the angles
    are given relative to a line connecting the two endpoints, and are equivalent
    to the variables "theta" and "phi" in the Hobby paper. Otherwise, the
    angles are absolute.
    """

    def __init__(
        self,
        x_1,
        y_1,
        x_2,
        y_2,
        theta_1,
        theta_2,
        tension_1=1.0,
        tension_2=1.0,
        *,
        relative_angles=False,
    ):
        self.x_1, self.y_1 = x_1, y_1
        self.x_2, self.y_2 = x_2, y_2

        if relative_angles:
            self.theta_1, self.theta_2 = theta_1, theta_2
        else:
            base_angle = math.atan2(self.y_2 - self.y_1, self.x_2 - self.x_1)
            self.theta_1, self.theta_2 = theta_1 - base_angle, base_angle - theta_2
        self.tension_1, self.tension_2 = tension_1, tension_2

        st1 = math.sin(self.theta_1)
        st2 = math.sin(self.theta_2)
        ct1 = math.cos(self.theta_1)
        ct2 = math.cos(self.theta_2)

        a = math.sqrt(2)
        b = 1 / 16
        c = (3 - math.sqrt(5)) / 2
        alpha = a * (st1 - b * st2) * (st2 - b * st1) * (ct1 - ct2)
        self.rho = (2 + alpha) / (1 + (1 - c) * ct1 + c * ct2)
        self.sigma = (2 - alpha) / (1 + (1 - c) * ct2 + c * ct1)

        point_1 = (0, 0)
        tmp_1 = self.rho / (3 * self.tension_1)
        point_2 = (tmp_1 * ct1, tmp_1 * st1)
        tmp_2 = self.sigma / (3 * self.tension_2)
        point_3 = (1 - tmp_2 * ct2, tmp_2 * st2)
        point_4 = (1, 0)
        control_points = [point_1, point_2, point_3, point_4]
        control_points = [
            self.transform_from_normalized_coordinates(*x)
            for x in control_points
        ]
        super().__init__(control_points)

    def transform_from_normalized_coordinates(self, x_hat, y_hat):
        x = self.x_1 + (self.x_2 - self.x_1) * x_hat + (self.y_1 - self.y_2) * y_hat
        y = self.y_1 + (self.y_2 - self.y_1) * x_hat + (self.x_2 - self.x_1) * y_hat
        return (x, y)


class BezierPath:

    def __init__(self, beziers):
        self.beziers = beziers

    @classmethod
    def from_beziertool_json(cls, path_json):
        beziers = []
        for x in path_json["outer_boundary"]:
            try:
                beziers.append(CubicBezier.from_beziertool_json(x))
            except DegenerateBezierError:
                pass
        return cls(beziers)

    def plot(self):
        import matplotlib.pyplot as plt
        for bezier in self.beziers:
            t = np.linspace(0, 1, 20, endpoint=False)
            points = bezier(t)
            x = points[:, 0]
            y = points[:, 1]
            plt.scatter(x, y)
        plt.show()

    def as_json(self):
        result = []
        for bezier in self.beziers:
            result += bezier.as_json()
        return {"points": result}

    def intersect(self, other):
        json_ = {
            "curves": [
                self.as_json(),
                other.as_json(),
            ],
        }
        with open("curves.json", "w") as f:
            json.dump(json_, f)
        process = subprocess.run(
            ["beziertool/beziertool", "curves.json"],
            check=True,
            stdout=subprocess.PIPE,
        )
        result = json.loads(process.stdout)
        return BezierPath.from_beziertool_json(result["polygons"][0])

class MetafontSpline(BezierPath):

    def __init__(self, points, tensions=None):
        self.points = np.array(points)
        n = self.number_of_points = self.points.shape[0]

        displacements = np.roll(self.points, 1, axis=0) - self.points
        distances = np.hypot(displacements[:, 1], displacements[:, 0])
        angle = np.arctan2(displacements[:, 1], displacements[:, 0])
        psi = np.roll(angle, -1) - angle
        psi = (psi + np.pi) % (2 * np.pi) - np.pi

        # In the Hobby paper, tension_after = tau, tension_before = tau with overline.
        if tensions is None:
            self.tension_after = np.ones(n)
            self.tension_before = np.ones(n)
        else:
            self.tension_after = tensions
            self.tension_before = np.roll(tensions, 1)

        # system of equations:
        # mock_curvature(phi[i], theta[i - 1], tension_before[i], tension_before[i - 1]) / distances[i - 1]
        # - mock_curvature(theta[i], phi[i + 1], tension_after[i], tension_before[i + 1]) / distances[i] = 0
        # phi[i] + theta[i] = -psi[i]

        # mock_curvature(theta, phi, tension_after, tension_before)
        # = tension_after^2 (2 * (theta + phi) / tension_before - 6 * theta)
        # = tension_after^2 * (2 / tension_before - 6) theta
        # + tension_after^2 * (2 / tension_before) * phi

        def theta(i):
            return i % n
        def phi(i):
            return n + i % n
        def d(i):
            return distances[i % n]

        A = np.zeros((n * 2, n * 2))
        b = np.zeros((n * 2,))
        row = 0

        def stamp_mock_curvature(theta, phi, tension_before, tension_after, scale):
            tmp = tension_after * tension_after
            A[row, theta] = tmp * (2 / tension_before - 6) * scale
            A[row, phi] = tmp * 2 / tension_before * scale

        for i in range(n):
            stamp_mock_curvature(
                phi(i),
                theta(i - 1),
                self.tension_before[i],
                self.tension_after[(i - 1) % n],
                scale=1 / d(i - 1)
            )
            stamp_mock_curvature(
                theta(i),
                phi(i + 1),
                self.tension_after[i],
                self.tension_before[(i + 1) % n],
                scale=-1 / d(i)
            )
            b[row] = 0
            row += 1
        for i in range(n):
            A[row, phi(i)] = 1
            A[row, theta(i)] = 1
            b[row] = -psi[i]
            row += 1

        x = np.linalg.solve(A, b)
        self.theta = x[:n]
        self.phi = x[n:]

        beziers = []
        for i in range(n):
            point_1 = self.points[i]
            point_2 = self.points[(i + 1) % n]
            bezier = MetafontBezier(
                point_1[0],
                point_1[1],
                point_2[0],
                point_2[1],
                self.theta[i],
                self.phi[(i + 1) % n],
                relative_angles=True
            )
            beziers.append(bezier)

        super().__init__(beziers)

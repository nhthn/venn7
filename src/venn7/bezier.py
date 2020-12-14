import json
import math
import subprocess
import numpy as np
import numpy.polynomial as polynomial


def get_rotation_matrix(theta):
    matrix = np.array(
        [
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)],
        ]
    )
    return matrix


class DegenerateBezierError(Exception):
    pass


class CubicBezier:
    def __init__(self, control_points):
        self.control_points = np.array(control_points)
        if self.control_points.shape != (4, 2):
            raise ValueError("Wrong shape, expected (4, 2)")

    def transform(self, matrix):
        return CubicBezier(self.control_points @ matrix.T)

    def translate(self, displacement):
        return CubicBezier(self.control_points + displacement[np.newaxis, :])

    @staticmethod
    def f(t, x0, x1, x2, x3):
        s = 1 - t
        return s * s * s * x0 + 3 * t * s * s * x1 + 3 * t * t * s * x2 + t * t * t * x3

    def __call__(self, t):
        x = self.f(t, *self.control_points[:, 0])
        y = self.f(t, *self.control_points[:, 1])
        return np.squeeze(np.vstack([x, y]).T)

    def get_furthest_point_from(self, point):
        """Given a point, find the point on this Bezier curve that is furthest
        from that point.

        The function to maximize is (f_x(t) - x) ** 2 + (f_y(t) - y) ** 2.

        Set derivative to zero:

            f_x'(t) (f_x(t) - x) + f_y'(t) (f_y(t) - y) = 0

        This is a 5th-degree polynomial. Find real roots in the interval [0, 1].
        Take all these real roots (some of which may be local maxima) along with
        f(0) and f(1) and find the furthest point.
        """
        x, y = point
        t = np.polynomial.Polynomial([0, 1])
        f_x = self.f(t, *self.control_points[:, 0])
        f_y = self.f(t, *self.control_points[:, 1])
        df_x = f_x.deriv()
        df_y = f_y.deriv()
        distance = (f_x - x) ** 2 + (f_y - y) ** 2
        optimizer = df_x * (f_x - x) + df_y * (f_y - y)
        roots = optimizer.roots()
        roots = np.real(roots[np.isreal(roots)])
        roots = roots[(0 < roots) & (roots < 1)]
        roots = np.concatenate([roots, [0, 1]])
        t = roots[np.argmax(distance(roots))]
        return (f_x(t), f_y(t))


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
            self.transform_from_normalized_coordinates(*x) for x in control_points
        ]
        super().__init__(control_points)

    def transform_from_normalized_coordinates(self, x_hat, y_hat):
        x = self.x_1 + (self.x_2 - self.x_1) * x_hat + (self.y_1 - self.y_2) * y_hat
        y = self.y_1 + (self.y_2 - self.y_1) * x_hat + (self.x_2 - self.x_1) * y_hat
        return (x, y)


class BezierPath:
    def __init__(self, beziers):
        self.beziers = beziers

    def transform(self, matrix):
        new_beziers = []
        for bezier in self.beziers:
            new_bezier = bezier.transform(matrix)
            new_beziers.append(new_bezier)
        return BezierPath(new_beziers)

    def translate(self, displacement):
        new_beziers = []
        for bezier in self.beziers:
            new_bezier = bezier.translate(displacement)
            new_beziers.append(new_bezier)
        return BezierPath(new_beziers)

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

    def as_svg_path(self):
        parts = []
        parts.append("M")
        parts.extend(self.beziers[0].control_points[0, :])
        for bezier in self.beziers:
            parts.append("C")
            for i in range(1, 4):
                parts.append(round(bezier.control_points[i, 0], 3))
                parts.append(round(bezier.control_points[i, 1], 3))
        return " ".join([str(x) for x in parts])

    def get_furthest_point_from(self, point):
        best = None
        best_distance = 0
        for bezier in self.beziers:
            candidate = bezier.get_furthest_point_from(point)
            distance = (
                (candidate[0] - point[0]) ** 2
                + (candidate[1] - point[1]) ** 2
            )
            if distance > best_distance:
                best = candidate
                best_distance = distance
        return best


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
                scale=1 / d(i - 1),
            )
            stamp_mock_curvature(
                theta(i),
                phi(i + 1),
                self.tension_after[i],
                self.tension_before[(i + 1) % n],
                scale=-1 / d(i),
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
                relative_angles=True,
            )
            beziers.append(bezier)

        super().__init__(beziers)

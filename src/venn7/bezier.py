import math
import numpy as np
import numpy.polynomial as polynomial
import sympy
import sympy.polys.polytools


class CubicBezier:

    def __init__(self, control_points):
        self.control_points = np.array(control_points)

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

    def get_t_from_x(self, x):
        """Draw a vertical line through the Bezier at the given x-coordinate
        and find one 0 <= t <= 1 where the Bezier intersects it. Raise an
        error if no roots, or more than one root, are found."""
        t = polynomial.Polynomial([0, 1])
        f = self.f(t, *self.control_points[:, 0])
        g = f - x
        roots = g.roots()
        if len(roots) == 0:
            raise RuntimeError("No roots")
        valid_roots = roots[np.isreal(roots) & (0.0 <= roots <= 1.0)]
        if len(roots) == 0:
            raise RuntimeError("No valid roots")
        if len(valid_roots) == 2:
            raise RuntimeError("Too many roots: {len(valid_roots)}")
        return valid_roots[0]

    def clip(self, source, target):
        """Return a new CubicBezier that starts at the given source point and
        ends at the given target point. The points are assumed to be on the
        curve."""
        t_1 = self.get_t_from_x(source[0])
        t_2 = self.get_t_from_x(target[0])

        c = [sympy.Symbol(f"c{i}") for i in range(4)]
        t = sympy.Symbol("t")

        # We have the equation
        # f(t, c0', c1', c2', c3') = f(t_1 + t * (t_2 - t_1), c0, c1, c2, c3).
        # c0-3 are known but and c0-3' are unknown. Two polynomials are equal
        # if their coefficients are equal. Identify the linear combinations of
        # c and c' variables in the coefficients of t-terms, and produce the
        # matrix equation L c' = R c which can be solved with a linear systems
        # solver.

        # In SymPy, polynomials cannot have variables in coefficients, so the
        # polynomial in t is treated as a multivariate polynomial. When using
        # coeff_monomial to exact coefficients, we have to treat c-variables
        # as dependent variable son the polynomial.

        rhs_poly = sympy.poly(self.f(t_1 + t * (t_2 - t_1), *c))
        rhs_matrix = np.zeros((4, 4))
        for i in range(4):
            for j in range(4):
                rhs_matrix[i, j] = rhs_poly.coeff_monomial(t ** i * c[j])

        lhs_poly = sympy.poly(self.f(t, *c))
        lhs_matrix = np.zeros((4, 4))
        for i in range(4):
            for j in range(4):
                lhs_matrix[i, j] = lhs_poly.coeff_monomial(t ** i * c[j])

        x = np.linalg.solve(lhs_matrix, rhs_matrix @ self.control_points[:, 0])
        y = np.linalg.solve(lhs_matrix, rhs_matrix @ self.control_points[:, 1])

        return CubicBezier(np.vstack([x, y]).T)


class MetafontBezier(CubicBezier):

    def __init__(self, x_1, y_1, x_2, y_2, theta_1, theta_2, tension_1=1.0, tension_2=1.0):
        self.x_1, self.y_1 = x_1, y_1
        self.x_2, self.y_2 = x_2, y_2

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


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    spline = Spline(
        x_1=0.0,
        y_1=0.0,
        x_2=0.0,
        y_2=1.0,
        theta_1=0.0,
        theta_2=math.pi * 0.25,
    )
    points = [spline.curve(i / 100) for i in range(100 + 1)]
    plt.scatter(*zip(*points))

    points = spline.get_bezier_control_points()
    plt.scatter(*zip(*points))
    plt.show()

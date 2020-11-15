import pytest
import numpy as np
import venn7.bezier


class TestCubicBezier:

    def test_basic(self):
        bezier = venn7.bezier.CubicBezier([
            (0.0, 0.0),
            (1.0, 1.0),
            (2.0, 1.0),
            (3.0, 0.0),
        ])
        np.testing.assert_allclose(bezier(0.0), bezier.control_points[0])
        np.testing.assert_allclose(bezier(0.5), (1.5, 0.75))
        np.testing.assert_allclose(bezier(1.0), bezier.control_points[3])

        # Reflectional symmetry between initial and final halves of curve.
        np.testing.assert_allclose(
            bezier(np.linspace(0.0, 0.5, 10)),
            np.array([3.0, 0.0]) + bezier(np.linspace(1.0, 0.5, 10)) * np.array([-1, 1])
        )


class TestMetafontSpline:

    def test_basic(self):
        spline = venn7.bezier.MetafontSpline([
            (0.0, 1.0),
            (1.0, 0.0),
            (0.0, -1.0),
            (-1.0, 0.0),
        ])
        np.testing.assert_allclose(
            spline.beziers[0].control_points[0, :],
            spline.points[0]
        )

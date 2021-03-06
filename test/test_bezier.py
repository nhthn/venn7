import pytest
import numpy as np
import venn7.bezier


class TestCubicBezier:
    def test_basic(self):
        bezier = venn7.bezier.CubicBezier(
            [
                (0.0, 0.0),
                (1.0, 1.0),
                (2.0, 1.0),
                (3.0, 0.0),
            ]
        )
        np.testing.assert_allclose(bezier(0.0), bezier.control_points[0])
        np.testing.assert_allclose(bezier(0.5), (1.5, 0.75))
        np.testing.assert_allclose(bezier(1.0), bezier.control_points[3])

        # Reflectional symmetry between initial and final halves of curve.
        np.testing.assert_allclose(
            bezier(np.linspace(0.0, 0.5, 10)),
            np.array([3.0, 0.0])
            + bezier(np.linspace(1.0, 0.5, 10)) * np.array([-1, 1]),
        )

    def test_get_furthest_point(self):
        bezier = venn7.bezier.CubicBezier(
            [
                (0.0, 0.0),
                (1.0, 1.0),
                (2.0, 1.0),
                (3.0, 0.0),
            ]
        )
        point = (1.5, -3.0)
        furthest_point = bezier.get_furthest_point_from(point)
        np.testing.assert_allclose(furthest_point[0], 1.5)


class TestMetafontSpline:
    def test_basic(self):
        spline = venn7.bezier.MetafontSpline(
            [
                (0.0, 1.0),
                (1.0, 0.0),
                (0.0, -1.0),
                (-1.0, 0.0),
            ]
        )
        np.testing.assert_allclose(
            spline.beziers[0].control_points[0, :], spline.points[0]
        )


class TestSVGPathParser:
    def test_basic(self):
        parser = venn7.bezier.SVGPathParser("""
            M 1, 1
            c 1.0 1.0 2 2 3 3
            c1,1,2,2,3,3z
        """)
        path = venn7.bezier.BezierPath(parser.parse())
        np.testing.assert_allclose(
            path.beziers[0].control_points,
            np.array([
                [1.0, 1.0],
                [2.0, 2.0],
                [3.0, 3.0],
                [4.0, 4.0],
            ])
        )

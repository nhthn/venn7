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

    def test_clip(self):
        bezier = venn7.bezier.CubicBezier([
            (0.0, 0.0),
            (1.0, 1.0),
            (2.0, 2.0),
            (3.0, 0.0),
        ])

        t_start = 0.3
        t_end = 0.6
        new_bezier = bezier.clip(t_start, t_end)
        np.testing.assert_allclose(
            bezier(np.linspace(t_start, t_end, 10)),
            new_bezier(np.linspace(0, 1, 10)),
        )

    def test_clip_1(self):
        bezier = venn7.bezier.CubicBezier([
            [1.0, 0.0],
            [1.32753749, 0.58870814],
            [0.6883663, 1.28513066],
            [0.0, 1.0]
        ])
        #np.testing.assert_allclose(0.0, bezier.get_t_from_x(1.0))


class TestBezierPath:

    def test_intersection(self):
        path_1 = venn7.bezier.MetafontSpline([
            (0.0, 0.0),
            (1.0, 0.0),
            (0.0, 1.0),
        ])
        path_2 = venn7.bezier.MetafontSpline([
            (0.0, 1.0),
            (1.0, 1.0),
            (1.0, 0.0),
        ])
        path_1.intersect(path_2)


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

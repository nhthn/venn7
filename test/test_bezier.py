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

    def test_get_t_from_x(self):
        bezier = venn7.bezier.CubicBezier([
            (0.0, 0.0),
            (1.0, 1.0),
            (2.0, 2.0),
            (3.0, 0.0),
        ])

        t = 0.3
        x, y = bezier(t)
        t_2 = bezier.get_t_from_x(x)
        np.testing.assert_allclose(t, t_2)

    def test_clip(self):
        bezier = venn7.bezier.CubicBezier([
            (0.0, 0.0),
            (1.0, 1.0),
            (2.0, 2.0),
            (3.0, 0.0),
        ])

        t_start = 0.3
        t_end = 0.6
        new_bezier = bezier.clip(bezier(t_start), bezier(t_end))
        np.testing.assert_allclose(
            bezier(np.linspace(t_start, t_end, 10)),
            new_bezier(np.linspace(0, 1, 10)),
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

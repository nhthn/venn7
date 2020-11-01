#include <CGAL/CORE_algebraic_number_traits.h>
#include <CGAL/Cartesian.h>
#include <CGAL/Arr_Bezier_curve_traits_2.h>
#include <CGAL/Boolean_set_operations_2.h>
#include <CGAL/Polygon_set_2.h>
#include <CGAL/General_polygon_set_2.h>
#include <iostream>

typedef CGAL::CORE_algebraic_number_traits NtTraits;
typedef NtTraits::Rational Rational;
typedef NtTraits::Algebraic Algebraic;
typedef CGAL::Cartesian<Rational> RatKernel;
typedef CGAL::Cartesian<Algebraic> AlgKernel;
typedef CGAL::Arr_Bezier_curve_traits_2<RatKernel, AlgKernel, NtTraits> Traits_2;

typedef RatKernel::Point_2 Point_2;
typedef Traits_2::Curve_2 Bezier_curve_2;
typedef Traits_2::X_monotone_curve_2 X_monotone_curve_2;
typedef CGAL::Gps_traits_2<Traits_2> Gps_traits_2;
typedef Gps_traits_2::General_polygon_2 Polygon_2;
typedef Gps_traits_2::General_polygon_with_holes_2 Polygon_with_holes_2;
typedef CGAL::General_polygon_set_2<Gps_traits_2> Polygon_set;

class BezierPath {
public:
    BezierPath(std::vector<float> points)
        : m_points(points)
        , m_num_beziers(points.size() / 6)
        , m_make_x_monotone(m_traits.make_x_monotone_2_object())
    {
        int size = points.size();
        if (size % 6 != 0 || size < 6) {
            throw std::runtime_error("Must have 6n entries, for n > 1.");
        }

        for (int i = 0; i < m_num_beziers; i++) {
            makeBezierCurve(i);
        }
        fixPolygonOrientation();

        m_polygonSet.insert(m_polygon);
    };

    void intersect(BezierPath& other) {
        m_polygonSet.intersection(other.m_polygonSet);
    }

    void printInfo() {
        std::list<Polygon_with_holes_2> polygons;
        m_polygonSet.polygons_with_holes(std::back_inserter(polygons));
        std::cout << "Polygons: " << m_polygonSet.number_of_polygons_with_holes() << std::endl;
        for (auto polygon : polygons) {
            if (polygon.is_unbounded()) {
                std::cout << "Unbounded" << std::endl;
            }
            std::cout << "Number of holes: " << polygon.number_of_holes() << std::endl;
            // We ignore holes for this application.

            Polygon_2 outer_boundary = polygon.outer_boundary();

            Polygon_2::Curve_const_iterator iterator;
            for (iterator = outer_boundary.curves_begin(); iterator != outer_boundary.curves_end(); iterator++) {
                X_monotone_curve_2 x = *iterator;
                Bezier_curve_2 supporting_curve = x.supporting_curve();
                std::cout << "Curve: " << supporting_curve << std::endl;
                std::cout << "Start: " << x.source() << std::endl;
                std::cout << "End: " << x.target() << std::endl;
            }
        }
    }

    Polygon_set m_polygonSet;

private:
    Traits_2 m_traits;
    std::vector<float> m_points;
    int m_num_beziers;
    Traits_2::Make_x_monotone_2 m_make_x_monotone;
    std::list<X_monotone_curve_2> m_subcurvesList;
    Polygon_2 m_polygon;

    void makeBezierCurve(int index)
    {
        std::list<Point_2> points;
        int offset = index * 6;
        int n = m_points.size();
        points.push_back(Point_2(m_points[offset + 0], m_points[offset + 1]));
        points.push_back(Point_2(m_points[offset + 2], m_points[offset + 3]));
        points.push_back(Point_2(m_points[offset + 4], m_points[offset + 5]));
        points.push_back(Point_2(m_points[(offset + 6) % n], m_points[(offset + 7) % n]));
        Bezier_curve_2 curve(points.begin(), points.end());

        splitIntoSubcurvesAndAddToPolygon(curve);
    }

    void splitIntoSubcurvesAndAddToPolygon(Bezier_curve_2& curve)
    {
        X_monotone_curve_2 subcurve;
        std::list<CGAL::Object> smallSubcurvesList;
        m_make_x_monotone(curve, std::back_inserter(smallSubcurvesList));
        for (auto candidate : smallSubcurvesList) {
            if (CGAL::assign(subcurve, candidate)) {
                m_polygon.push_back(subcurve);
            }
        }
    }

    void fixPolygonOrientation()
    {
        CGAL::Orientation orientation = m_polygon.orientation();
        if (orientation == CGAL::CLOCKWISE) {
            m_polygon.reverse_orientation();
        }
    }
};

int main()
{
    std::vector<float> points_1 = { 0, 0, 1, 3, 2, 1 };
    BezierPath path_1(points_1);

    std::vector<float> points_2 = { 1, 1, 2, 2, 3, 2 };
    BezierPath path_2(points_2);

    path_1.intersect(path_2);
    path_1.printInfo();

    return 0;
}

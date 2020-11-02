Venn 7
======

This project consists of:

- a tool for generating attractively rendered symmetric 7-Venn diagrams
- a web app where said symmetric 7-Venn diagrams are identified with 7-note scales and used as an interface for playing chords.

Venn diagrams
-------------

The problem of constructing rotationally symmetric Venn diagrams with more than three sets is an active area of research in the field of combinatorics. A theorem of Henderson states that n-fold rotational symmetric Venn diagrams can only exist when n is prime. A 5-Venn diagram rendered using five congruent ellipses has been known for a while.

Symmetric 7-Venn diagrams were a mystery for some years, but eventually one was found by Grunbaum (and is the subject of some viral Internet posts). As more were discovered, some constraints on the search were defined:

- **Simple:** no intersections of three curves.
- **Monotonicity:** the Venn diagram can theoretically be rendered with convex curves (even if it isn't in practice).
- **Polar symmetry:** the Venn diagram is unchanged when turned inside out.

There are exactly 23 symmetric 7-Venn diagrams that are both simple and monotone, and of those 23, exactly six are polar symmetric. These six "golden 7-Venn diagrams" are named after their place of discovery: Adelaide, Hamilton, Manawatu, Massey, Palmerston North, and Victoria.

Pandiatonicism
--------------

My friend Nathan Turczan originally inspired this project by pointing out that the curves of a 7-fold Venn diagram can be associated with the seven tones of a diatonic scale. The regions of the Venn diagram each represent a pitch class set within the musical theory of pandiatonicism. It could therefore be used as an interface for selecting and visualizing pandiatonic pitch class sets. Although its practicality is certainly up for debate, we thought it would make an interesting art piece.

The sounds used are Shepard tones, so that the octavation of the chord is ambiguous. If non-Shepard tones were used, two tones that are adjacent in the scale would have to be separated by a leap of a seventh, tarnishing some of the symmetry.

Implementation details
----------------------

The Bezier curve data is generated offline using a Python + NumPy + SymPy + Shapely. A small C++ application using CGAL computes the Boolean operations on Bezier curves. The resulting data is wrapped up into a single JSON file and loaded into the web app.

All Venn diagrams are created parametrically/algorithmically with no use of a GUI, so their parameters can be adjusted. The app works in the following stages:

- Entry of Venn diagrams with a matrix encoding.
- Combinatorial validation of diagram.
- Conversion to cubic Bezier curves. (Partially implemented.)
- Geometric validation of diagram.
- Boolean operations on Bezier curves using CGAL. (Not yet implemented.)
- JSON export for use in JavaScript web app.

Since the data generation is decoupled from the app, I would love to see what other things you can do with it. Some fun ideas:

- virtual MIDI keyboard as a VST plugin
- physical instrument with buttons
- posters
- string or wire art (all Venn diagrams are representable as woven strings)
- dartboard
- Twister mat
- 7-day weekly planner
- corn maze
- eccentric billionaire mansion floor plan

### Entry of Venn diagrams

The curves of a monotone *n*-Venn diagram can be characterized as *n* parallel, horizontal strands that can cross over with adjacent strands. Copied from [Ruskey and Weston](https://www.combinatorics.org/files/Surveys/ds5/nonsymm7.html), here is an ASCII version of the "strand encoding" for Adelaide:

```
-----   ---------------------------------
      X                                 
-   -   -   -------------   -------------
  X       X               X             
-   -   -   -   -----   -   -   -----   -
      X       X       X       X       X 
-   -   -   -   -   -   -   -   -   -   -
  X       X       X       X       X     
-   -----   -   -   -   -   -----   -   -
              X       X               X 
-------------   -   -   -------------   -
                  X                     
-----------------   ---------------------
```

Adelaide, like all the diagrams we work with in this project, is 7-fold rotational symmetric, so we display here only 1/7th of the full diagram. For the full figure, imagine seven of these chained together, and then bent into a circular loop. Noting that the crossing points fall into a grid with six rows and ten columns, we can horizontally read off each space between the seven strands, writing 1 at every crossing point and a 0 otherwise:

```
0100000000
1010001000
0101010101
1010101010
0001010010
0000100000
```

We could call this a "compact matrix encoding." This is a generalization of the "matrix encoding" described in a paper by Cao et al. The distinction is that we allow multiple 1's in each column, whereas the matrix encoding places each 1 in its own column, producing a much more horizontally spaced-out figure. The matrix vs. compact matrix encodings are topologically identical, but the compact matrix encoding lends itself better to conversion to an attractive geometrical figure, so we prefer it for this application.

Noting that the odd-numbered entries in odd-numbered rows and even-numbered entries in even-numbered rows are all 0's (i.e. the 1's fall in a checkerboard), every other entry can be removed from each row to form a "very compact matrix encoding:"

```
10000
11010
11111
11111
01101
00100
```

This is an encoding employed from the above-linked Ruskey and Weston page, and the format used to enter Venn diagrams into the project.

### Combinatorial validation

Cao et al. found an algorithm that works from the (full) matrix encoding to ensure that it encodes a real Venn diagram. Their application was to ensure that the search for Venn diagrams was exhaustive, but we can also use it here as a test tool to check for mistakes.

### Determination of cubic Bezier curves

Next, the combinatorial design is converted into a geometrical object. We pick any curve (they're all congruent anyway) and follow its strand around the diagram. For every crossover point, we map its position on the grid to polar coordinates in the 2D plane, using manually tweaked parameters to choose the spacing between the seven concentric rings and the radius of the innermost one. The problem is to find a smooth curve that passes through all these points.

For this, we turn to a spline algorithm developed by Knuth and Hobby originally for the METAFONT system. This algorithm automatically selects control points for Bezier curves that connect the points, producing an attractive and smooth shape that can be exported to an SVG path for use in the web app.

Here we have some artistic license to arbitrarily add new points and change constraints of the splines to produce pretty curves.

### Geometric validation

In the process of spline interpolation, it is technically possible for the curves introduced by interpolation to disrupt the topology of the Venn diagram. To make sure this doesn't happen, we add an extra validation layer where the curves are converted to reasonably hi-res polygons. The Shapely library is used to compute Boolean operations on these polygons to ensure that they produce a valid diagram, i.e. all 127 regions are nonempty and each one is a connected shape.

### Boolean operations on Bezier curves using CGAL

We need to produce path data for the 127 regions of the Venn diagram by performing Boolean operations on the Bezier curves. I couldn't find any well-supported Python library that does this. I also tried Paper.js's built-in Boolean operations on SVG-type paths, but ran into bugs. Alternatives seem sparse, and it looked difficult to roll my own.

I was pointed to CGAL, an enormous C++ library of computational geometry algorithms, which contains a robust and well-developed library for Boolean operations on curves (Bezier and otherwise). My review of CGAL: it's an excellent work of software, but intimidating to use due to its degree of mathematical rigor.

Before it can do any Booleans, CGAL requires us to first split each Bezier curve into one or more "weakly x-monotone curves," defined as a curve that either passes the vertical line test or is itself a vertical line segment. For example, a Bezier curve that doubles back on itself horizontally would need to be split into two or more such subcurves. CGAL provides a `Make_x_monotone_2` object that does this, but you have to invoke it yourself.

I prefer to stick with Python for scientific computing, so I keep the C++ application minimal and talk to it via JSON.

CGAL knows immediately if a curve is empty or disconnected, so we can also use CGAL to verify once more that the Venn diagram is valid. Certainly doesn't hurt.

### Normalizing clipped Bezier curves

An important subtlety of CGAL that took me a while to grasp: when computing Booleans on Bezier curves, CGAL does not actually produce new control points. Instead, it retains the old Bezier curve and defines "source" and "target" points to which the curve is truncated. Maybe I missed it, but I couldn't find built-in CGAL functionality to convert a clipped Bezier curve into a standard Bezier curve that would be readable by an SVG path.

Suppose we have a clipped Bezier curve whose "supporting curve" (i.e. the original prior to clipping) is given by control points `P0, P1, P2, P3`, which is clipped to the points `S,T`. Let `f(t, P0, P1, P2, P3)` denote the function of a cubic Bezier curve evaluated at time `0 <= t <= 1`, which is a cubic polynomial in `t`. We wish to find the new control points `P0', P1', P2', P3'` of the clipped Bezier curve.

The first step is to find `0 <= t_S <= 1` and `0 <= t_T <= 1` such that

    f(t_S, P0, P1, P2, P3) = S
    f(t_T, P0, P1, P2, P3) = T

Due to the condition that the Bezier curves generated by CGAL are weakly x-monotone, the x-coordinate half of each equation is a cubic with a single root in the interval `[0, 1]`. (The y-coordinates aren't important since the equations are overdetermined anyway. `S` and `T` may not be right on the curves due to precision issues.) Cubic equations can be solved with any popular scientific computing package.

Knowing `t_T` and `t_S` gives us the equality:

    f(t, P0', P1', P2', P3') = f(t_S + (t_T - t_S) * t, P0, P1, P2, P3)

If we consider the x-coordinates only, this is the statement that two cubic polynomials in `t` are equal, so their four coefficients must be equal. This lets us set up a system of four linear equations relating the x-coordinates of `Pi` to the x-coordinates of `Pi'`. The same is true of the y-coordinates. Solving two 4x4 linear systems then allows us to compute the new control points. This completes the algorithm for clipping a Bezier curve.

### Web app

I went with SVG.js rather than canvas (e.g. p5.js or Paper.js) due to an educated guess on performance implications that I have yet to verify. SVG natively supports mouse events on Bezier paths. In canvas, libraries have to provide their own functionality to determine whether the mouse is inside or outside a path. Plus, I can easily export the figures as SVG.

The app is plain old vanilla JavaScript runnable in a local filesystem, and the sole dependencies are SVG.js and Tone.js (both of which I have vendored).

References
----------

- Cao, Tao et al. "Symmetric Monotone Venn Diagrams with Seven Curves."
- Grunbaum, Branko. "The search for symmetric Venn diagrams."
- Ruskey, Frank and Weston, Mark. "A Survey of Venn Diagrams." https://www.combinatorics.org/files/Surveys/ds5/VennSymmExamples.html
- Hobby, John D. "Smooth, Easy to Compute Interpolating Splines."

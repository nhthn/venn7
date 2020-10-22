Venn 7
======

This project consists of:

- a tool for generating attractively rendered symmetric 7-Venn diagrams
- a web app where said symmetric 7-Venn diagrams are identified with 7-note scales and used as an interface for playing chords.

Venn diagrams
-------------

The problem of constructing rotationally symmetric Venn diagrams with more than three sets is an active area of research in the field of combinatorics. A theorem of Henderson states that n-fold rotational symmetric Venn diagrams can only exist when n is prime. A 5-Venn diagram rendered using five congruent ellipses has been known for a while.

No symmetric 7-Venn diagrams were known for a while, but eventually one was found by Grunbaum (and is the subject of some viral Internet posts). As more were discovered, some constraints on the search were defined:

- **Simple:** no intersections of three curves.
- **Monotonicity:** the Venn diagram can theoretically be rendered with convex curves (even if it isn't in practice).
- **Polar symmetry:** the Venn diagram is unchanged when turned inside out.

There are exactly 23 symmetric 7-Venn diagrams that are both simple and monotone, and of those 23, exactly six are polar symmetric. These six "golden 7-Venn diagrams" are named after their place of discovery: Adelaide, Hamilton, Manawatu, Massey, Palmerston North, and Victoria.

Pandiatonicism
--------------

My friend Nathan Turczan pointed out that the curves of a 7-fold Venn diagram can be associated with the seven tones of a diatonic scale. The regions of the Venn diagram each represent a pitch class set within the musical theory of pandiatonicism. It could therefore be used as an interface for selecting and visualizing pandiatonic pitch class sets. Although its practicality is certainly up for debate, we agreed it'd make an interesting art piece.

The sounds used are Shepard tones, so that the octavation of the chord is ambiguous. If non-Shepard tones were used, two tones that are adjacent in the scale would have to be separated by a leap of a seventh, tarnishing some of the symmetry.

Implementation details
----------------------

Each Venn diagram is entered using Cao et al.'s "matrix encoding." The figure is unfurled into seven horizontal strands which can cross over with adjacent strands. The matrix encoding uses a matrix consisting mostly of 0's, placing 1's at every crossover location. Since the figure is 7-fold rotational symmetric, only 1/7th of the matrix needs to be represented. Once entered, we perform a verification that the matrix encodes a valid Venn diagram, using the algorithm described in Cao's paper.

Crossover locations are interpolated using a type of spline developed for the METAFONT system by Knuth and Hobby. Once the resulting shapes are achieved, we use the Shapely computational geometry library to do a final check that the Venn diagram has the correct topology.

References
----------

- Cao, Tao et al. "Symmetric Monotone Venn Diagrams with Seven Curves."
- Grunbaum, Branko. "The search for symmetric Venn diagrams."
- https://www.combinatorics.org/files/Surveys/ds5/VennSymmExamples.html
- Hobby, John D. "Smooth, Easy to Compute Interpolating Splines."

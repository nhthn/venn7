Venn 7
======

This project consists of:

- a tool for generating attractively rendered symmetric 7-Venn diagrams
- a web app where said symmetric 7-Venn diagrams are identified with 7-note scales and used as an interface for playing chords.

Running the app
---------------

This repository contains sound files checked in using git-lfs. To obtain them, you will need to [install git-lfs](git-lfs), and run `git lfs pull` after cloning this repo.

[git-lfs]: https://git-lfs.github.com/

Tone.js uses AJAX to retrieve the samples used for playback, so you will need to run a local web server. To do this, `cd` into the `app` folder and run `python3 -m http.server`, then point your browser to `http://localhost:8000/`.

Venn diagrams
-------------

You're certainly familiar with the well-known Venn diagrams with two and three sets. With four or more sets, the space of Venn diagrams is rich and full of surprising properties. For example, a valid 4-Venn diagram can't be constructed using circles (we have to resort to ellipses), and neither can a 4-Venn diagram possess four-fold rotational symmetry.

A theorem of Henderson states that a n-Venn diagram with n-fold rotational symmetry can only exist when n is prime. The search for symmetric n-Venn diagrams for n > 3 is an active research topic in the field of combinatorics.

There is only one symmetric 5-Venn diagram, which can be rendered with five ellipses. Symmetric 7-Venn diagrams were a mystery for some years, but eventually one was found by Grunbaum. As more were discovered, some constraints on the search were defined:

- **Simple:** no intersections of three or more curves.
- **Monotonicity:** the Venn diagram can theoretically be rendered with convex curves (even if it isn't in practice). This implies that the different regions are sorted into concentric layers by the number of curves that they are part of.
- **Polar symmetry:** the Venn diagram is topologically unchanged when turned inside out.

There are exactly six "golden 7-Venn diagrams" satisfying all three: Adelaide, Hamilton, Manawatu, Massey, Palmerston North, and Victoria. If we relax the polar symmetry condition, there are an additional 16 "silver 7-Venn diagrams," for a total of 23 simple monotone symmetric 7-Venn diagrams.

The 11-Venn case is even richer than the 7-Venn case. A few non-simple diagrams were found in the 2000's, but Mamakani and Ruskey made a breakthrough in 2012, discovering over 200,000 simple symmetric monotone 11-Venn diagrams as well as 13-Venn cases. As beautiful as these diagrams are, I don't see an obvious way to make them into a user interface, as there are thousands of extremely small regions.

Pandiatonicism
--------------

Pandiatonicism is a broad variety of musical practices that use the diatonic scale in ways "beyond" tonal harmony. A common pandiatonic technique is to treat the seven tones as roughly uniform,just as dodecaphony views the 12-tone chromatic scale. This idea is realized in pitch class set theory mod 7 (Santa, 2000), which adapts classical 12-tone set theory to pandiatonic music by thinking of diatonic chords as subsets of the scale.

My friend Nathan Turczan originally inspired this project by pointing out that the curves of a 7-fold Venn diagram can be mapped to a diatonic scale, making the Venn diagram into a playable visualization of set theory mod 7. I loved the idea, and it stuck with me for a good two years until I finally caved and built it. Just as we anticipated, the resulting interface is as awkward and strange as it is fascinating.

I noticed early on that, when playing standard synthesizer tones on the diagram, there is a discontinuity as the scale wraps back to the octave. For example, there are seven regions on a diagram representing diatonic seconds, but one of those has to be a seventh, breaking the symmetry. To address this, I decided to use Shepard tones, an auditory illusion where a note has ambiguous octavation. This closes the seam formed by the octave and makes the tones reflect the symmetry of the diagram.

Implementation details
----------------------

The Bezier curve data is generated offline using Python + NumPy, and a bit of SymPy and Shapely. Paper.js's functions are used to compute Boolean operations on Bezier curves. The resulting data is wrapped up into a single JSON file and loaded into the web app. The sound design is rendered from synthesizer patches made in SuperCollider.

All Venn diagrams are created parametrically and algorithmically with no use of a GUI, so their parameters can be adjusted. In the following sections, I'll cover technical details and challenges of each component: 

- Entry of Venn diagrams with a matrix encoding.
- Combinatorial validation of diagram.
- Conversion to cubic Bezier curves using METAFONT splines.
- Geometric validation of diagram.
- Boolean operations on Bezier curves using Paper.js.
- Sound design of Shepard tones.
- JSON export for use in JavaScript web app.

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

Noting that the odd-numbered entries in odd-numbered rows and even-numbered entries in even-numbered rows are all 0's (i.e. the 1's fall in a checkerboard), every other entry can be removed from each row:

```
10000
11010
11111
11111
01101
00100
```

I call this the "mini-matrix encoding." It is employed from the above-linked Ruskey and Weston page, and the format used to enter Venn diagrams into the project. Readding the zeros expands them to compact matrix encodings.

### Combinatorial validation

Cao et al. found an algorithm that works from the (full) matrix encoding to ensure that it encodes a real Venn diagram. Their application was to ensure that the search for Venn diagrams was exhaustive, but we can also use it here as a test tool to check for mistakes. With minor modifications, this algorithm applies just as well to compact matrix encodings.

A few quick validation steps need to get out of the way first: no two horizontally or vertically adjacent `1`'s are allowed, and 1-indexed row `i` should have exactly `binomial(n, k) / n` ones. From here we construct the *p-matrix*, which is a matrix indicating the position of each numbered strand at each column. For example, the first column of the p-matrix is [0, 1, 2, 3, 4, 5, 6]. The first column of Adelaide's compact matrix encoding tells us to swap the 2nd/3rd strands and the 4th/5th strands, so the next column is [0, 2, 1, 4, 3, 5, 6]. Repeat for the entire diagram.

A key observation in the Cao et al. algorithm is that, reading left to right, every crossing starts a region, and every region is started by exactly one crossing. In other words, a crossing is a junction of four regions, and the crossing's associated region is immediately to its right. The relationship between crossings and regions is almost one-to-one -- only the outermost (empty set) and innermost ({0, 1, 2, 3, 4, 5, 6}) regions have no associated crossing.

Given a crossing, the p-matrix can be used to identify the sets in the associated region. After swapping entries `k` and `k + 1` (0-indexed) in column `c` of the p-matrix, the strip `c[:k + 1]` in Python slice notation names the precise set of curves that the region belongs to. For example, if we just swapped the 2nd/3rd entries and 4th/5th entries to get p-matrix column [0, 2, 1, 4, 3, 5, 6], the upper crossing starts region {0, 2} and the lower one {0, 2, 1, 4}. If the matrix encoding produces a valid Venn diagram, then 126 subsets will each be represented exactly once by a crossing. The remaining two are the innermost and outermost regions, bringing the total to 2^7 = 128.

### Determination of cubic Bezier curves

Next, the combinatorial design is converted into a geometrical object. We pick any curve (they're all congruent anyway) and follow its strand around the diagram. For every crossover point, we map its position on the grid to polar coordinates in the 2D plane, using manually tweaked parameters to choose the spacing between the seven concentric rings and the radius of the innermost one. The problem is to find a smooth curve that passes through all these points.

For this, we turn to a spline algorithm developed by Knuth and Hobby originally for the METAFONT system. This algorithm automatically selects control points for Bezier curves that connect the points, producing an attractive and smooth shape that can be exported to an SVG path for use in the web app.

Here we have some artistic license to arbitrarily add new points and change constraints of the splines to produce pretty curves.

### Boolean operations on Bezier curves

We need to produce path data for the 127 regions of the Venn diagram by performing Boolean operations on the Bezier curves. I couldn't find any well-supported Python library that does this. I experimented with CGAL, but ran into mysterious "precondition errors" that I couldn't resolve.

Paper.js's built-in Boolean operations seemed to work OK, although sometimes they produce artifacts. I invoke Paper.js using Node as a subprocess. In this case, I'm purely running Paper.js offline, not using it in the Web app.

### Sound design of Shepard tones

I used SuperCollider, an audio synthesis language, to make some Shepard tone patches for the app. Each Venn diagram is associated with a different patch and color scheme, only for the reason of making the app less bland. These choices are artistic and not reflective of any mathematical properties of the diagrams.

Each patch is a single-octave SynthDef which is instantiated in nine different octaves on the language side. Each octave is multiplied by a gain factor `exp(-((p - c) / (12 * s))^2)`, where `p` is the synth's pitch, `c` is a fixed "center" pitch, and `s` is a spread factor that controls the width of the bell curve. `s` has to be tuned to ensure the Shepard tone illusion works and creates a seamless scale.

Due to the octaves, Shepard tones seem to require a really huge, orchestral-sounding patches.

Some comments on individual patches:

- Pads: standard detuned subtractive synths with super long reverb.
- Bells: modal/additive synthesis using a stiff string physical model. See my blog post on modal synthesis for info in this.

### Web app

The app is plain old vanilla JavaScript runnable in a local filesystem, and the sole dependencies are SVG.js and Tone.js (both of which I have vendored).

Conclusions
-----------

Thanks for checking out this project! I loved working on it since it combines a few of my favorite topics: sound design, music theory, research mathematics, and musical interface design.

Since the data generation is decoupled from the app, I would love to see what other things you can do with it. Some fun ideas:

- virtual MIDI keyboard as a VST plugin
- posters
- string or wire art (all Venn diagrams are representable as woven strings)
- physical instrument with buttons
- dartboard
- Twister mat
- 7-day weekly planner
- eccentric billionaire mansion floor plan

Acknowledgements
----------------

Thanks to Nathan Turczan for first coming up with this idea, and Luke Nihlen for early feedback. Dedicated in memory of Eddie Gale.

References
----------

- Cao, Tao et al. "Symmetric Monotone Venn Diagrams with Seven Curves."
- Grunbaum, Branko. "The search for symmetric Venn diagrams."
- Ruskey, Frank and Weston, Mark. "A Survey of Venn Diagrams." https://www.combinatorics.org/files/Surveys/ds5/VennSymmExamples.html
- Hobby, John D. "Smooth, Easy to Compute Interpolating Splines."
- Santa, Matthew. "Analysing Post-Tonal Diatonic Music: A Modulo 7 Perspective." https://www.jstor.org/stable/854427?seq=1
- Ahmadi Mamakani, Abdolkhalegh. "Searching for Simple Symmetric Venn Diagrams." https://dspace.library.uvic.ca:8443/handle/1828/4709

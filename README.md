Venn 7
======

**Try it out here: https://nathan.ho.name/venn7/**

This project consists of:

- a tool for generating attractively rendered symmetric 7-Venn diagrams
- a web app where said symmetric 7-Venn diagrams are identified with 7-note scales and used as an interface for playing chords.

Information on what symmetric 7-Venn diagrams are can be found in the app itself.

Running the web app
-------------------

This repository contains sound files checked in using git-lfs. To obtain them, you will need to [install git-lfs](git-lfs), and run `git lfs pull` after cloning this repo.

[git-lfs]: https://git-lfs.github.com/

Tone.js uses AJAX to retrieve the samples used for playback, so you will need to run a local web server. To do this, `cd` into the `app` folder and run `python3 -m http.server`, then point your browser to `http://localhost:8000/`.

### Development

Sorry, the Python side of this repo is a bit of a mess. To set up:

- Start a virtualenv and run `pip install -e .`.
- `cd` into `src/venn7` and run `npm install`.
- `pip install pytest` and `pytest`.

To recompile Venn diagram shape data, run `python src/venn7/venn.py app/venn_diagrams.js`.

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
0001010001
0000100000
```

We could call this a "compact matrix encoding." This is a generalization of the "matrix encoding" described in a paper by Cao et al. The distinction is that we allow multiple 1's in each column, whereas the matrix encoding places each 1 in its own column, producing a much more horizontally spaced-out figure. The matrix vs. compact matrix encodings are topologically identical, but the compact matrix encoding lends itself better to conversion to an attractive geometrical figure, so we prefer it for this application.

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

- Victoria = bells: modal/additive synthesis using a stiff string physical model. See my blog post on modal synthesis for info in this.
- Adelaide = pad: detuned subtractive synths with super long reverb.
- Massey = weird vocal formant synth: subtractive synth with multiple vocal-like resonances.
- Manawatu = reed organ: pulse waves with small pulse width and some noise in the upper register.
- Palmerston North = granular: FM grains triggered by random impulses.
- Hamilton = electric piano: FM synthesis.
- Symmetric 5-Venn diagram = weird synthesizer: resonant subtractive synth with randomized envelope for every voice.

### Web app

The app is plain old vanilla JavaScript, almost runnable in a local filesystem save for Tone.js sample loading. The sole dependencies are SVG.js and Tone.js (both of which I have vendored).

References
----------

- Cao, Tao et al. "Symmetric Monotone Venn Diagrams with Seven Curves."
- Ruskey, Frank and Weston, Mark. "A Survey of Venn Diagrams." https://www.combinatorics.org/files/Surveys/ds5/VennSymmExamples.html
- Hobby, John D. "Smooth, Easy to Compute Interpolating Splines."

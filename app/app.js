function interpolateColors(color1, color2, steps, longHue) {
    const result = [];

    let hueDifference = color2[0] - color1[0];
    if (hueDifference > 180) {
        hueDifference = hueDifference - 360;
    } else if (hueDifference < -180) {
        hueDifference = hueDifference + 360;
    }
    if (longHue) {
        hueDifference = 360 + hueDifference;
    }

    let i;
    for (i = 0; i < steps; i++) {
        const k = i / (steps - 1);
        const intermediateColor = [
            (color1[0] + k * hueDifference) % 360,
            color1[1] * (1 - k) + color2[1] * k,
            color1[2] * (1 - k) + color2[2] * k
        ];
        result.push(hsluv.hsluvToHex(intermediateColor));
    }
    return result;
}

function makeColorScheme(spec) {
    const scheme = {};
    scheme.background = hsluv.hsluvToHex(spec.background);
    scheme.foreground = hsluv.hsluvToHex(spec.foreground);
    scheme.center = hsluv.hsluvToHex(spec.center);
    scheme.regionColors = interpolateColors(spec.background, spec.center, spec.order + 1, !!spec.longHue);
    scheme.sound = spec.sound;
    return scheme;
}

const COLOR_SCHEMES = {
    // pink/indigo
    victoria: makeColorScheme({
        background: [340, 30, 90],
        center: [270, 30, 30],
        foreground: [190, 10, 10],
        sound: "bell",
        order: 7
    }),
    // red/dusty pink
    adelaide: makeColorScheme({
        background: [-50, 10, 10],
        center: [0, 30, 70],
        foreground: [190, 30, 95],
        sound: "pad",
        order: 7
    }),
    // yellow/beige
    massey: makeColorScheme({
        background: [70, 30, 90],
        center: [0, 10, 30],
        foreground: [50, 10, 10],
        sound: "weird",
        order: 7
    }),
    // almost black and white, faintly green/yellow
    manawatu: makeColorScheme({
        background: [115, 30, 10],
        center: [90, 10, 80],
        foreground: [190, 30, 95],
        sound: "reed",
        order: 7
    }),
    // blue
    palmerston_north: makeColorScheme({
        background: [210, 20, 90],
        center: [280, 20, 30],
        foreground: [190, 20, 40],
        sound: "droplet",
        order: 7
    }),
    // orange/red/purple
    hamilton: makeColorScheme({
        background: [0, 30, 10],
        center: [30, 90, 70],
        foreground: [10, 20, 95],
        sound: "piano",
        order: 7
    }),
    // orange/red/purple
    "5": makeColorScheme({
        background: [145, 30, 95],
        center: [30, 30, 30],
        foreground: [10, 20, 10],
        longHue: true,
        sound: "bell2",
        order: 5
    })
};
COLOR_SCHEMES.default = COLOR_SCHEMES.victoria;

class VennDiagramApp {
    constructor(vennDiagrams) {
        const that = this;
        document.querySelector("#next-diagram")
            .addEventListener("click", () => {
                that.loadNextDiagram();
            });
        document.querySelector("#previous-diagram")
            .addEventListener("click", () => {
                that.loadPreviousDiagram();
            });

        this.vennDiagrams = vennDiagrams;
        this.numberOfDiagrams = this.vennDiagrams.diagrams_list.length;
        this.diagram = null;
        this.diagramIndex = 0;
        this.loadDiagram();

        window.addEventListener("keydown", (event) => {
            if (event.key === "ArrowLeft") {
                event.preventDefault();
                that.loadPreviousDiagram();
            } else if (event.key === "ArrowRight") {
                event.preventDefault();
                that.loadNextDiagram();
            }
        });
    }

    loadNextDiagram() {
        this.diagramIndex = (this.diagramIndex + 1) % this.numberOfDiagrams;
        this.loadDiagram();
    }

    loadPreviousDiagram() {
        this.diagramIndex = (
            this.diagramIndex - 1 + this.numberOfDiagrams
        ) % this.numberOfDiagrams;
        this.loadDiagram();
    }

    loadDiagram() {
        if (this.diagram !== null) {
            this.diagram.cleanup();
        }
        const name = this.vennDiagrams.diagrams_list[this.diagramIndex];
        const diagram = this.vennDiagrams[name];
        document.querySelector("#diagram-name").innerText = diagram.name;
        const colorScheme = COLOR_SCHEMES[name] || COLOR_SCHEMES.default;
        this.applyColorScheme(colorScheme);
        this.diagram = new VennDiagram(diagram, colorScheme);
    }

    applyColorScheme(colorScheme) {
        document.querySelector("body")
            .style.backgroundColor = colorScheme.background;
        for (let selector of ["#diagram-name", "#previous-diagram", "#next-diagram"]) {
            document.querySelector(selector)
                .style.color = colorScheme.foreground;
        }
    }
}


function get_venn_sets(region_index, n) {
    let tmp = region_index;
    const result = [];
    let i;
    for (i = 0; i < n; i++) {
        result.push(tmp % 2);
        tmp = Math.floor(tmp / 2);
    }
    return result;
}


class VennDiagram {
    constructor(venn_diagram, colorScheme) {
        this.venn_diagram = venn_diagram;
        this.n = venn_diagram.n;
        this.colorScheme = colorScheme;

        const canvas_size = 800;
        this.canvas_size = canvas_size;
        const draw = SVG().addTo("#canvas-container").size(canvas_size, canvas_size);
        this.draw = draw;
        const scale = 350 / 50;
        this.scale = scale;

        this.player = new VennPlayer(this.n, `sounds/${colorScheme.sound}`);

        function updateSize() {
            const size = Math.min(
                window.innerWidth,
                window.innerHeight - document.getElementById("header").clientHeight
            );
            draw.node.setAttribute("width", size);
            draw.node.setAttribute("height", size);
            draw.node.setAttribute("viewBox", `0 0 ${canvas_size} ${canvas_size}`);
        }
        updateSize();
        this.resizeListener = window.addEventListener("resize", function () {
            updateSize();
        });

        function make_venn_curve(i) {
            const path = draw.path(venn_diagram.curve)
                .attr({ "pointer-events": "none" })
                .fill({ color: "black", opacity: 0 })
                .stroke({ opacity: 0, color: colorScheme.center, width: 1.5 / scale })
                .rotate(360 / venn_diagram.n * i, 0, 0)
                .scale(scale, 0, 0)
                .translate(canvas_size / 2, canvas_size / 2);
            return path;
        }

        this.curves = [];
        let i;
        for (i = 0; i < venn_diagram.n; i++) {
            this.curves.push(make_venn_curve(i));
        }

        this.curves.forEach((curve) => {
            curve.front();
        });

        this.regions = [];
        this.region_outlines = [];
        for (i = 1; i < Math.pow(2, venn_diagram.n); i++) {
            this.renderRegion(i);
        }
    }

    makeRegionShape(regionIndex) {
        const path = this.draw.path(this.venn_diagram.regions[regionIndex])
            .stroke({ linejoin: "round", linecap: "round" })
            .scale(this.scale, 0, 0)
            .translate(this.canvas_size / 2, this.canvas_size / 2)
        return path;
    }

    renderRegion(regionIndex) {
        const sets = get_venn_sets(regionIndex, this.n);
        const order = get_venn_sets(regionIndex, this.n).reduce((a, b) => a + b);

        let region = this.makeRegionShape(regionIndex);
        region.fill({
            color: this.colorScheme.regionColors[order]
        });
        region.stroke({
            width: 0.1,
            color: this.colorScheme.regionColors[order]
        });
        this.regions.push(region);
        region.back();

        let region_outline = this.makeRegionShape(regionIndex);
        this.region_outlines.push(region_outline);
        region_outline
            .fill({ color: "black", opacity: 0 })
            .stroke({
                opacity: 0,
                color: this.colorScheme.foreground,
                width: 3 / this.scale
            });

        region_outline
            .mouseover(() => {
                region_outline.stroke({ opacity: 1 });
                let i;
                for (i = 0; i < this.n; i++) {
                    this.curves[i].stroke({ opacity: sets[i] * 0.9 });
                }
            })
            .mouseout(() => {
                region_outline.stroke({ opacity: 0 });
            })
            .mousedown(() => {
                this.clickRegion(regionIndex);
            });
    }

    clickRegion(regionIndex) {
        console.log("lick");
        const sets = get_venn_sets(regionIndex, this.n);
        this.player.playChord(sets);
    }

    cleanup() {
        this.draw.clear();
        const node = this.draw.node;
        node.parentElement.removeChild(node);

        this.player.cleanUp();

        window.removeEventListener("resize", this.resizeListener);
    }
}

class VennPlayer {
    constructor(n, directory) {
        this.directory = directory;
        this.n = n;

        this.scale = n === 5 ? [0, 3, 5, 7, 10] : [0, 2, 3, 5, 7, 8, 10];

        this.polyphony = 3;
        this.synths = [];
        for (let i = 0; i < this.n; i++) {
            let note = [];
            this.synths.push(note);
            for (let j = 0; j < this.polyphony; j++) {
                const synth = new Tone.Player(
                    `${directory}/note_${this.scale[i]}.mp3`
                ).toDestination();
                synth.fadeOut = 1;
                synth.volume.value = -10;
                note.push(synth);
            }
        }
    }

    stopAllSynths() {
        for (let note of this.synths) {
            for (let synth of note) {
                synth.stop();
            }
        }
    }

    playChord(chord) {
        this.stopAllSynths();
        for (let i = 0; i < this.n; i++) {
            if (chord[i]) {
                let synth = this.synths[i].pop();
                this.synths[i].unshift(synth);
                synth.start();
            }
        }
    }

    cleanUp() {
        for (let note of this.synths) {
            for (let synth of note) {
                synth.dispose();
            }
        }
    }
}

const app = new VennDiagramApp(venn_diagrams);

document.getElementById("help").addEventListener("click", () => {
    document.getElementById("explanation").style.display = "flex";
});
document.getElementById("explanation-background").addEventListener("click", () => {
    document.getElementById("explanation").style.display = "none";
});

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
        this.bufferLoader = new BufferLoader();

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
            this.diagram.cleanUp();
        }
        const name = this.vennDiagrams.diagrams_list[this.diagramIndex];
        const diagram = this.vennDiagrams[name];
        document.querySelector("#diagram-name").innerText = diagram.name;
        const colorScheme = COLOR_SCHEMES[name] || COLOR_SCHEMES.default;
        this.applyColorScheme(colorScheme);
        this.diagram = new VennDiagram(diagram, colorScheme, this.bufferLoader);
    }

    applyColorScheme(colorScheme) {
        document.querySelector("body")
            .style.backgroundColor = colorScheme.background;
        for (let selector of ["#header", "#loading-text"]) {
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
    constructor(venn_diagram, colorScheme, bufferLoader) {
        this.venn_diagram = venn_diagram;
        this.n = venn_diagram.n;
        this.colorScheme = colorScheme;
        this.bufferLoader = bufferLoader;

        this.canvasContainer = document.getElementById("container");

        this.loadStatus = {
            audio: false,
            graphics: false,
        };
        this.loadingText = document.getElementById("loading-text");
        this.onUpdateLoadStatus();

        const canvas_size = 800;
        this.canvas_size = canvas_size;

        this.draw = SVG().addTo("#canvas-container").size(canvas_size, canvas_size);
        this.draw.node.classList.add("hidden");
        this.scale = 350 / 50;

        this.player = new VennPlayer(
            this.n, `sounds/${colorScheme.sound}`, this.bufferLoader
        );
        this.player.load().then(() => {
            this.loadStatus.audio = true;
            this.onUpdateLoadStatus();
        });

        this.updateSize();
        this.resizeListener = window.addEventListener("resize", () => {
            this.updateSize();
        });

        this.midiCallbacks = {}; 
  
        this.triggerMidiNoteOn = (midiNote) => {
          if (this.midiCallbacks[midiNote] !== undefined) {
            this.midiCallbacks[midiNote].noteOn();
          }
        }
        
        this.triggerMidiNoteOff = (midiNote) => {
          if (this.midiCallbacks[midiNote] !== undefined) {
            this.midiCallbacks[midiNote].noteOff();
          }
        }

        setTimeout(() => {
            this.render();
            this.loadStatus.graphics = true;
            this.onUpdateLoadStatus();
            InitMidiListeners(this.triggerMidiNoteOn, this.triggerMidiNoteOff);
        }, 0);
    }

    onUpdateLoadStatus() {
        if (this.loadStatus.graphics) {
            this.draw.node.classList.remove("hidden");
        }
        if (this.loadStatus.audio && this.loadStatus.graphics) {
            this.loadingText.innerText = "";
        } else if (this.loadStatus.audio) {
            this.loadingText.innerText = "Loading graphics...";
        } else if (this.loadStatus.graphics) {
            this.loadingText.innerText = "Loading audio...";
        } else {
            this.loadingText.innerText = "Loading audio & graphics...";
        }
    }

    render() {
        this.curves = [];
        let i;
        for (i = 0; i < this.venn_diagram.n; i++) {
            this.curves.push(this.makeVennCurve(i));
        }

        this.curves.forEach((curve) => {
            curve.front();
        });

        this.regions = [];
        this.region_outlines = [];
        for (i = 1; i < Math.pow(2, this.venn_diagram.n); i++) {
            this.renderRegion(i);
        }
    }

    updateSize() {
        const size = Math.min(
            window.innerWidth,
            window.innerHeight - document.getElementById("header").clientHeight
        );
        this.draw.node.setAttribute("width", size);
        this.draw.node.setAttribute("height", size);
        this.draw.node.setAttribute("viewBox", `0 0 ${this.canvas_size} ${this.canvas_size}`);
    }

    makeVennCurve(i) {
        return this.draw.path(this.venn_diagram.curve)
            .attr({ "pointer-events": "none" })
            .fill({ color: "black", opacity: 0 })
            .stroke({ opacity: 0, color: this.colorScheme.center, width: 1.5 / this.scale })
            .rotate(360 / this.venn_diagram.n * i, 0, 0)
            .scale(this.scale, 0, 0)
            .translate(this.canvas_size / 2, this.canvas_size / 2);
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

        const noteOnAnimation = () => {
            region_outline.stroke({ opacity: 1 });
            let i;
            for (i = 0; i < this.n; i++) {
                this.curves[i].stroke({ opacity: sets[i] * 0.9 });
            }
        } 

        const noteOffAnimation = () => {
            region_outline.stroke({ opacity: 0 });
            let i;
            for (i = 0; i < this.n; i++) {
                this.curves[i].stroke({ opacity: 0 });
            }
        }
        
        this.midiCallbacks[regionIndex] = {
            'noteOn': () => {
                noteOnAnimation();
                this.clickRegion(regionIndex);
            },
            'noteOff': () => {
                noteOffAnimation();
            }
        };

        region_outline
            .mouseover(noteOnAnimation)
            .mouseout(() => {
                region_outline.stroke({ opacity: 0 });
            })
            .mousedown(() => {
                this.clickRegion(regionIndex);
            });
    }

    clickRegion(regionIndex) {
        const sets = get_venn_sets(regionIndex, this.n);
        this.player.playChord(sets);
    }

    cleanUp() {
        this.draw.clear();
        const node = this.draw.node;
        node.parentElement.removeChild(node);

        this.player.cleanUp();

        window.removeEventListener("resize", this.resizeListener);
    }
}

class BufferLoader {
    constructor() {
        this.buffers = {};
    }

    async loadAudioBuffers(audioContext, files) {
        for (let file of files) {
            if (this.buffers[file]) {
                continue;
            }
            const audioBuffer = await new Tone.Buffer().load(file);
            this.buffers[file] = audioBuffer;
        }
    }
}

class VennPlayer {
    constructor(n, directory, bufferLoader) {
        this.directory = directory;
        this.n = n;
        this.bufferLoader = bufferLoader;

        this.scale = n === 5 ? [0, 3, 5, 7, 10] : [0, 2, 3, 5, 7, 8, 10];

        this.files = [];
        for (let i = 0; i < this.n; i++) {
            this.files.push(`${directory}/note_${this.scale[i]}.mp3`);
        }

        this.polyphony = 3;
        this.synths = [];

        this.state = "not loading";
    }

    async load() {
        this.state = "loading";
        const buffers = await this.bufferLoader.loadAudioBuffers(Tone.context, this.files);
        for (let i = 0; i < this.n; i++) {
            let note = [];
            this.synths.push(note);
            for (let j = 0; j < this.polyphony; j++) {
                const synth = new Tone.Player(
                    this.bufferLoader.buffers[this.files[i]]
                ).toDestination();
                synth.fadeOut = 1;
                synth.volume.value = -10;
                note.push(synth);
            }
        }
        this.state = "ready";
    }

    stopAllSynths() {
        if (this.state !== "ready") {
            return;
        }
        for (let note of this.synths) {
            for (let synth of note) {
                synth.stop();
            }
        }
    }

    playChord(chord) {
        if (this.state !== "ready") {
            return;
        }
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
        if (this.state !== "ready") {
            return;
        }
        for (let note of this.synths) {
            for (let synth of note) {
                synth.dispose();
            }
        }
    }
}

const app = new VennDiagramApp(venn_diagrams);

document.getElementById("help").addEventListener("click", () => {
    document.getElementById("explanation").classList.remove("hidden");
});
document.getElementById("explanation-background").addEventListener("click", () => {
    document.getElementById("explanation").classList.add("hidden");
});

const COLOR_SCHEMES = {
    victoria: {
        center: "#034488",
        foreground: "#111111",
        background: "#e0f0ff"
    },
    adelaide: {
        center: "#ffffff",
        foreground: "#ffffff",
        background: "#440013"
    },
    massey: {
        center: "#fff0ef",
        foreground: "#888888",
        background: "#131313"
    },
    manawatu: {
        center: "#000000",
        foreground: "#000000",
        background: "#ffefff"
    },
    palmerston_north: {
        center: "#003300",
        foreground: "#000000",
        background: "#aaffaa"
    },
    hamilton: {
        center: "#330033",
        foreground: "#000000",
        background: "#ffeef8"
    },
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
        document.querySelector("#canvas-container")
            .style.backgroundColor = colorScheme.background;
        for (let selector of ["#diagram-name", "#previous-diagram", "#next-diagram"]) {
            document.querySelector(selector)
                .style.color = colorScheme.foreground;
        }
    }
}

class VennDiagram {
    constructor(venn_diagram, colorScheme) {
        const canvas_size = 800;
        const draw = SVG().addTo("#canvas-container").size(canvas_size, canvas_size);
        this.draw = draw;
        const scale = 5;

        function updateSize() {
            const size = Math.min(window.innerHeight, window.innerWidth);
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
                .fill({ color: colorScheme.center, opacity: 1 / 7 })
                .stroke({ opacity: 0, color: colorScheme.center, width: 1.5 / scale })
                .rotate(360 / 7 * i, 0, 0)
                .scale(scale, 0, 0)
                .translate(canvas_size / 2, canvas_size / 2);
            return path;
        }
        function make_region(i) {
            const path = draw.path(venn_diagram.regions[i])
                .fill({ opacity: 0 })
                .stroke({ opacity: 0, color: colorScheme.foreground, width: 3 / scale })
                .scale(scale, 0, 0)
                .translate(canvas_size / 2, canvas_size / 2)
            return path;
        }

        const curves = [];
        let i;
        for (i = 0; i < venn_diagram.n; i++) {
            curves.push(make_venn_curve(i));
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
        };

        this.synths = [];
        for (i = 0; i < venn_diagram.n; i++) {
            const synth = new Tone.Player(`sounds/note_${[0, 2, 3, 5, 7, 8, 10][i]}.mp3`).toDestination();
            synth.volume.value = -10;
            this.synths.push(synth);
        }

        const regions = [];
        for (i = 1; i < Math.pow(2, venn_diagram.n); i++) {
            const sets = get_venn_sets(i, venn_diagram.n);
            let region = make_region(i);
            regions.push(region);
            region
                .mouseover(() => {
                    region.stroke({ opacity: 1 });
                    let i;
                    for (i = 0; i < venn_diagram.n; i++) {
                        curves[i].stroke({ opacity: sets[i] * 0.9 });
                    }
                })
                .mouseout(() => {
                    region.stroke({ opacity: 0 });
                })
                .mousedown(() => {
                    let i;
                    for (i = 0; i < venn_diagram.n; i++) {
                        if (sets[i]) {
                            this.synths[i].start();
                        }
                    }
                });
        }
    }

    cleanup() {
        const node = this.draw.node;
        node.parentElement.removeChild(node);

        for (let synth of this.synths) {
            synth.dispose();
        }

        window.removeEventListener("resize", this.resizeListener);
    }
}

const app = new VennDiagramApp(venn_diagrams);

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
        this.diagram = new VennDiagram(diagram);
    }
}

class VennDiagram {
    constructor(venn_diagram) {
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
                .fill({ color: "#036", opacity: 1 / 7 })
                .stroke({ opacity: 0, color: "#036", width: 1.5 / scale })
                .rotate(360 / 7 * i, 0, 0)
                .scale(scale, 0, 0)
                .translate(canvas_size / 2, canvas_size / 2);
            return path;
        }
        function make_region(i) {
            const path = draw.path(venn_diagram.regions[i])
                .fill({ opacity: 0 })
                .stroke({ opacity: 0, color: "#000", width: 3 / scale })
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
            const synth = new Tone.Synth().toDestination();
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
                            this.synths[i].triggerAttackRelease(["C", "D", "Eb", "F", "G", "Ab", "Bb"][i] + "4", "8n");
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

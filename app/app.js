const venn_diagram = venn_diagrams[location.hash.substring(1) || "adelaide"];

const canvas_size = 800;
const canvas = document.createElement("canvas");
canvas.setAttribute("width", canvas_size);
canvas.setAttribute("height", canvas_size);
document.getElementById("canvas-container").appendChild(canvas);
paper.setup(canvas);

const scale = 5;

function make_venn_curve(i) {
    const path = new paper.Path(venn_diagram.curve);
    path.scale(scale, new paper.Point(0, 0));
    path.rotate(360 / 7 * i, new paper.Point(0, 0));
    path.translate(new paper.Point(canvas_size / 2, canvas_size / 2));
    return path;
}
function make_region(i) {
    const path = new paper.Path(venn_diagram.regions[i]);
    path.scale(scale, new paper.Point(0, 0));
    path.translate(new paper.Point(canvas_size / 2, canvas_size / 2));
    return path;
}


const curves = [];

let i;
for (i = 0; i < venn_diagram.n; i++) {
    let path = make_venn_curve(i);
    path.strokeColor = null; // new paper.Color(0, 51 / 255, 102 / 255);
    path.strokeWidth = 1.5;
    path.fillColor = new paper.Color(0, 51 / 255, 102 / 255, 1 / 7);
    curves.push(path);
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

const synths = [];
for (i = 0; i < venn_diagram.n; i++) {
    const synth = new Tone.Synth().toDestination();
    synth.volume.value = -10;
    synths.push(synth);
}

const regions = [];

for (i = 1; i < Math.pow(2, venn_diagram.n); i++) {
    const sets = get_venn_sets(i, venn_diagram.n);

    let region = make_region(i);
    regions.push(region);

    region.fillColor = new paper.Color(0, 0, 0, 1e-3);
    region.strokeColor = null;
    region.strokeWidth = 3;

    region.on("mouseenter", () => {
        region.strokeColor = new paper.Color(0, 0, 0);
        let i;
        for (i = 0; i < venn_diagram.n; i++) {
            curves[i].strokeColor = sets[i] ? new paper.Color(0, 51 / 255, 102 / 255) : null;
        }
    });
    region.on("mouseleave", () => {
        region.strokeColor = null;
    });
    region.on("mousedown", () => {
        let i;
        for (i = 0; i < venn_diagram.n; i++) {
            if (sets[i]) {
                synths[i].triggerAttackRelease(["C", "D", "Eb", "F", "G", "Ab", "Bb"][i] + "4", "8n");
            }
        }
    });
}

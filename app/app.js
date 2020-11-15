const venn_diagram = venn_diagrams[location.hash.substring(1) || "adelaide"];

const canvas_size = 800;

const canvas_container = document.getElementById("canvas-container");

const draw = SVG().addTo(canvas_container).size(canvas_size, canvas_size);
const scale = 5;

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
                    synths[i].triggerAttackRelease(["C", "D", "Eb", "F", "G", "Ab", "Bb"][i] + "4", "8n");
                }
            }
        });
}

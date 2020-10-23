const venn_diagram = venn_diagrams.victoria;

const canvas_size = 800;
const draw = SVG().addTo("body").size(canvas_size, canvas_size);
const curves = [];
const scale = 5;

let i;

for (i = 0; i < venn_diagram.n; i++) {
    const polygon = draw.polygon(venn_diagram.spline)
        .fill({ color: "#036", opacity: 1 / 7 })
        .stroke({ opacity: 0, color: "#036", width: 1.5 / scale })
        .scale(scale, 0, 0)
        .rotate(360 / 7 * i, 0, 0)
        .translate(canvas_size / 2, canvas_size / 2);
    curves.push(polygon);
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

for (i = 1; i < venn_diagram.regions.length; i++) {
    const sets = get_venn_sets(i, venn_diagram.n);
    const polygon = draw.polygon(venn_diagram.regions[i])
        .fill({ opacity: 0 })
        .stroke({ opacity: 0, color: "#000", width: 3 / scale })
        .scale(scale, 0, 0)
        .translate(canvas_size / 2, canvas_size / 2)
        .mouseover(() => {
            polygon.stroke({ opacity: 1 });
            let i;
            for (i = 0; i < venn_diagram.n; i++) {
                curves[i].stroke({ opacity: sets[i] * 0.9 });
            }
        })
        .mouseout(() => {
            polygon.stroke({ opacity: 0 });
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

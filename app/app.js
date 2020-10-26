const venn_diagram = venn_diagrams.adelaide;

const canvas_size = 800;
const canvas = document.createElement("canvas");
canvas.setAttribute("width", canvas_size);
canvas.setAttribute("height", canvas_size);
document.getElementById("canvas-container").appendChild(canvas);
paper.setup(canvas);

function get_curve_as_svg_path_string() {
    const path_array = [];
    path_array.push("M");
    path_array.push(venn_diagram.bezier_control_points[0][0][0]);
    path_array.push(venn_diagram.bezier_control_points[0][0][1]);
    for (let spline of venn_diagram.bezier_control_points) {
        path_array.push("C");
        path_array.push(spline[1][0]);
        path_array.push(spline[1][1]);
        path_array.push(spline[2][0]);
        path_array.push(spline[2][1]);
        path_array.push(spline[3][0]);
        path_array.push(spline[3][1]);
    }
    return path_array.join(",");
}

function make_venn_curve(i) {
    const path = new paper.Path(get_curve_as_svg_path_string());
    path.scale(scale, new paper.Point(0, 0));
    path.translate(new paper.Point(1, 0));
    path.rotate(360 / 7 * i, new paper.Point(0, 0));
    path.translate(new paper.Point(canvas_size / 2, canvas_size / 2));
    return path;
}

const curves = [];
const scale = 5;

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

for (i = 1; i < Math.pow(2, venn_diagram.n); i++) {
    const sets = get_venn_sets(i, venn_diagram.n);

    let polygon = null;
    let j;
    for (j = 0; j < venn_diagram.n; j++) {
        if (sets[j]) {
            let curve = make_venn_curve(j);
            if (polygon === null) {
                polygon = curve;
            } else {
                polygon = polygon.intersect(curve);
            }
        }
    }
    for (j = 0; j < venn_diagram.n; j++) {
        if (!sets[j]) {
            let curve = make_venn_curve(j);
            polygon = polygon.subtract(curve);
        }
    }
    polygon.fillColor = new paper.Color(0, 0, 0, 0.01);
    polygon.strokeColor = null;
    polygon.strokeWidth = 3;

    polygon.on("mouseenter", () => {
        polygon.strokeColor = new paper.Color(0, 0, 0);
        let i;
        for (i = 0; i < venn_diagram.n; i++) {
            curves[i].strokeColor = sets[i] ? new paper.Color(0, 51 / 255, 102 / 255) : null;
        }
    });
    polygon.on("mouseleave", () => {
        polygon.strokeColor = null;
    });
    polygon.on("mousedown", () => {
        let i;
        for (i = 0; i < venn_diagram.n; i++) {
            if (sets[i]) {
                synths[i].triggerAttackRelease(["C", "D", "Eb", "F", "G", "Ab", "Bb"][i] + "4", "8n");
            }
        }
    });

}

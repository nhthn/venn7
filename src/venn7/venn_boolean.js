const fs = require("fs");
const { JSDOM } = require("jsdom");
const paper = require("paper");

const dom = new JSDOM(`
    <!doctype html>
    <html>
        <body>
        </body>
    </html>
`);
paper.setup(dom.window.document.body);

const venn_diagram = JSON.parse(fs.readFileSync(0, "utf-8"));

function make_venn_curve(i) {
    const path = new paper.Path(venn_diagram.curve);
    path.rotate(360 / venn_diagram.n * i, new paper.Point(0, 0));
    return path;
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

const region_paths = [""];

for (i = 1; i < Math.pow(2, venn_diagram.n); i++) {
    const sets = get_venn_sets(i, venn_diagram.n);

    let region = null;
    let j;
    for (j = 0; j < venn_diagram.n; j++) {
        if (sets[j]) {
            let curve = make_venn_curve(j);
            if (region === null) {
                region = curve;
            } else {
                region = region.intersect(curve);
            }
        }
    }
    for (j = 0; j < venn_diagram.n; j++) {
        if (!sets[j]) {
            let curve = make_venn_curve(j);
            region = region.subtract(curve);
        }
    }

    region_paths.push(region.pathData);
}

console.log(JSON.stringify(region_paths));

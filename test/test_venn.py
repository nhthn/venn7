import pytest
import json
import venn7.venn


@pytest.mark.parametrize("diagram", list(venn7.venn.DIAGRAMS.values()))
def test_venn_diagrams(diagram):
    diagram.check_regions()
    json.dumps(diagram.export_json())

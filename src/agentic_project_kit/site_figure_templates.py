"""Deterministic rendering of reviewed SVG layouts from validated figure cells."""
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def render_template(figure: dict, *, compact: bool, root: Path) -> str:
    filename = figure['id'] + ('-mobile' if compact else '') + '.svg'
    tree = ET.parse(root / 'site/templates/figures' / filename)
    svg = tree.getroot()
    cells = dict(figure['cells'])
    cells['description'] = figure['boundary'] + ' ' + ' '.join(
        node['label'] + ': ' + node['detail'] for node in figure['nodes'])
    if compact and figure['id'] == 'G0':
        cells['provenance'] = cells['provenance'].split(' · local Git')[0]
        cells['nested'] += ' PR, CI wait,'
    slots = [e for e in svg.iter() if 'data-bind' in e.attrib]
    keys = [e.attrib['data-bind'] for e in slots]
    if len(keys) != len(set(keys)) or set(keys) != set(figure['template_slots']['mobile' if compact else 'desktop']):
        raise ValueError('figure template slots changed; review data bindings')
    for element in slots:
        key = element.attrib.pop('data-bind')
        if key not in cells:
            raise ValueError('missing figure cell: ' + key)
        element.text = str(cells[key])
    return ET.tostring(svg, encoding='unicode') + '\n'

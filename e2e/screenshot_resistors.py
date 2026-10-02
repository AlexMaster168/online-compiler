"""Add series resistor symbols to every discrete LED in screenshot diagrams."""
ADD_RESISTORS = r'''diagram => {
  const copy = JSON.parse(JSON.stringify(diagram));
  for (const led of [...copy.parts]) {
    const roles = led.type === 'led' ? ['A'] : led.type === 'rgb' ? ['R', 'G', 'B'] : [];
    roles.forEach((pin, i) => {
      if (copy.parts.some(r => r.series?.part === led.id && r.series.pin === pin)) return;
      copy.parts.push({id: `r-${led.id}-${pin}`, type: 'resistor',
        x: Math.max(0, led.x - 25), y: led.y + 105 + i * 65,
        pins: {}, props: {ohms: '220'}, series: {part: led.id, pin}});
    });
  }
  return copy;
}'''


def arduino_resistors(page):
    diagram = page.evaluate('ocCircuit.toJSON()')
    diagram = page.evaluate(ADD_RESISTORS, diagram)
    page.evaluate('d => ocCircuit.load(d)', diagram)
    assert page.evaluate("ocCircuit.toJSON().parts.filter(p => p.type === 'resistor').every(p => p.series)")


def esp32_resistors(page):
    diagram = page.evaluate("JSON.parse(OCProject.getFile('diagram.json'))")
    if not diagram:
        diagram = {'parts': [
            {'id': 'led2', 'type': 'led', 'x': 200, 'y': 120, 'pins': {'A': 'GPIO2'}, 'props': {'color': 'blue'}},
            {'id': 'servo18', 'type': 'servo', 'x': 290, 'y': 90, 'pins': {'SIG': 'GPIO18'}, 'props': {}},
        ]}
    diagram = page.evaluate(ADD_RESISTORS, diagram)
    page.evaluate("d => { OCProject.setFile('diagram.json', JSON.stringify(d)); OCEsp32Hardware.projectLoaded(); }", diagram)
    page.wait_for_selector('.cc-part[data-type="resistor"]')

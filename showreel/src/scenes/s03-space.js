// PLACEHOLDER — replaced by the scene build. Space — the corridor (3.75s–5.15625s)
R.scene({
  id: "s03-space",
  start: 3.75,
  end: 5.15625,
  z: 30,
  bg: R.pal.graphite,
  setup(root) {
    this.label = R.el('div', { text: "s03-space · Space — the corridor", style: { left: '120px', top: '470px', font: `800 72px ${R.font.display}`, color: R.pal.fog } }, root);
    this.bar = R.el('div', { style: { left: '120px', top: '590px', height: '6px', width: '0px', background: R.pal.fog } }, root);
  },
  update(lt, p) {
    this.bar.style.width = (p * 1680).toFixed(1) + 'px';
  },
});

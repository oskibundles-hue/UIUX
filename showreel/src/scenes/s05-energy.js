// PLACEHOLDER — replaced by the scene build. Energy — breath, drop, chaos into RANGE (7.03125s–9.375s)
R.scene({
  id: "s05-energy",
  start: 7.03125,
  end: 9.375,
  z: 50,
  bg: R.pal.graphite,
  setup(root) {
    this.label = R.el('div', { text: "s05-energy · Energy — breath, drop, chaos into RANGE", style: { left: '120px', top: '470px', font: `800 72px ${R.font.display}`, color: R.pal.fog } }, root);
    this.bar = R.el('div', { style: { left: '120px', top: '590px', height: '6px', width: '0px', background: R.pal.fog } }, root);
  },
  update(lt, p) {
    this.bar.style.width = (p * 1680).toFixed(1) + 'px';
  },
});

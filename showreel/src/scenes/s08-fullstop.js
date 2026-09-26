// PLACEHOLDER — replaced by the scene build. Full Stop — the name card (13.125s–15s)
R.scene({
  id: "s08-fullstop",
  start: 13.125,
  end: 15,
  z: 80,
  bg: R.pal.graphite,
  setup(root) {
    this.label = R.el('div', { text: "s08-fullstop · Full Stop — the name card", style: { left: '120px', top: '470px', font: `800 72px ${R.font.display}`, color: R.pal.fog } }, root);
    this.bar = R.el('div', { style: { left: '120px', top: '590px', height: '6px', width: '0px', background: R.pal.fog } }, root);
  },
  update(lt, p) {
    this.bar.style.width = (p * 1680).toFixed(1) + 'px';
  },
});

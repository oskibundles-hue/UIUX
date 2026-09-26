// PLACEHOLDER — replaced by the scene build. Timing — the dot learns to move (1.875s–3.75s)
R.scene({
  id: "s02-timing",
  start: 1.875,
  end: 3.75,
  z: 20,
  bg: R.pal.graphite,
  setup(root) {
    this.label = R.el('div', { text: "s02-timing · Timing — the dot learns to move", style: { left: '120px', top: '470px', font: `800 72px ${R.font.display}`, color: R.pal.fog } }, root);
    this.bar = R.el('div', { style: { left: '120px', top: '590px', height: '6px', width: '0px', background: R.pal.fog } }, root);
  },
  update(lt, p) {
    this.bar.style.width = (p * 1680).toFixed(1) + 'px';
  },
});

// PLACEHOLDER — replaced by the scene build. Range I — C · L · A · U (9.140625s–11.25s)
R.scene({
  id: "s06-range-1",
  start: 9.140625,
  end: 11.25,
  z: 60,
  bg: R.pal.graphite,
  setup(root) {
    this.label = R.el('div', { text: "s06-range-1 · Range I — C · L · A · U", style: { left: '120px', top: '470px', font: `800 72px ${R.font.display}`, color: R.pal.fog } }, root);
    this.bar = R.el('div', { style: { left: '120px', top: '590px', height: '6px', width: '0px', background: R.pal.fog } }, root);
  },
  update(lt, p) {
    this.bar.style.width = (p * 1680).toFixed(1) + 'px';
  },
});

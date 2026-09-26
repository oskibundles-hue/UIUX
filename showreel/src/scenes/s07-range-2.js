// PLACEHOLDER — replaced by the scene build. Range II — D · E · the specimen row · the squeeze (11.25s–13.125s)
R.scene({
  id: "s07-range-2",
  start: 11.25,
  end: 13.125,
  z: 70,
  bg: R.pal.graphite,
  setup(root) {
    this.label = R.el('div', { text: "s07-range-2 · Range II — D · E · the specimen row · the squeeze", style: { left: '120px', top: '470px', font: `800 72px ${R.font.display}`, color: R.pal.fog } }, root);
    this.bar = R.el('div', { style: { left: '120px', top: '590px', height: '6px', width: '0px', background: R.pal.fog } }, root);
  },
  update(lt, p) {
    this.bar.style.width = (p * 1680).toFixed(1) + 'px';
  },
});

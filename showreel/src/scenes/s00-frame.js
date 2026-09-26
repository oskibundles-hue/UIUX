// PLACEHOLDER — replaced by the scene build. The Frame — persistent editorial HUD (0s–15s)
R.scene({
  id: "s00-frame",
  start: 0,
  end: 15,
  z: 900,
  setup(root) {
    this.label = R.el('div', { text: "s00-frame · The Frame — persistent editorial HUD", style: { left: '40px', top: '40px', font: `600 16px ${R.font.mono}`, color: R.pal.fog } }, root);
    this.bar = R.el('div', { style: { left: '0px', top: '1076px', height: '4px', width: '0px', background: R.pal.fog } }, root);
  },
  update(lt, p) {
    this.bar.style.width = (p * 1920).toFixed(1) + 'px';
  },
});

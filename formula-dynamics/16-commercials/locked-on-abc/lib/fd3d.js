/* fd3d.js -- tiny deterministic 3D kit for the FD PPF style frames (3 Oct 2026).
 * A pinhole camera (world y up, camera looks down +z after its rotation), projection to the 1080x1920 page,
 * easing, springs and canvas helpers. Everything is a pure function of the inputs so renderAt(t) stays deterministic.
 */
(function () {
  const D = {};
  D.W = 1080; D.H = 1920; D.FPS = 30000 / 1001; D.BEAT = 60 / 128;
  D.clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  D.p = (t, a, b) => D.clamp((t - a) / (b - a));
  D.lerp = (a, b, x) => a + (b - a) * x;
  D.mix3 = (a, b, x) => [D.lerp(a[0], b[0], x), D.lerp(a[1], b[1], x), D.lerp(a[2], b[2], x)];
  const E = {
    lin: x => x,
    inOut: x => x < .5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2,
    out3: x => 1 - Math.pow(1 - x, 3),
    in3: x => x * x * x,
    outExpo: x => x >= 1 ? 1 : 1 - Math.pow(2, -10 * x),
    inExpo: x => x <= 0 ? 0 : Math.pow(2, 10 * x - 10),
    inOutExpo: x => x <= 0 ? 0 : x >= 1 ? 1 : x < .5 ? Math.pow(2, 20 * x - 10) / 2 : (2 - Math.pow(2, -20 * x + 10)) / 2,
    inOut5: x => x < .5 ? 16 * x ** 5 : 1 - Math.pow(-2 * x + 2, 5) / 2,
    // damped spring: 0 -> 1 with a little overshoot (zeta ~0.45)
    spring: (x, k = 14, z = .42) => x <= 0 ? 0 : 1 - Math.exp(-z * k * x) * Math.cos(k * Math.sqrt(1 - z * z) * x),
  };
  D.E = E;
  // vector
  D.add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
  D.sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  D.mul = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
  D.dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  D.cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  D.norm = a => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
  D.rotY = (v, a) => { const c = Math.cos(a), s = Math.sin(a); return [c * v[0] + s * v[2], v[1], -s * v[0] + c * v[2]]; };
  D.rotX = (v, a) => { const c = Math.cos(a), s = Math.sin(a); return [v[0], c * v[1] - s * v[2], s * v[1] + c * v[2]]; };
  D.rotZ = (v, a) => { const c = Math.cos(a), s = Math.sin(a); return [c * v[0] - s * v[1], s * v[0] + c * v[1], v[2]]; };
  D.deg = Math.PI / 180;

  // camera: eye, yaw (about y), pitch (down positive), focal f in px, principal point
  D.camera = function (o) {
    const cam = Object.assign({ eye: [0, 0, 0], yaw: 0, pitch: 0, roll: 0, f: 2059, cx: 540, cy: 960 }, o);
    cam.view = P => {                       // world -> camera coords (z forward)
      let v = D.sub(P, cam.eye);
      v = D.rotY(v, -cam.yaw); v = D.rotX(v, -cam.pitch); v = D.rotZ(v, -cam.roll);
      return v;
    };
    cam.proj = P => { const v = cam.view(P); const z = Math.max(v[2], 1e-3);
      return [cam.cx + cam.f * v[0] / z, cam.cy - cam.f * v[1] / z, v[2]]; };
    // world point on the ray through screen (x,y) at camera depth d
    cam.unproj = (x, y, d) => {
      let v = [(x - cam.cx) / cam.f * d, -(y - cam.cy) / cam.f * d, d];
      v = D.rotZ(v, cam.roll); v = D.rotX(v, cam.pitch); v = D.rotY(v, cam.yaw);
      return D.add(v, cam.eye);
    };
    // ray through (x,y) hitting the plane y = h
    cam.toPlane = (x, y, h = 0) => {
      const a = cam.unproj(x, y, 1), dir = D.sub(a, cam.eye);
      const s = (h - cam.eye[1]) / dir[1];
      return D.add(cam.eye, D.mul(dir, s));
    };
    return cam;
  };

  // canvas helpers
  D.poly = (g, pts, fill, stroke, lw = 1) => {
    g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]); g.closePath();
    if (fill) { g.fillStyle = fill; g.fill(); }
    if (stroke) { g.strokeStyle = stroke; g.lineWidth = lw; g.stroke(); }
  };
  D.line = (g, pts, stroke, lw = 1, close = false) => {
    if (pts.length < 2) return;
    g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]);
    if (close) g.closePath();
    g.strokeStyle = stroke; g.lineWidth = lw; g.stroke();
  };
  // partial polyline: draw the first fraction q of its length (for draw-on)
  D.partial = (pts, q) => {
    if (q >= 1) return pts; if (q <= 0) return [];
    let L = 0; const seg = [];
    for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(l); L += l; }
    let want = L * q; const out = [pts[0]];
    for (let i = 1; i < pts.length; i++) {
      if (want >= seg[i - 1]) { out.push(pts[i]); want -= seg[i - 1]; continue; }
      const u = want / seg[i - 1]; out.push([D.lerp(pts[i - 1][0], pts[i][0], u), D.lerp(pts[i - 1][1], pts[i][1], u)]); break;
    }
    return out;
  };
  D.rgba = (rgb, a) => `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`;
  D.RED = [254, 15, 19];
  // capture signature: kcapture only takes sub-frame samples when some element's inline style changes
  D.sig = t => { const s = document.getElementById('sig'); if (s) s.style.setProperty('--t', String(Math.round(t * 1e4))); };
  window.D3 = D;
})();

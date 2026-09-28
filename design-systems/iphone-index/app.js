(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var store = { get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
                set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} } };
  var TABS = ['todo', 'pages', 'files', 'rules'];
  var panels = {}; TABS.forEach(function (t) { panels[t] = $('#p-' + t); });
  var bigTitle = $('#bigTitle'), navTitle = $('#navTitle'), nav = $('#nav'), q = $('#q'), qx = $('#qx');
  var current = 'todo';

  // ---------------------------------------------------------------- counts (counted from the page, never typed)
  var nWait = $$('#waiting details.wi').length;          // open items are counted from the list, never typed
  $$('[data-count="wait"]').forEach(function (e) { e.textContent = nWait; });
  var rows = $$('#chron .pg'), dead = rows.filter(function (r) { return r.classList.contains('dead'); });
  $$('[data-count="pages"]').forEach(function (e) { e.textContent = rows.length; });
  var live = rows.length - dead.length, roster = $('#roster');
  // the one hand-stamped figure: how many pages the gallery held when the sweep read it (data-gallery, data-swept)
  var GALLERY = roster ? +(roster.dataset.gallery || live) : live, SWEPT = roster ? (roster.dataset.swept || 'the last sweep') : '';
  if (roster) {
    var ok = live === GALLERY;
    roster.innerHTML = '<span class="' + (ok ? 'ok' : 'no') + '">' + (ok ? '&#10003;' : '&#9888;') + '</span><span><b>' +
      (ok ? 'Every page in the gallery has a row.' : 'Mismatch: ' + Math.abs(live - GALLERY) + (live > GALLERY ? ' more rows than gallery pages.' : ' gallery pages with no row.')) +
      '</b> ' + rows.length + ' rows counted on this page: ' + live + ' that open, ' + dead.length +
      ' that no longer do. The gallery held ' + GALLERY + ' pages when it was read on ' + SWEPT + '.</span>';
  }

  // ---------------------------------------------------------------- tabs
  function show(tab, opts) {
    if (TABS.indexOf(tab) < 0) tab = 'todo';
    current = tab;
    TABS.forEach(function (t) { panels[t].hidden = t !== tab; });
    $$('.tab').forEach(function (b) { if (b.dataset.tab === tab) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current'); });
    var title = panels[tab].dataset.title;
    bigTitle.textContent = title; navTitle.textContent = title;
    document.title = 'Download Everything';
    store.set('de-tab', tab);
    try { history.replaceState(null, '', '#' + tab); } catch (e) {}
    if (!opts || !opts.keepScroll) window.scrollTo(0, 0);
  }
  $$('.tab').forEach(function (b) {
    b.addEventListener('click', function () {
      if (q.value) { q.value = ''; runSearch(); }
      if (b.dataset.tab === current) { window.scrollTo({ top: 0, behavior: 'smooth' }); return; }
      show(b.dataset.tab);
    });
  });
  function goTo(tab, id) {
    if (q.value) { q.value = ''; runSearch(); }
    show(tab);
    if (id) { var el = document.getElementById(id); if (el) requestAnimationFrame(function () { el.scrollIntoView({ block: 'start' }); }); }
  }
  $$('[data-go]').forEach(function (b) { b.addEventListener('click', function () { goTo(b.dataset.go, b.dataset.to); }); });
  $$('[data-jump]').forEach(function (b) { b.addEventListener('click', function () { var el = document.getElementById(b.dataset.jump); if (el) el.scrollIntoView({ block: 'start', behavior: 'smooth' }); }); });

  // ---------------------------------------------------------------- nav bar: solid + small title once the big title is gone
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (es) { nav.classList.toggle('solid', !es[0].isIntersecting); },
      { rootMargin: '-44px 0px 0px 0px', threshold: 0 }).observe(bigTitle);
  }
  $('#navSearch').addEventListener('click', function () { window.scrollTo(0, 0); q.focus(); });
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== q && !/INPUT|TEXTAREA/.test((document.activeElement || {}).tagName || '')) { e.preventDefault(); window.scrollTo(0, 0); q.focus(); }
    if (e.key === 'Escape' && document.activeElement === q) { q.value = ''; runSearch(); q.blur(); }
  });

  // ---------------------------------------------------------------- page filters
  var filter = 'all';
  function applyFilter() {
    rows.forEach(function (r) {
      var on = filter === 'all' || (filter === 'needs' ? r.dataset.needs === '1' : r.dataset.ws === filter);
      r.hidden = !on;
    });
    $$('#chron .day').forEach(function (g) { g.hidden = !$$('.pg', g).some(function (r) { return !r.hidden; }); });
  }
  $$('.chips [data-f]').forEach(function (c) {
    var f = c.dataset.f, n = rows.filter(function (r) { return f === 'all' || (f === 'needs' ? r.dataset.needs === '1' : r.dataset.ws === f); }).length;
    $('.chip-n', c).textContent = n;
    c.addEventListener('click', function () {
      filter = f;
      $$('.chips [data-f]').forEach(function (x) { var on = x === c; x.classList.toggle('on', on); x.setAttribute('aria-pressed', on ? 'true' : 'false'); });
      applyFilter();
    });
  });

  // ---------------------------------------------------------------- search, across every tab
  var units = $$('.panel .s').filter(function (el) { return !el.closest('.nosearch'); }).map(function (el) { return { el: el, t: norm(el.textContent) }; });
  var groups = $$('.panel .grp');
  function norm(s) { return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[‘’]/g, "'").replace(/\s+/g, ' '); }
  var opened = [];
  function runSearch() {
    var raw = q.value.trim(), words = norm(raw).split(' ').filter(Boolean);
    qx.hidden = !raw;
    opened.forEach(function (d) { d.open = false; }); opened = [];
    if (!words.length) {
      document.body.classList.remove('searching');
      units.forEach(function (u) { u.el.hidden = false; });
      groups.forEach(function (g) { g.hidden = false; });
      applyFilter();
      show(current, { keepScroll: true });
      $('#results').hidden = true; $('#empty').hidden = true;
      return;
    }
    document.body.classList.add('searching');
    bigTitle.textContent = 'Search'; navTitle.textContent = 'Search';
    TABS.forEach(function (t) { panels[t].hidden = false; });
    var hits = 0;
    units.forEach(function (u) {
      var m = words.every(function (w) { return u.t.indexOf(w) >= 0; });
      u.el.hidden = !m;
      if (m) {
        hits++;
        if (u.el.tagName === 'DETAILS' && !u.el.open) {
          var sum = norm(($('summary', u.el) || {}).textContent);
          if (!words.every(function (w) { return sum.indexOf(w) >= 0; })) { u.el.open = true; opened.push(u.el); }
        }
      }
    });
    groups.forEach(function (g) { g.hidden = !units.some(function (u) { return !u.el.hidden && g.contains(u.el); }); });
    TABS.forEach(function (t) { panels[t].hidden = !units.some(function (u) { return !u.el.hidden && panels[t].contains(u.el); }); });
    var r = $('#results'); r.hidden = !hits; r.textContent = hits + (hits === 1 ? ' result' : ' results') + ' for “' + raw + '”';
    $('#empty').hidden = hits > 0;
  }
  q.addEventListener('input', runSearch);
  qx.addEventListener('click', function () { q.value = ''; runSearch(); q.focus(); });

  // ---------------------------------------------------------------- start on the tab in the link, else the last one used
  var h = (location.hash || '').replace('#', '');
  show(TABS.indexOf(h) >= 0 ? h : (store.get('de-tab') || 'todo'), { keepScroll: false });
})();

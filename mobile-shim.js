/* Phone-width safety net, inlined into every explorer by build.py.
   On narrow screens, anything wider than the page (a long equation, a table,
   a fixed-width figure) is shrunk to fit or given its own sideways scroll, so
   the page itself never scrolls horizontally. Does nothing on wide screens. */
(function () {
  var LIMIT = 820, MEDIA = { CANVAS: 1, IMG: 1, VIDEO: 1, svg: 1, IFRAME: 1 };

  function scrollsItself(el) {
    for (var p = el.parentElement; p && p !== document.body; p = p.parentElement) {
      var o = getComputedStyle(p).overflowX;
      if (o === 'auto' || o === 'scroll') return true;
    }
    return false;
  }

  function fix(el, vw, depth) {
    var cs = getComputedStyle(el);
    if (cs.position === 'fixed' || depth > 14) return;
    if (MEDIA[el.tagName]) {
      el.style.maxWidth = '100%';
      if (el.tagName !== 'IFRAME' && !el.style.height) el.style.height = 'auto';
      return;
    }
    if (el.tagName === 'TABLE' || cs.display === 'table') {
      el.style.display = 'block'; el.style.maxWidth = '100%'; el.style.overflowX = 'auto';
      return;
    }
    if (cs.display === 'inline') el.style.display = 'inline-block';
    el.style.minWidth = '0'; el.style.maxWidth = '100%'; el.style.boxSizing = 'border-box';
    var edge = Math.min(el.getBoundingClientRect().right, vw) + 1;
    function tooWide() {
      return [].filter.call(el.children, function (c) {
        var r = c.getBoundingClientRect();
        return r.width && r.right > edge && !c.ownerSVGElement;
      });
    }
    var wide = tooWide();
    if (wide.length && cs.display.indexOf('flex') >= 0 && cs.flexDirection.indexOf('row') === 0 && cs.flexWrap === 'nowrap') {
      el.style.flexWrap = 'wrap';   // a row of controls too long for the screen: let it wrap
      wide = tooWide();
    }
    if (wide.length && cs.whiteSpace !== 'nowrap') {
      wide.forEach(function (c) { fix(c, vw, depth + 1); });
    }
    if (el.scrollWidth > el.clientWidth + 1) {
      el.style.overflowX = 'auto';
      if (el.style.display === 'inline-block') el.style.verticalAlign = 'bottom';
    }
  }

  function run() {
    var root = document.documentElement, vw = root.clientWidth;
    if (vw > LIMIT || !document.body) return;
    for (var pass = 0; pass < 4 && root.scrollWidth > vw + 1; pass++) {
      var all = document.body.getElementsByTagName('*');
      for (var i = 0; i < all.length; i++) {
        var el = all[i], r = el.getBoundingClientRect();
        if (!r.width || r.right <= vw + 1 || el.ownerSVGElement) continue;
        var p = el.parentElement;
        if (p !== document.body && p.getBoundingClientRect().right > vw + 1) continue; // start at the outermost offender
        if (scrollsItself(el)) continue;
        var ps = getComputedStyle(p);
        if (ps.display.indexOf('flex') >= 0 && ps.flexDirection.indexOf('row') === 0 && ps.flexWrap === 'nowrap') {
          p.style.flexWrap = 'wrap';   // a row of controls too long for the screen: let it wrap
          if (el.getBoundingClientRect().right <= vw + 1) continue;
        }
        fix(el, vw, 0);
      }
    }
  }

  var timer;
  function soon() { clearTimeout(timer); run(); timer = setTimeout(function () { run(); timer = setTimeout(run, 700); }, 300); }
  window.addEventListener('load', soon);
  window.addEventListener('resize', soon);
  ['click', 'change', 'toggle'].forEach(function (ev) {
    document.addEventListener(ev, function () { setTimeout(soon, 30); }, true);
  });
  if (document.readyState !== 'loading') soon(); else document.addEventListener('DOMContentLoaded', soon);
})();

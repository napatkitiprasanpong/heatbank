/* Shared DOM helpers and pictograms. All text goes in through textContent (pack data is never parsed as HTML).
   Pictograms are drawn for this project (no third-party icon set). Red uses a no-entry bar, not a red cross (protected emblem). */
(function (root) {
  "use strict";
  var NS = "http://www.w3.org/2000/svg";

  function h(tag, attrs, kids) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "text") e.textContent = attrs[k]; else if (k === "class") e.className = attrs[k]; else e.setAttribute(k, attrs[k]);
    });
    (kids || []).forEach(function (c) { if (c) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }

  var PIC = {
    pic_water: '<path d="M32 6 C32 6 14 28 14 40 a18 18 0 0 0 36 0 C50 28 32 6 32 6 Z" fill="currentColor"/>',
    pic_shade: '<path d="M6 30 a26 22 0 0 1 52 0 Z" fill="currentColor"/><rect x="30" y="30" width="4" height="24" fill="currentColor"/><rect x="18" y="54" width="28" height="4" rx="2" fill="currentColor"/>',
    pic_cooldown: '<g stroke="currentColor" stroke-width="5" stroke-linecap="round"><line x1="32" y1="8" x2="32" y2="56"/><line x1="11" y1="20" x2="53" y2="44"/><line x1="11" y1="44" x2="53" y2="20"/></g><circle cx="32" cy="32" r="6" fill="currentColor"/>',
    pic_stop_medic: '<polygon points="22,4 42,4 60,22 60,42 42,60 22,60 4,42 4,22" fill="currentColor"/><rect x="16" y="28" width="32" height="8" rx="2" fill="var(--pic-knockout,#fff)"/>'
  };
  function pictogram(id, size) {
    var s = document.createElementNS(NS, "svg");
    s.setAttribute("viewBox", "0 0 64 64"); s.setAttribute("width", size || 64); s.setAttribute("height", size || 64);
    s.setAttribute("aria-hidden", "true"); s.setAttribute("focusable", "false");
    s.innerHTML = PIC[id] || "";
    return s;
  }

  // Level shapes: circle, triangle, diamond, square. Meaning never depends on colour alone.
  var SHAPE = [
    '<circle cx="12" cy="12" r="8" fill="currentColor"/>',
    '<polygon points="12,3 22,21 2,21" fill="currentColor"/>',
    '<polygon points="12,2 22,12 12,22 2,12" fill="currentColor"/>',
    '<rect x="3" y="3" width="18" height="18" fill="currentColor"/>'
  ];
  function shape(level, size) {
    var s = document.createElementNS(NS, "svg");
    s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("width", size || 20); s.setAttribute("height", size || 20);
    s.setAttribute("aria-hidden", "true"); s.setAttribute("focusable", "false");
    s.innerHTML = SHAPE[level] || "";
    return s;
  }

  function initLang(pack, onChange) {
    var nav = (navigator.language || "en").slice(0, 2);
    var q = /[?&]lang=(\w+)/.exec(location.search);
    var lang = q && pack.strings[q[1]] ? q[1] : (pack.strings[nav] ? nav : "en");
    var sel = document.getElementById("lang");
    Object.keys(pack.strings).forEach(function (l) {
      var o = h("option", { value: l, text: pack.lang_label[l] + (pack.lang_status[l] && l !== "en" ? " (draft)" : "") });
      if (l === lang) o.selected = true; sel.appendChild(o);
    });
    sel.addEventListener("change", function () { onChange(sel.value); });
    return lang;
  }

  root.HBUI = { h: h, pictogram: pictogram, shape: shape, initLang: initLang };
})(window);

/* Touch-Geräte: Erklärungen, die am Desktop per Mauszeiger (title-Attribut) erscheinen,
   öffnen sich beim Antippen als Karte. Ein zweites Antippen oder Scrollen schließt sie. */
(function () {
  var touch = ("ontouchstart" in window) || (navigator.maxTouchPoints > 0);
  if (!touch) return;
  var tip = null, owner = null;

  function hide() {
    if (tip) { tip.remove(); tip = null; }
    if (owner && owner.dataset.tip) owner.setAttribute("title", owner.dataset.tip);
    owner = null;
  }

  document.addEventListener("click", function (e) {
    if (e.target.closest(".touch-tip")) { hide(); return; }
    var el = e.target.closest("[title], [data-tip]");
    if (!el || el.closest(".js-plotly-plot") || el.tagName === "IFRAME") { hide(); return; }
    var text = el.getAttribute("title") || el.dataset.tip;
    if (!text) { hide(); return; }
    if (owner === el) { hide(); return; }
    hide();
    owner = el;
    el.dataset.tip = text;
    el.removeAttribute("title");          // verhindert den nativen Tooltip parallel
    tip = document.createElement("div");
    tip.className = "touch-tip";
    tip.setAttribute("role", "tooltip");
    tip.textContent = text;
    document.body.appendChild(tip);
    var r = el.getBoundingClientRect();
    var w = Math.min(320, window.innerWidth - 24);
    tip.style.width = w + "px";
    var left = Math.max(12, Math.min(r.left + r.width / 2 - w / 2, window.innerWidth - w - 12));
    tip.style.left = left + "px";
    tip.style.top = (r.bottom + window.scrollY + 8) + "px";
  }, true);

  window.addEventListener("scroll", hide, { passive: true });
  window.addEventListener("resize", hide);
})();

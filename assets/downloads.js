/* Download-Links: Beim Klick wird die Adresse aus den aktuellen Einstellungen gebildet
   (Zeitraum, Gebühren, Sprache), danach lädt der Browser die Datei direkt vom Server –
   mit eigener Fortschrittsanzeige und ohne Umweg über die Dash-Callbacks. */
(function () {
  function sliderValue(id) {
    var root = document.getElementById(id);
    if (!root) return "";
    var thumb = root.querySelector('[role="slider"][aria-valuenow]');
    if (thumb) return thumb.getAttribute("aria-valuenow");
    var input = root.querySelector('input[type="number"]');
    return input ? input.value : "";
  }
  function current(kind) {
    var period = document.querySelector('#period input:checked');
    var lang = (document.getElementById("lang-current") || {}).textContent || "";
    var q = new URLSearchParams({
      period: period ? period.value : "all",
      mgmt: sliderValue("mgmt-fee"),
      perf: sliderValue("perf-fee"),
      lang: (lang.trim().toLowerCase() || document.documentElement.lang || "en")
    });
    return "/download/" + kind + "?" + q.toString();
  }
  document.addEventListener("click", function (e) {
    var a = e.target.closest("a.dl-btn");
    if (!a || a.classList.contains("is-disabled")) return;
    var kind = a.id === "btn-pdf" ? "pdf" : "xlsx";
    a.setAttribute("href", current(kind));      // vor der Navigation gesetzt -> wird verwendet
    a.classList.add("is-busy");
    setTimeout(function () { a.classList.remove("is-busy"); }, 5000);
  }, true);
})();

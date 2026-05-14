// Google Analytics 4 — window.__GA4_MEASUREMENT_ID__ が G-XXXXXXXXXX のときのみ読み込み
(function () {
  var raw = "";
  try {
    if (typeof window !== "undefined" && window.__GA4_MEASUREMENT_ID__) {
      raw = String(window.__GA4_MEASUREMENT_ID__).trim();
    }
  } catch (_e) {}
  var MID = /^G-[A-Z0-9]+$/.test(raw) ? raw : "";
  if (!MID) return;

  if (window.gtag && window.dataLayer) {
    try {
      window.gtag("config", MID);
    } catch (_e) {}
    return;
  }

  window.dataLayer = window.dataLayer || [];
  function gtag() {
    window.dataLayer.push(arguments);
  }
  window.gtag = gtag;
  gtag("js", new Date());

  var s = document.createElement("script");
  s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(MID);
  document.head.appendChild(s);

  gtag("config", MID);
})();

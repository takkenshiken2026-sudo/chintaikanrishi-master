// Google Analytics 4 — window.__GA4_MEASUREMENT_ID__ で上書き可（未設定・空なら下記の既定ID）
(function () {
  var DEFAULT_MID = "G-NYSHQLECDS";
  var raw = "";
  try {
    if (typeof window !== "undefined" && window.__GA4_MEASUREMENT_ID__ != null) {
      raw = String(window.__GA4_MEASUREMENT_ID__).trim();
    }
  } catch (_e) {}
  if (!raw) raw = DEFAULT_MID;
  var MID = /^G-[A-Za-z0-9]+$/.test(raw) ? raw : "";
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

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

  /**
   * SPA 等で URL・title が変わったあとに呼ぶ。index.html の gotoPage / popstate から利用。
   * 引数省略時は現在の location + document.title。
   */
  function ga4PageView(pagePath, pageTitle) {
    if (typeof window.gtag !== "function") return;
    var path = pagePath != null && String(pagePath) ? String(pagePath) : "";
    if (!path && typeof location !== "undefined") {
      path = location.pathname + location.search + location.hash;
    }
    var title = pageTitle != null ? String(pageTitle) : typeof document !== "undefined" ? document.title : "";
    try {
      var o = { page_path: path, page_title: title };
      window.gtag("config", MID, o);
    } catch (_e) {}
  }
  window.ga4PageView = ga4PageView;

  if (window.__GA4_SNIPPET_INIT__ === MID) return;
  window.__GA4_SNIPPET_INIT__ = MID;

  try {
    if (document.querySelector('script[src*="googletagmanager.com/gtag/js"][data-ga4-mid="' + MID + '"]')) {
      ga4PageView();
      return;
    }
  } catch (_e) {}

  window.dataLayer = window.dataLayer || [];
  function gtag() {
    window.dataLayer.push(arguments);
  }
  window.gtag = gtag;
  gtag("js", new Date());

  var s = document.createElement("script");
  s.async = true;
  s.setAttribute("data-ga4-mid", MID);
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(MID);
  document.head.appendChild(s);

  try {
    gtag("config", MID);
  } catch (_e2) {}
})();

// click-log.js - records page tab clicks (all pages) and button clicks
// (PTZ grid page) with the signed-in user name and timestamp. Each click
// is sent as one JSON line to the click-log endpoint, appended to
// monitoring\logs\clicks.log by the dashboard server.
(function () {
  function currentUser() {
    try {
      var s = JSON.parse(sessionStorage.getItem('shekmunSession') || 'null');
      if (s && s.name) return s.name;
    } catch (e) {}
    try {
      var r = localStorage.getItem('shekmunRememberUser');
      if (r) return r;
    } catch (e) {}
    return 'localhost';
  }

  function sendLog(page, action) {
    try {
      var payload = JSON.stringify({
        ts: new Date().toISOString(),
        user: currentUser(),
        page: page,
        action: action
      });
      if (navigator.sendBeacon) {
        navigator.sendBeacon('click-log', payload);
      } else {
        fetch('click-log', { method: 'POST', body: payload, keepalive: true }).catch(function () {});
      }
    } catch (e) {}
  }

  var pageName = (location.pathname.split('/').pop() || 'unknown');
  if (pageName === '') pageName = 'index';

  // Tab bar clicks (pages with nav.tabs)
  var nav = document.querySelector('nav.tabs');
  if (nav) {
    nav.addEventListener('click', function (e) {
      var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
      if (a) sendLog(pageName, 'tab:' + a.getAttribute('href'));
    });
  }

  // Button / link clicks (PTZ grid page and any other controls)
  document.addEventListener('click', function (e) {
    var el = e.target && e.target.closest ? e.target.closest('button, a[href]') : null;
    if (!el) return;
    if (el.closest && el.closest('nav.tabs')) return;   // tab clicks handled above
    var action = el.title || el.textContent || el.getAttribute('href') || '';
    action = action.trim().replace(/\s+/g, ' ').slice(0, 80);
    if (!action) return;
    sendLog(pageName, 'click:' + action);
  });
})();
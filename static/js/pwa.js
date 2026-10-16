(function () {
  'use strict';

  function updateNetworkStatus() {
    var status = document.getElementById('networkStatus');
    if (!status) return;
    status.hidden = navigator.onLine;
  }

  function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) return;
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/serviceworker.js', { scope: '/' })
        .catch(function (error) { console.warn('Service worker registration failed:', error); });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    updateNetworkStatus();
    window.addEventListener('online', updateNetworkStatus);
    window.addEventListener('offline', updateNetworkStatus);
    registerServiceWorker();
  });
}());

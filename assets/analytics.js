(function () {
  'use strict';

  var MEASUREMENT_ID = 'G-L9TTK0SBD1';

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () {
    window.dataLayer.push(arguments);
  };

  var tag = document.createElement('script');
  tag.async = true;
  tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(MEASUREMENT_ID);
  document.head.appendChild(tag);

  window.gtag('js', new Date());
  window.gtag('config', MEASUREMENT_ID, {
    send_page_view: true
  });

  function track(name, params) {
    if (typeof window.gtag === 'function') {
      window.gtag('event', name, params || {});
    }
  }

  document.addEventListener('click', function (event) {
    var link = event.target.closest && event.target.closest('a[href]');
    if (!link) return;

    var href = link.getAttribute('href') || '';
    var absolute;
    try {
      absolute = new URL(href, window.location.href);
    } catch (e) {
      return;
    }

    var label = (link.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 120);

    if (/\/review\.html(?:$|[?#])/.test(absolute.pathname + absolute.search + absolute.hash)) {
      track('career_review_click', {
        link_url: absolute.href,
        link_text: label,
        source_path: window.location.pathname
      });
    }

    if (absolute.origin !== window.location.origin) {
      track('outbound_click', {
        link_url: absolute.href,
        link_domain: absolute.hostname,
        link_text: label,
        source_path: window.location.pathname
      });
    }
  }, true);
})();

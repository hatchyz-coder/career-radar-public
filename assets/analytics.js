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
  window.gtag('config', MEASUREMENT_ID, { send_page_view: true });

  function track(name, params) {
    if (typeof window.gtag === 'function') window.gtag('event', name, params || {});
  }

  function cleanLabel(link) {
    return (link.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 120);
  }

  document.addEventListener('click', function (event) {
    var link = event.target.closest && event.target.closest('a[href]');
    if (!link) return;

    var absolute;
    try {
      absolute = new URL(link.getAttribute('href') || '', window.location.href);
    } catch (e) {
      return;
    }

    var label = cleanLabel(link);
    var sourcePath = window.location.pathname;
    var targetPath = absolute.pathname;

    if (/\/review\.html$/.test(targetPath)) {
      track('career_review_click', {
        link_url: absolute.href,
        link_text: label,
        source_path: sourcePath
      });
    }

    if (absolute.origin === window.location.origin && /\/(?:ja|en)\/articles\//.test(targetPath) && !/\/articles\/$/.test(targetPath)) {
      track('internal_article_click', {
        target_path: targetPath,
        link_text: label,
        source_path: sourcePath
      });

      if (link.closest && link.closest('.pv-related')) {
        track('related_article_click', {
          target_path: targetPath,
          link_text: label,
          source_path: sourcePath
        });
      }

      if (/\/(?:ja|en)\/articles\/$/.test(sourcePath)) {
        track('article_library_click', {
          target_path: targetPath,
          link_text: label,
          source_path: sourcePath
        });
      }
    }

    if (absolute.origin === window.location.origin && /\/ja\/topics\//.test(targetPath)) {
      track('topic_guide_click', {
        target_path: targetPath,
        link_text: label,
        source_path: sourcePath
      });
    }

    if (absolute.origin !== window.location.origin) {
      track('outbound_click', {
        link_url: absolute.href,
        link_domain: absolute.hostname,
        link_text: label,
        source_path: sourcePath
      });
    }
  }, true);

  var sentDepth = {};
  function checkDepth() {
    var doc = document.documentElement;
    var max = Math.max(doc.scrollHeight - window.innerHeight, 1);
    var pct = Math.round((window.scrollY / max) * 100);
    [50, 90].forEach(function (threshold) {
      if (pct >= threshold && !sentDepth[threshold]) {
        sentDepth[threshold] = true;
        track('scroll_depth', {
          percent_scrolled: threshold,
          page_path: window.location.pathname
        });
      }
    });
  }

  window.addEventListener('scroll', checkDepth, { passive: true });
})();

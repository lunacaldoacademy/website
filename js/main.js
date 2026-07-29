/* ルナカルドアカデミー 公式サイト — 依存ライブラリなし */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* --- 1. スクロールで要素をふわっと表示 --- */
  var targets = document.querySelectorAll('.reveal');

  if (reduceMotion || !('IntersectionObserver' in window)) {
    Array.prototype.forEach.call(targets, function (el) {
      el.classList.add('is-visible');
    });
  } else {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    Array.prototype.forEach.call(targets, function (el) {
      observer.observe(el);
    });
  }

  /* --- 2. FAQ は1つ開いたら他を閉じる --- */
  var faqItems = document.querySelectorAll('.faq details');
  Array.prototype.forEach.call(faqItems, function (item) {
    item.addEventListener('toggle', function () {
      if (!item.open) return;
      Array.prototype.forEach.call(faqItems, function (other) {
        if (other !== item) other.open = false;
      });
    });
  });

  /* --- 3. 現在地に応じてヘッダーナビをハイライト --- */
  var navLinks = document.querySelectorAll('.header__nav a[href^="#"]');
  var sections = [];
  Array.prototype.forEach.call(navLinks, function (link) {
    var el = document.getElementById(link.getAttribute('href').slice(1));
    if (el) sections.push({ link: link, el: el });
  });

  if (sections.length && 'IntersectionObserver' in window) {
    var navObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var match = sections.filter(function (s) { return s.el === entry.target; })[0];
        if (!match || match.link.classList.contains('is-cta')) return;
        match.link.style.background = entry.isIntersecting ? 'var(--c-yellow-soft)' : '';
      });
    }, { rootMargin: '-40% 0px -50% 0px' });

    sections.forEach(function (s) { navObserver.observe(s.el); });
  }
})();

/* ルナカルドアカデミー 公式サイト — 依存ライブラリなし */
(function () {
  'use strict';

  /* index.html の安全網へ「JSは無事に動いた」と伝える */
  window.__lcaReady = true;

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hasIO = 'IntersectionObserver' in window;
  var each = function (list, fn) { Array.prototype.forEach.call(list, fn); };

  var hero = document.querySelector('.hero');

  /* -----------------------------------------------------------
     1. スクロールで要素を表示（reveal / stagger）
     ----------------------------------------------------------- */
  var revealTargets = document.querySelectorAll('.reveal, .stagger');

  if (reduceMotion || !hasIO) {
    each(revealTargets, function (el) { el.classList.add('is-visible'); });
  } else {
    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        revealObserver.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    each(revealTargets, function (el) { revealObserver.observe(el); });
  }

  /* -----------------------------------------------------------
     2. 数字のカウントアップ
     HTMLには最初から最終値が入っているので、JSが動かなくても正しく読める
     ----------------------------------------------------------- */
  var counters = document.querySelectorAll('[data-count]');

  function renderCount(el, value) {
    var suffix = el.getAttribute('data-suffix');
    el.innerHTML = String(value) + (suffix ? '<small>' + suffix + '</small>' : '');
  }

  function runCount(el) {
    var goal = parseInt(el.getAttribute('data-count'), 10);
    if (isNaN(goal)) return;
    var duration = 1100;
    var start = null;

    function tick(now) {
      if (start === null) start = now;
      var p = Math.min((now - start) / duration, 1);
      // ease-out（終わりにかけてゆっくり）
      var eased = 1 - Math.pow(1 - p, 3);
      renderCount(el, Math.round(goal * eased));
      if (p < 1) requestAnimationFrame(tick);
    }
    renderCount(el, 0);
    requestAnimationFrame(tick);
  }

  if (counters.length && !reduceMotion && hasIO) {
    var countObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        runCount(entry.target);
        countObserver.unobserve(entry.target);
      });
    }, { threshold: 0.6 });

    each(counters, function (el) { countObserver.observe(el); });
  }

  /* -----------------------------------------------------------
     3. FAQ は1つ開いたら他を閉じる
     ----------------------------------------------------------- */
  var faqItems = document.querySelectorAll('.faq details');
  each(faqItems, function (item) {
    item.addEventListener('toggle', function () {
      if (!item.open) return;
      each(faqItems, function (other) {
        if (other !== item) other.open = false;
      });
    });
  });

  /* -----------------------------------------------------------
     4. 現在地に応じてヘッダーナビをハイライト
     ----------------------------------------------------------- */
  var navLinks = document.querySelectorAll('.header__nav a[href^="#"]');
  var navPairs = [];
  each(navLinks, function (link) {
    var el = document.getElementById(link.getAttribute('href').slice(1));
    if (el) navPairs.push({ link: link, el: el });
  });

  if (navPairs.length && hasIO) {
    var navObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var pair = navPairs.filter(function (p) { return p.el === entry.target; })[0];
        if (!pair || pair.link.classList.contains('is-cta')) return;
        pair.link.classList.toggle('is-active', entry.isIntersecting);
      });
    }, { rootMargin: '-40% 0px -50% 0px' });

    navPairs.forEach(function (p) { navObserver.observe(p.el); });
  }

  /* -----------------------------------------------------------
     5. スクロールに応じた追従UI
        - ヘッダーの影と進捗バー
        - スマホ下部CTA（ヒーローを過ぎたら出す）
        - トップへ戻るボタン
     ----------------------------------------------------------- */
  var header = document.querySelector('.header');
  var progress = document.querySelector('.header__progress');
  var stickyCta = document.querySelector('.sticky-cta');
  var toTop = document.querySelector('.to-top');
  var ticking = false;

  function onScroll() {
    var y = window.pageYOffset || document.documentElement.scrollTop;
    var max = document.documentElement.scrollHeight - window.innerHeight;
    var ratio = max > 0 ? Math.min(y / max, 1) : 0;

    if (header) header.classList.toggle('is-stuck', y > 8);
    if (progress) progress.style.transform = 'scaleX(' + ratio + ')';

    var passedHero = y > (hero ? hero.offsetHeight * 0.6 : 400);
    if (stickyCta) stickyCta.classList.toggle('is-shown', passedHero);
    if (toTop) toTop.classList.toggle('is-shown', y > 800);

    ticking = false;
  }

  function requestScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(onScroll);
  }

  window.addEventListener('scroll', requestScroll, { passive: true });
  window.addEventListener('resize', requestScroll);
  onScroll();
})();

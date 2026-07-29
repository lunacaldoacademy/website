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
     1. トップ画像のスライドショー
        枚数は img-src/hero/ の中身に応じて index.html 側で増減する。
        1枚しかないときは何もしない。
     ----------------------------------------------------------- */
  (function initHeroSlider() {
    var slider = document.querySelector('.hero__slider');
    if (!slider) return;

    var slides = slider.querySelectorAll('.hero__slide');
    if (slides.length < 2) return;

    var interval = parseInt(slider.getAttribute('data-interval'), 10) || 5000;
    var index = 0;
    var timer = null;

    /* 何枚目かを示す点を作る（JSがある環境だけに置く） */
    var dots = document.createElement('div');
    dots.className = 'hero__dots';
    dots.setAttribute('role', 'tablist');
    dots.setAttribute('aria-label', 'トップ画像の切り替え');

    var buttons = [];
    each(slides, function (slide, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'hero__dot';
      b.setAttribute('role', 'tab');
      b.setAttribute('aria-label', (i + 1) + '枚目の写真を表示');
      b.addEventListener('click', function () { show(i); restart(); });
      dots.appendChild(b);
      buttons.push(b);
    });
    slider.parentNode.insertBefore(dots, slider.nextSibling);

    function show(next) {
      index = (next + slides.length) % slides.length;
      each(slides, function (slide, i) {
        slide.classList.toggle('is-current', i === index);
      });
      buttons.forEach(function (b, i) {
        b.setAttribute('aria-current', i === index ? 'true' : 'false');
      });
    }

    /* 「動きを減らす」設定でも切り替えは続ける。
       その場合はフェードをやめて瞬時に入れ替える（CSS側で transition を無効化）。 */
    function start() {
      if (timer) return;
      timer = setInterval(function () { show(index + 1); }, interval);
    }
    function stop() {
      if (!timer) return;
      clearInterval(timer);
      timer = null;
    }
    function restart() { stop(); start(); }

    /* マウスを乗せている間・キーボード操作中・タブを離れている間は止める */
    slider.addEventListener('mouseenter', stop);
    slider.addEventListener('mouseleave', start);
    dots.addEventListener('mouseenter', stop);
    dots.addEventListener('mouseleave', start);
    dots.addEventListener('focusin', stop);
    dots.addEventListener('focusout', start);
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stop(); else start();
    });

    show(0);
    start();
  })();

  /* -----------------------------------------------------------
     2. スクロールで要素を表示（reveal / stagger）
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

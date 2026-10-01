/* Keep TOC generation and ScrollSpy initialization in the same ready callback.
 * Bootstrap's window.load handler can run before jQuery's asynchronous ready
 * callbacks on a cached page, leaving ScrollSpy with an empty list of targets.
 */
$(function() {
  const $toc = $('#toc');
  const $content = $('.post-content');

  if (!$toc.length || !$content.length || !window.Toc || !$.fn.scrollspy) {
    return;
  }

  Toc.init({ $nav: $toc, $scope: $content });
  const $body = $('body');
  $body.scrollspy({ target: '#toc' });

  let refreshPending = false;
  function refresh() {
    if (refreshPending) {
      return;
    }

    refreshPending = true;
    window.requestAnimationFrame(function() {
      refreshPending = false;
      $body.scrollspy('refresh');
      // Refresh recalculates offsets; a scroll event also updates the highlight.
      $(window).trigger('scroll.bs.scrollspy');
    });
  }

  $(window).on('load.toc pageshow.toc resize.toc', refresh);
  const contentArea = document.getElementById('main') || $content[0];
  // Image load events do not bubble, including images loaded lazily later on.
  contentArea.addEventListener('load', refresh, true);

  if (window.ResizeObserver) {
    const observer = new ResizeObserver(refresh);
    observer.observe(contentArea);
  }

  if (document.fonts) {
    document.fonts.ready.then(refresh);
  }
});

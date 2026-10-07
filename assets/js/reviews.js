// 鉴赏页：按类型筛选封面墙；点击卡片在所在行下方展开详情，同时只展开一件。
(() => {
  const wall = document.querySelector('.reviews-wall');
  if (!wall) return;

  const cards = Array.from(wall.querySelectorAll('.work-card'));
  const emptyState = document.querySelector('.reviews-empty');
  const sources = new Map(
    Array.from(document.querySelectorAll('template[data-detail-for]')).map((template) => [
      template.dataset.detailFor,
      template
    ])
  );
  const detailRow = document.createElement('div');
  detailRow.className = 'work-detail-row';
  detailRow.id = 'work-detail-panel';
  detailRow.setAttribute('role', 'region');
  detailRow.hidden = true;
  wall.append(detailRow);

  let openCard = null;

  const positionDetail = (card) => {
    const focused = detailRow.contains(document.activeElement) ? document.activeElement : null;
    // Measure the grid without the old full-width panel. Hidden cards do not
    // participate in a row, even when interleaved with visible cards in the DOM.
    detailRow.hidden = true;
    const top = card.offsetTop;
    const rowCards = cards.filter((item) => !item.hidden && Math.abs(item.offsetTop - top) < 1);
    rowCards[rowCards.length - 1].after(detailRow);
    detailRow.hidden = false;
    if (focused) focused.focus({ preventScroll: true });
  };

  const close = (restoreFocus = false) => {
    if (!openCard) return;
    const trigger = openCard.querySelector('.work-card-main');
    trigger.setAttribute('aria-expanded', 'false');
    openCard.classList.remove('expanded');
    openCard = null;
    detailRow.hidden = true;
    detailRow.replaceChildren();
    detailRow.removeAttribute('aria-labelledby');
    if (restoreFocus) trigger.focus({ preventScroll: true });
  };

  const open = (card) => {
    const template = sources.get(card.dataset.workId);
    if (!template) return;
    if (openCard === card) {
      close(true);
      return;
    }
    close();
    detailRow.append(...template.content.cloneNode(true).childNodes);
    const title = detailRow.querySelector('.work-detail-title');
    title.id = `work-detail-title-${card.dataset.workId}`;
    detailRow.setAttribute('aria-labelledby', title.id);
    positionDetail(card);
    card.classList.add('expanded');
    card.querySelector('.work-card-main').setAttribute('aria-expanded', 'true');
    openCard = card;
  };

  cards.forEach((card) => {
    const main = card.querySelector('.work-card-main');
    main.setAttribute('aria-controls', detailRow.id);
    // The theme's image anchor is handled by the card itself on this page.
    main.querySelectorAll('a.popup').forEach((link) => link.setAttribute('tabindex', '-1'));
    // 捕获阶段拦截：封面被主题包进 a.popup（glightbox），展开逻辑必须抢先。
    main.addEventListener(
      'click',
      (event) => {
        event.preventDefault();
        event.stopPropagation();
        main.focus({ preventScroll: true });
        open(card);
      },
      true
    );
    main.addEventListener('keydown', (event) => {
      if (!event.repeat && (event.key === 'Enter' || event.key === ' ')) {
        event.preventDefault();
        open(card);
      }
    });
  });

  detailRow.addEventListener('click', (event) => {
    if (event.target.closest('.work-detail-close')) close(true);
  });

  wall.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && openCard) {
      event.preventDefault();
      event.stopPropagation();
      close(true);
    }
  });

  document.querySelectorAll('.reviews-filter button').forEach((button) => {
    button.addEventListener('click', () => {
      close();
      document
        .querySelectorAll('.reviews-filter button')
        .forEach((other) => {
          other.classList.toggle('active', other === button);
          other.setAttribute('aria-pressed', String(other === button));
        });
      const type = button.dataset.filter;
      cards.forEach((card) => {
        card.hidden = type !== 'all' && card.dataset.workType !== type;
      });
      if (emptyState) emptyState.hidden = cards.some((card) => !card.hidden);
    });
  });

  let resizeFrame;
  const reposition = () => {
    cancelAnimationFrame(resizeFrame);
    resizeFrame = requestAnimationFrame(() => {
      if (openCard) positionDetail(openCard);
    });
  };
  window.addEventListener('resize', reposition);
  if ('ResizeObserver' in window) {
    let width = wall.clientWidth;
    new ResizeObserver(() => {
      if (wall.clientWidth !== width) {
        width = wall.clientWidth;
        reposition();
      }
    }).observe(wall);
  }

  if (location.hash) {
    const target = cards.find((card) => card.dataset.workId === location.hash.slice(1));
    if (target && !target.hidden) {
      open(target);
      target.scrollIntoView({ block: 'start' });
    }
  }
})();

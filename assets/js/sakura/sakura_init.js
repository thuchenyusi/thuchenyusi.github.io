/* Initialize the pinned Sakura core without changing page overflow styles. */
(function () {
    'use strict';

    if (typeof window.Sakura !== 'function') {
        return;
    }

    new window.Sakura('body', {
        position: 'fixed',
        hideScrollbars: false
    });
})();

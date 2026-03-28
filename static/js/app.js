/**
 * Навигация: drawer (мобильная), без фреймворков
 */
(function () {
    const toggle = document.getElementById('av-nav-toggle');
    const drawer = document.getElementById('av-drawer');
    if (!toggle || !drawer) return;

    const panel = drawer.querySelector('.av-drawer__panel');
    const closers = drawer.querySelectorAll('[data-drawer-close]');

    function openDrawer() {
        drawer.classList.add('is-open');
        drawer.setAttribute('aria-hidden', 'false');
        toggle.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden';
    }

    function closeDrawer() {
        drawer.classList.remove('is-open');
        drawer.setAttribute('aria-hidden', 'true');
        toggle.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
    }

    toggle.addEventListener('click', () => {
        if (drawer.classList.contains('is-open')) {
            closeDrawer();
        } else {
            openDrawer();
        }
    });

    closers.forEach((el) => {
        el.addEventListener('click', closeDrawer);
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && drawer.classList.contains('is-open')) {
            closeDrawer();
        }
    });

    if (panel) {
        panel.addEventListener('click', (e) => e.stopPropagation());
    }
})();

/**
 * Слайдер каталога: свайп, стрелки (desktop), точки. CSS transition на track.
 */
(function () {
    const SWIPE_THRESHOLD = 48;

    function initCarousel(root) {
        const viewport = root.querySelector('.av-carousel__viewport');
        const track = root.querySelector('.av-carousel__track');
        if (!viewport || !track) return;

        const slides = track.querySelectorAll('.av-carousel__slide');
        const n = slides.length;
        if (n === 0) return;

        const prevBtn = root.querySelector('.av-carousel__arrow--prev');
        const nextBtn = root.querySelector('.av-carousel__arrow--next');
        const dotsWrap = root.querySelector('.av-carousel__dots');

        let index = 0;
        let startX = null;

        function go(i) {
            index = Math.max(0, Math.min(n - 1, i));
            track.style.transform = `translateX(-${index * 100}%)`;
            if (dotsWrap) {
                dotsWrap.querySelectorAll('.av-carousel__dot').forEach((d, j) => {
                    d.classList.toggle('is-active', j === index);
                });
            }
        }

        if (dotsWrap && n > 1) {
            dotsWrap.innerHTML = '';
            for (let j = 0; j < n; j += 1) {
                const b = document.createElement('button');
                b.type = 'button';
                b.className = 'av-carousel__dot' + (j === 0 ? ' is-active' : '');
                b.setAttribute('aria-label', `Слайд ${j + 1}`);
                b.addEventListener('click', () => go(j));
                dotsWrap.appendChild(b);
            }
        }

        if (prevBtn) {
            prevBtn.addEventListener('click', () => go(index - 1));
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', () => go(index + 1));
        }

        viewport.addEventListener(
            'touchstart',
            (e) => {
                if (e.touches.length !== 1) return;
                startX = e.touches[0].clientX;
            },
            { passive: true }
        );

        viewport.addEventListener(
            'touchend',
            (e) => {
                if (startX === null) return;
                const endX = e.changedTouches[0].clientX;
                const dx = endX - startX;
                startX = null;
                if (Math.abs(dx) < SWIPE_THRESHOLD) return;
                if (dx > 0) {
                    go(index - 1);
                } else {
                    go(index + 1);
                }
            },
            { passive: true }
        );

        go(0);
    }

    document.querySelectorAll('.av-carousel').forEach(initCarousel);

    window.AVISHU_initCarousel = initCarousel;
})();

/**
 * Витрина: модальное окно товара (AVISHU) + карусель в модалке
 */
(function () {
    const raw = document.getElementById('catalog-json');
    if (!raw) return;

    let modalI18n = { carousel_prev: 'Предыдущее фото', carousel_next: 'Следующее фото' };
    const i18nRaw = document.getElementById('client-modal-i18n');
    if (i18nRaw) {
        try {
            modalI18n = JSON.parse(i18nRaw.textContent);
        } catch (e) {
            /* keep defaults */
        }
    }

    let catalog = [];
    try {
        catalog = JSON.parse(raw.textContent);
    } catch (e) {
        return;
    }

    const modal = document.getElementById('product-modal');
    const carouselHost = document.getElementById('modal-carousel-host');
    const titleEl = document.getElementById('modal-title');
    const priceEl = document.getElementById('modal-price');
    const detailEl = document.getElementById('modal-detail');
    const preorderFields = document.getElementById('modal-preorder-fields');
    const instockActions = document.getElementById('modal-instock-actions');
    const preorderActions = document.getElementById('modal-preorder-actions');
    const cartProductName = document.getElementById('cart-product-name');
    const buyProductName = document.getElementById('buy-product-name');
    const preorderProductName = document.getElementById('preorder-product-name');
    const deadlineInput = document.getElementById('modal-deadline');

    function findProduct(id) {
        return catalog.find((p) => p.id === id);
    }

    function escapeAttr(s) {
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/</g, '&lt;');
    }

    function buildCarouselHtml(product) {
        const imgs = product.images || [];
        if (!imgs.length) return '';
        const multi = imgs.length > 1;
        const slideHtml = imgs
            .map(
                (src) =>
                    `<div class="av-carousel__slide"><img src="${escapeAttr(src)}" alt="${escapeAttr(product.name)}" loading="lazy" decoding="async"></div>`
            )
            .join('');
        const multiClass = multi ? ' av-carousel--has-multiple' : '';
        const arrows = multi
            ? `
                <button type="button" class="av-carousel__arrow av-carousel__arrow--prev" aria-label="${escapeAttr(modalI18n.carousel_prev)}">‹</button>
                <button type="button" class="av-carousel__arrow av-carousel__arrow--next" aria-label="${escapeAttr(modalI18n.carousel_next)}">›</button>
                <div class="av-carousel__dots" aria-hidden="true"></div>`
            : '';
        return `<div class="av-carousel${multiClass}" data-carousel>
            <div class="av-carousel__viewport">
                <div class="av-carousel__track">${slideHtml}</div>
            </div>${arrows}
        </div>`;
    }

    function openModal(product) {
        if (!modal || !product) return;
        if (carouselHost) {
            carouselHost.innerHTML = buildCarouselHtml(product);
            if (typeof window.AVISHU_initCarousel === 'function') {
                const c = carouselHost.querySelector('.av-carousel');
                if (c) window.AVISHU_initCarousel(c);
            }
        }

        titleEl.textContent = product.name;
        priceEl.textContent = product.price;
        detailEl.textContent = product.detail;

        const name = product.name;
        cartProductName.value = name;
        buyProductName.value = name;
        preorderProductName.value = name;

        if (product.type === 'preorder') {
            preorderFields.classList.remove('hidden');
            instockActions.classList.add('hidden');
            preorderActions.classList.remove('hidden');
            if (deadlineInput) {
                deadlineInput.required = true;
                const t = new Date();
                deadlineInput.min = t.toISOString().slice(0, 10);
            }
        } else {
            preorderFields.classList.add('hidden');
            instockActions.classList.remove('hidden');
            preorderActions.classList.add('hidden');
            if (deadlineInput) {
                deadlineInput.required = false;
                deadlineInput.value = '';
            }
        }

        modal.hidden = false;
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        if (!modal) return;
        modal.hidden = true;
        document.body.style.overflow = '';
        if (carouselHost) carouselHost.innerHTML = '';
    }

    document.querySelectorAll('[data-open-modal]').forEach((btn) => {
        btn.addEventListener('click', () => {
            const card = btn.closest('.av-product');
            if (!card) return;
            const id = card.dataset.productId;
            openModal(findProduct(id));
        });
    });

    modal.querySelectorAll('[data-close-modal]').forEach((el) => {
        el.addEventListener('click', closeModal);
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal && !modal.hidden) closeModal();
    });
})();

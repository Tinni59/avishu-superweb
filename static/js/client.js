/**
 * Витрина: модальное окно товара (AVISHU)
 */
(function () {
    const raw = document.getElementById('catalog-json');
    if (!raw) return;

    let catalog = [];
    try {
        catalog = JSON.parse(raw.textContent);
    } catch (e) {
        return;
    }

    const modal = document.getElementById('product-modal');
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

    function openModal(product) {
        if (!modal || !product) return;
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

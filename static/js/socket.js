/**
 * Flask-SocketIO: order_created / order_updated — обновление DOM без reload.
 * Сначала polling, затем upgrade на WebSocket (так надёжнее с Flask-SocketIO + threading).
 */
(function () {
    const body = document.body;
    const role = body.dataset.userRole || '';
    const userId = body.dataset.userId ? parseInt(body.dataset.userId, 10) : null;

    if (!role || typeof io === 'undefined') {
        return;
    }

    let I18N = {};
    const i18nEl = document.getElementById('av-i18n-socket');
    if (i18nEl) {
        try {
            I18N = JSON.parse(i18nEl.textContent);
        } catch (e) {
            I18N = {};
        }
    }

    function trf(key, vars) {
        let s = I18N[key] || '';
        if (!vars) return s;
        Object.keys(vars).forEach((k) => {
            s = s.split(`{${k}}`).join(String(vars[k]));
        });
        return s;
    }

    function typeLabel(t) {
        const x = t || '';
        if (x === 'in_stock') return I18N.type_in_stock || x;
        if (x === 'preorder') return I18N.type_preorder || x;
        return x;
    }

    function statusLabel(code) {
        const m = {
            created: 'status_created',
            accepted: 'status_accepted',
            in_production: 'status_in_production',
            done: 'status_done',
        };
        const k = m[code];
        return k ? I18N[k] || code : code;
    }

    const alertEl = document.getElementById('realtime-alert');
    const showAlert = (message) => {
        if (!alertEl) return;
        alertEl.textContent = message;
        alertEl.classList.remove('hidden');
        window.clearTimeout(showAlert._t);
        showAlert._t = window.setTimeout(() => alertEl.classList.add('hidden'), 4500);
    };

    const socket = io({
        path: '/socket.io',
        transports: ['polling', 'websocket'],
        upgrade: true,
        reconnection: true,
        reconnectionAttempts: 8,
        reconnectionDelay: 1000,
    });

    const fmtDate = (iso) => {
        if (!iso) return '—';
        const d = new Date(iso);
        if (Number.isNaN(d.getTime())) return '—';
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
    };

    const fmtDateTime = (iso) => {
        if (!iso) return '—';
        const d = new Date(iso);
        if (Number.isNaN(d.getTime())) return '—';
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const h = String(d.getHours()).padStart(2, '0');
        const min = String(d.getMinutes()).padStart(2, '0');
        return `${y}-${m}-${day} ${h}:${min}`;
    };

    function periodStartUtc(period) {
        const now = new Date();
        if (period === 'today') {
            return Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), 0, 0, 0, 0);
        }
        if (period === 'month') {
            return Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1, 0, 0, 0, 0);
        }
        return Date.now() - 7 * 24 * 60 * 60 * 1000;
    }

    function orderInFranchiseePeriod(order, period) {
        if (!order || !order.created_at) return false;
        const t = new Date(order.created_at).getTime();
        return t >= periodStartUtc(period);
    }

    function bumpKanban(status, delta) {
        const el = document.querySelector(`[data-kanban-count="${status}"]`);
        if (!el) return;
        const n = Math.max(0, (parseInt(el.textContent, 10) || 0) + delta);
        el.textContent = String(n);
    }

    function applyFranchiseeKanban(prev, next, order) {
        const root = document.getElementById('franchisee-kanban');
        if (!root || !order) return;
        const period = root.dataset.franchiseePeriod || 'week';
        if (!orderInFranchiseePeriod(order, period)) return;
        if (prev && next && prev !== next) {
            bumpKanban(prev, -1);
            bumpKanban(next, 1);
        }
    }

    function bumpFranchiseeKanbanNewOrder(order) {
        const root = document.getElementById('franchisee-kanban');
        if (!root || !order) return;
        const period = root.dataset.franchiseePeriod || 'week';
        if (!orderInFranchiseePeriod(order, period)) return;
        bumpKanban('created', 1);
    }

    function bumpProdStat(key, delta) {
        const el = document.querySelector(`[data-prod-stat="${key}"]`);
        if (!el) return;
        const n = Math.max(0, (parseInt(el.textContent, 10) || 0) + delta);
        el.textContent = String(n);
    }

    function moveProductionDashboardStats(prev, next) {
        if (!document.getElementById('production-stats') || !prev || !next || prev === next) return;
        if (prev === 'accepted') bumpProdStat('requested', -1);
        else if (prev === 'in_production') bumpProdStat('in_progress', -1);
        else if (prev === 'done') bumpProdStat('completed', -1);

        if (next === 'accepted') bumpProdStat('requested', 1);
        else if (next === 'in_production') bumpProdStat('in_progress', 1);
        else if (next === 'done') bumpProdStat('completed', 1);
    }

    function syncClientLoyaltyFromCount() {
        const badge = document.querySelector('[data-client-order-count]');
        const loyaltyRoot = document.getElementById('client-loyalty');
        if (!badge || !loyaltyRoot) return;
        const total = parseInt(badge.textContent, 10) || 0;
        const pct = Math.min(100, total * 12 + 8);
        const fill = document.getElementById('client-loyalty-fill');
        const labelEl = document.getElementById('client-loyalty-label');
        const bar = loyaltyRoot.querySelector('.av-loyalty__bar');
        const tpl = loyaltyRoot.dataset.loyaltyTemplate || I18N.loyalty_label_js || '';
        if (fill) fill.style.width = `${pct}%`;
        if (labelEl && tpl) labelEl.textContent = tpl.replace('{pct}', String(pct));
        if (bar) bar.setAttribute('aria-valuenow', String(pct));
        loyaltyRoot.setAttribute('data-order-total', String(total));
    }

    const FRANCHISEE_NEXT = {
        created: ['accepted'],
    };

    function franchiseeActionCell(orderId, status) {
        const next = FRANCHISEE_NEXT[status];
        if (!next || !next.length) {
            return `<span class="av-muted">${I18N.fr_no_action || '—'}</span>`;
        }
        const buttons = next
            .map(
                (s) => {
                    const lab = s === 'accepted' ? I18N.fr_btn_accept || s : s;
                    return `<button type="submit" name="status" value="${s}" class="av-btn av-btn--sm">${lab}</button>`;
                }
            )
            .join('');
        return `<form method="post" action="/franchisee/orders/${orderId}/status" class="inline-form">${buttons}</form>`;
    }

    function franchiseeActionCard(orderId, status) {
        const next = FRANCHISEE_NEXT[status];
        if (!next || !next.length) {
            return `<span class="av-muted">${I18N.fr_no_action || '—'}</span>`;
        }
        const label = (s) => {
            if (s === 'accepted') return I18N.fr_btn_accept || String(s);
            return String(s);
        };
        const buttons = next
            .map(
                (s) =>
                    `<button type="submit" name="status" value="${s}" class="av-btn av-btn--accept av-btn--inverse av-btn--block">${label(s)}</button>`
            )
            .join('');
        return `<form method="post" action="/franchisee/orders/${orderId}/status" class="inline-form">${buttons}</form>`;
    }

    function productionActionsHtml(orderId, status) {
        const st = status || '';
        const inProgDisabled = st === 'in_production' ? ' disabled aria-disabled="true"' : '';
        const doneDisabled = st !== 'in_production' ? ' disabled aria-disabled="true"' : '';
        const labProg = I18N.pq_btn_progress || 'В процессе';
        const labDone = I18N.pq_btn_finish || 'Завершить';
        return `<div class="av-prod-actions">
            <form method="post" action="/production/orders/${orderId}/status" class="av-prod-actions__form">
                <input type="hidden" name="status" value="in_production">
                <button type="submit" class="av-btn av-btn--prod-twin"${inProgDisabled}>${labProg}</button>
            </form>
            <form method="post" action="/production/orders/${orderId}/status" class="av-prod-actions__form">
                <input type="hidden" name="status" value="done">
                <button type="submit" class="av-btn av-btn--prod-twin av-btn--finish"${doneDisabled}>${labDone}</button>
            </form>
        </div>`;
    }

    function productionCardHtml(order) {
        const stLab = I18N.pq_status || 'Статус:';
        const dueLab = I18N.pq_due || 'срок';
        return `
            <div class="av-queue__card av-queue__card--dark" data-order-id="${order.id}">
                <div class="av-queue__card-main">
                    <p class="av-queue__id av-queue__id--muted">#${order.id}</p>
                    <p class="av-queue__title av-queue__title--light">${escapeHtml(order.product_name)}</p>
                    <p class="av-muted av-queue__meta">${escapeHtml(typeLabel(order.type))} · ${dueLab} ${fmtDate(order.deadline)}</p>
                    <p class="av-queue__id av-queue__id--muted" style="margin-top:0.5rem;">${stLab} <span class="js-order-status">${escapeHtml(statusLabel(order.status))}</span></p>
                </div>
                <div class="av-queue__actions js-production-actions">${productionActionsHtml(order.id, order.status)}</div>
            </div>`;
    }

    function ensureClientTable() {
        const wrap = document.getElementById('client-orders-table-wrap');
        if (!wrap) return null;
        let tbody = document.getElementById('client-orders-tbody');
        if (tbody) return tbody;
        const empty = wrap.querySelector('.empty-state');
        if (empty) empty.remove();
        wrap.innerHTML = `
            <div class="av-order-cards" id="client-order-cards"></div>
            <div class="av-table-wrap av-table-desktop">
                <table class="av-table">
                    <thead>
                        <tr>
                            <th>${I18N.table_id || 'ID'}</th>
                            <th>${I18N.table_product || ''}</th>
                            <th>${I18N.table_type || ''}</th>
                            <th>${I18N.table_status || ''}</th>
                            <th>${I18N.table_deadline || ''}</th>
                            <th>${I18N.table_created || ''}</th>
                        </tr>
                    </thead>
                    <tbody id="client-orders-tbody"></tbody>
                </table>
            </div>`;
        return document.getElementById('client-orders-tbody');
    }

    function upsertClientCard(order) {
        if (userId !== order.user_id) return;
        let container = document.getElementById('client-order-cards');
        if (!container) {
            ensureClientTable();
            container = document.getElementById('client-order-cards');
        }
        if (!container) return;

        let card = container.querySelector(`[data-order-id="${order.id}"]`);
        if (!card) {
            card = document.createElement('article');
            card.className = 'av-order-card';
            card.dataset.orderId = String(order.id);
            container.insertBefore(card, container.firstChild);
            const tbody = document.getElementById('client-orders-tbody');
            if (!tbody || !tbody.querySelector(`tr[data-order-id="${order.id}"]`)) {
                bumpClientCount(1);
            }
        }
        card.innerHTML = `
            <div class="av-order-card__top">
                <span class="av-order-card__id">#${order.id}</span>
                <span class="av-badge status">${escapeHtml(statusLabel(order.status))}</span>
            </div>
            <h3 class="av-order-card__title">${escapeHtml(order.product_name)}</h3>
            <p class="av-order-card__meta">${escapeHtml(typeLabel(order.type))} · ${fmtDate(order.deadline)}</p>
            <p class="av-order-card__meta">${fmtDateTime(order.created_at)}</p>`;
    }

    function bumpClientCount(delta) {
        const badge = document.querySelector('[data-client-order-count]');
        if (!badge) return;
        const n = parseInt(badge.textContent, 10) || 0;
        badge.textContent = String(Math.max(0, n + delta));
    }

    function upsertClientRow(order) {
        if (userId !== order.user_id) return;
        upsertClientCard(order);
        let tbody = document.getElementById('client-orders-tbody');
        if (!tbody) tbody = ensureClientTable();
        if (!tbody) return;

        let row = tbody.querySelector(`tr[data-order-id="${order.id}"]`);
        if (!row) {
            row = document.createElement('tr');
            row.dataset.orderId = String(order.id);
            tbody.insertBefore(row, tbody.firstChild);
        }
        row.innerHTML = `
            <td>#${order.id}</td>
            <td>${escapeHtml(order.product_name)}</td>
            <td>${escapeHtml(typeLabel(order.type))}</td>
            <td class="status">${escapeHtml(statusLabel(order.status))}</td>
            <td>${fmtDate(order.deadline)}</td>
            <td>${fmtDateTime(order.created_at)}</td>`;
    }

    function escapeHtml(s) {
        const div = document.createElement('div');
        div.textContent = s == null ? '' : String(s);
        return div.innerHTML;
    }

    function updateClientTrack(order) {
        const track = document.getElementById('client-order-track');
        if (!track || parseInt(track.dataset.orderId, 10) !== order.id) return;
        const steps = track.querySelectorAll('.av-step');
        if (steps.length < 3) return;
        steps[0].classList.add('av-step--on');
        if (['accepted', 'in_production', 'done'].includes(order.status)) {
            steps[1].classList.add('av-step--on');
        } else {
            steps[1].classList.remove('av-step--on');
        }
        if (order.status === 'done') {
            steps[2].classList.add('av-step--on');
        } else {
            steps[2].classList.remove('av-step--on');
        }
    }

    function ensureFranchiseeTable() {
        const wrap = document.getElementById('franchisee-orders-wrap');
        if (!wrap) return null;
        let tbody = document.getElementById('franchisee-orders-tbody');
        if (tbody) return tbody;
        const empty = wrap.querySelector('.empty-state');
        if (empty) empty.remove();
        wrap.innerHTML = `
            <div class="av-order-cards" id="franchisee-order-cards"></div>
            <div class="av-table-wrap av-table-desktop">
                <table class="av-table">
                    <thead>
                        <tr>
                            <th>${I18N.table_id || 'ID'}</th>
                            <th>${I18N.fr_table_client || ''}</th>
                            <th>${I18N.table_product || ''}</th>
                            <th>${I18N.table_type || ''}</th>
                            <th>${I18N.table_status || ''}</th>
                            <th>${I18N.table_deadline || ''}</th>
                            <th>${I18N.table_created || ''}</th>
                            <th>${I18N.fr_table_action || ''}</th>
                        </tr>
                    </thead>
                    <tbody id="franchisee-orders-tbody"></tbody>
                </table>
            </div>`;
        return document.getElementById('franchisee-orders-tbody');
    }

    function upsertFranchiseeCard(order) {
        let container = document.getElementById('franchisee-order-cards');
        if (!container) {
            ensureFranchiseeTable();
            container = document.getElementById('franchisee-order-cards');
        }
        if (!container) return;
        const email = order.client_email || '—';
        let card = container.querySelector(`[data-order-id="${order.id}"]`);
        if (!card) {
            card = document.createElement('article');
            card.className = 'av-order-card av-order-card--fr';
            card.dataset.orderId = String(order.id);
            container.insertBefore(card, container.firstChild);
            const badge = document.querySelector('[data-franchisee-order-count]');
            if (badge) {
                const n = parseInt(badge.textContent, 10) || 0;
                badge.textContent = String(n + 1);
            }
        }
        card.innerHTML = `
            <p class="av-order-card__id">#${order.id} · ${escapeHtml(email)}</p>
            <h3 class="av-order-card__title">${escapeHtml(order.product_name)}</h3>
            <div class="av-order-card__top">
                <span class="av-muted">${escapeHtml(order.type)}</span>
                <span class="av-badge js-order-status">${escapeHtml(order.status)}</span>
            </div>
            <p class="av-order-card__meta">${fmtDate(order.deadline)} · ${fmtDateTime(order.created_at)}</p>
            <div class="av-order-card__actions js-franchisee-actions">${franchiseeActionCard(order.id, order.status)}</div>`;
    }

    function upsertFranchiseeRow(order) {
        upsertFranchiseeCard(order);
        let tbody = document.getElementById('franchisee-orders-tbody');
        if (!tbody) tbody = ensureFranchiseeTable();
        if (!tbody) return;
        const email = order.client_email || '—';
        let row = tbody.querySelector(`tr[data-order-id="${order.id}"]`);
        if (!row) {
            row = document.createElement('tr');
            row.dataset.orderId = String(order.id);
            tbody.insertBefore(row, tbody.firstChild);
        }
        row.innerHTML = `
            <td>#${order.id}</td>
            <td>${escapeHtml(email)}</td>
            <td>${escapeHtml(order.product_name)}</td>
            <td>${escapeHtml(order.type)}</td>
            <td class="js-order-status">${escapeHtml(order.status)}</td>
            <td>${fmtDate(order.deadline)}</td>
            <td>${fmtDateTime(order.created_at)}</td>
            <td class="js-franchisee-actions">${franchiseeActionCell(order.id, order.status)}</td>`;
    }

    function removeProductionActiveRow(orderId) {
        const card = document.querySelector(`#production-active-wrap .av-queue [data-order-id="${orderId}"]`);
        if (card) card.remove();
        const badge = document.querySelector('[data-production-active-count]');
        if (badge) {
            const rest = document.querySelectorAll('#production-active-wrap .av-queue [data-order-id]').length;
            badge.textContent = String(rest);
        }
    }

    function appendProductionDone(order) {
        const list = document.getElementById('production-done-list');
        if (!list) return;
        const empty = list.querySelector('.empty-state');
        if (empty) {
            empty.remove();
        }
        const email = order.client_email || '—';
        const li = document.createElement('li');
        li.dataset.orderId = String(order.id);
        li.innerHTML = `
            <div>
                <strong style="letter-spacing:0.08em;text-transform:uppercase;font-size:0.85rem;">#${order.id} — ${escapeHtml(order.product_name)}</strong>
                <p class="av-muted" style="margin:0.35rem 0 0;">${escapeHtml(email)}</p>
            </div>
            <span class="av-badge">${I18N.pq_badge_done || 'Завершён'}</span>`;
        list.insertBefore(li, list.firstChild);
        const badge = document.querySelector('[data-production-done-count]');
        if (badge) {
            const n = parseInt(badge.textContent, 10) || 0;
            badge.textContent = String(n + 1);
        }
    }

    function ensureProductionQueue() {
        const wrap = document.getElementById('production-active-wrap');
        if (!wrap) return null;
        let queue = wrap.querySelector('.av-queue');
        if (queue) return queue;
        const empty = wrap.querySelector('.empty-state, .av-muted');
        if (empty) empty.remove();
        wrap.innerHTML = '<div class="av-queue" id="production-active-queue"></div>';
        const badge = document.querySelector('[data-production-active-count]');
        if (badge) badge.textContent = '0';
        return document.getElementById('production-active-queue');
    }

    function upsertProductionActiveRow(order) {
        if (order.status !== 'accepted' && order.status !== 'in_production') return;

        let queue = document.getElementById('production-active-queue');
        if (!queue) queue = ensureProductionQueue();
        if (!queue) return;

        let card = queue.querySelector(`[data-order-id="${order.id}"]`);
        if (!card) {
            const div = document.createElement('div');
            div.innerHTML = productionCardHtml(order).trim();
            queue.insertBefore(div.firstElementChild, queue.firstChild);
            const badge = document.querySelector('[data-production-active-count]');
            if (badge) {
                const n = parseInt(badge.textContent, 10) || 0;
                badge.textContent = String(n + 1);
            }
            return;
        }
        card.outerHTML = productionCardHtml(order);
    }

    function updateOrderRowStatus(order) {
        const row = document.querySelector(`tr[data-order-id="${order.id}"]`);
        if (row) {
            const cell = row.querySelector('.status, .js-order-status');
            if (cell) cell.textContent = statusLabel(order.status);
            const fa = row.querySelector('.js-franchisee-actions');
            if (fa) fa.innerHTML = franchiseeActionCell(order.id, order.status);
        }
        const frCard = document.querySelector(`#franchisee-order-cards [data-order-id="${order.id}"]`);
        if (frCard) {
            const st = frCard.querySelector('.js-order-status');
            if (st) st.textContent = order.status;
            const fa = frCard.querySelector('.js-franchisee-actions');
            if (fa) fa.innerHTML = franchiseeActionCard(order.id, order.status);
        }
        const card = document.querySelector(`#production-active-wrap .av-queue [data-order-id="${order.id}"]`);
        if (card) {
            const st = card.querySelector('.js-order-status');
            if (st) st.textContent = statusLabel(order.status);
            const pa = card.querySelector('.js-production-actions');
            if (pa) pa.innerHTML = productionActionsHtml(order.id, order.status);
        }
    }

    socket.on('connect', () => {
        showAlert(I18N.js_alert_connected || '');
    });

    socket.on('disconnect', () => {
        showAlert(I18N.js_alert_disconnected || '');
    });

    socket.on('connect_error', () => {
        showAlert(I18N.js_alert_connect_error || '');
    });

    socket.on('order_created', (payload) => {
        const order = payload && payload.order;
        if (!order) return;

        if (role === 'client' && userId === order.user_id) {
            upsertClientRow(order);
            syncClientLoyaltyFromCount();
            showAlert(trf('js_alert_order_created', { id: order.id }));
            return;
        }

        if (role === 'franchisee') {
            upsertFranchiseeRow(order);
            bumpFranchiseeKanbanNewOrder(order);
            showAlert(trf('js_alert_new_order', { id: order.id }));
            return;
        }

        if (role === 'production') {
            showAlert(trf('js_alert_new_order_prod', { id: order.id }));
        }
    });

    socket.on('order_updated', (payload) => {
        const order = payload && payload.order;
        if (!order) return;
        const prev = payload.previous_status;

        if (role === 'client' && userId === order.user_id) {
            upsertClientRow(order);
            updateClientTrack(order);
            syncClientLoyaltyFromCount();
            showAlert(
                trf('js_alert_order_status', {
                    id: order.id,
                    status: statusLabel(order.status),
                })
            );
            return;
        }

        if (role === 'franchisee') {
            upsertFranchiseeRow(order);
            if (prev) {
                applyFranchiseeKanban(prev, order.status, order);
            }
            showAlert(
                trf('js_alert_order_status', {
                    id: order.id,
                    status: order.status,
                })
            );
            return;
        }

        if (role === 'production') {
            if (prev) {
                moveProductionDashboardStats(prev, order.status);
            }
            if (order.status === 'done') {
                removeProductionActiveRow(order.id);
                appendProductionDone(order);
                showAlert(trf('js_alert_order_done', { id: order.id }));
                return;
            }
            if (order.status === 'accepted') {
                upsertProductionActiveRow(order);
                showAlert(trf('js_alert_order_accepted_prod', { id: order.id }));
                return;
            }
            upsertProductionActiveRow(order);
            updateOrderRowStatus(order);
            showAlert(
                trf('js_alert_order_status', {
                    id: order.id,
                    status: statusLabel(order.status),
                })
            );
        }
    });
})();

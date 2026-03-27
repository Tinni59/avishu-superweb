/**
 * Flask-SocketIO: order_created / order_updated — обновление DOM без reload.
 * Транспорт: только WebSocket (без polling).
 */
(function () {
    const body = document.body;
    const role = body.dataset.userRole || '';
    const userId = body.dataset.userId ? parseInt(body.dataset.userId, 10) : null;

    if (!role || typeof io === 'undefined') {
        return;
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
        transports: ['websocket'],
        upgrade: false,
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

    const FRANCHISEE_NEXT = {
        created: ['accepted'],
        accepted: ['in_production'],
    };

    const PRODUCTION_NEXT = {
        accepted: ['done'],
        in_production: ['done'],
    };

    function franchiseeActionCell(orderId, status) {
        const next = FRANCHISEE_NEXT[status];
        if (!next || !next.length) {
            return '<span class="muted">—</span>';
        }
        const buttons = next
            .map(
                (s) =>
                    `<button type="submit" name="status" value="${s}" class="small-btn">${s}</button>`
            )
            .join('');
        return `<form method="post" action="/franchisee/orders/${orderId}/status" class="inline-form">${buttons}</form>`;
    }

    function productionActionCell(orderId, status) {
        const next = PRODUCTION_NEXT[status];
        if (!next || !next.length) {
            return '<span class="muted">—</span>';
        }
        const buttons = next
            .map(
                (s) =>
                    `<button type="submit" name="status" value="${s}" class="small-btn">${s}</button>`
            )
            .join('');
        return `<form method="post" action="/production/orders/${orderId}/status" class="inline-form">${buttons}</form>`;
    }

    function ensureClientTable() {
        const wrap = document.getElementById('client-orders-table-wrap');
        if (!wrap) return null;
        let tbody = document.getElementById('client-orders-tbody');
        if (tbody) return tbody;
        const empty = wrap.querySelector('.empty-state');
        if (empty) empty.remove();
        wrap.innerHTML = `
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Продукт</th>
                            <th>Тип</th>
                            <th>Статус</th>
                            <th>Дедлайн</th>
                            <th>Создан</th>
                        </tr>
                    </thead>
                    <tbody id="client-orders-tbody"></tbody>
                </table>
            </div>`;
        const badge = document.querySelector('[data-client-order-count]');
        if (badge) badge.textContent = '0';
        return document.getElementById('client-orders-tbody');
    }

    function bumpClientCount(delta) {
        const badge = document.querySelector('[data-client-order-count]');
        if (!badge) return;
        const n = parseInt(badge.textContent, 10) || 0;
        badge.textContent = String(Math.max(0, n + delta));
    }

    function upsertClientRow(order) {
        if (userId !== order.user_id) return;
        let tbody = document.getElementById('client-orders-tbody');
        if (!tbody) tbody = ensureClientTable();
        if (!tbody) return;

        let row = tbody.querySelector(`tr[data-order-id="${order.id}"]`);
        if (!row) {
            row = document.createElement('tr');
            row.dataset.orderId = String(order.id);
            tbody.insertBefore(row, tbody.firstChild);
            bumpClientCount(1);
        }
        row.innerHTML = `
            <td>#${order.id}</td>
            <td>${escapeHtml(order.product_name)}</td>
            <td>${escapeHtml(order.type)}</td>
            <td class="status">${escapeHtml(order.status)}</td>
            <td>${fmtDate(order.deadline)}</td>
            <td>${fmtDateTime(order.created_at)}</td>`;
    }

    function escapeHtml(s) {
        const div = document.createElement('div');
        div.textContent = s == null ? '' : String(s);
        return div.innerHTML;
    }

    function ensureFranchiseeTable() {
        const wrap = document.getElementById('franchisee-orders-wrap');
        if (!wrap) return null;
        let tbody = document.getElementById('franchisee-orders-tbody');
        if (tbody) return tbody;
        const empty = wrap.querySelector('.empty-state');
        if (empty) empty.remove();
        wrap.innerHTML = `
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Клиент</th>
                            <th>Продукт</th>
                            <th>Тип</th>
                            <th>Статус</th>
                            <th>Дедлайн</th>
                            <th>Создан</th>
                            <th>Действие</th>
                        </tr>
                    </thead>
                    <tbody id="franchisee-orders-tbody"></tbody>
                </table>
            </div>`;
        const badge = document.querySelector('[data-franchisee-order-count]');
        if (badge) badge.textContent = '0';
        return document.getElementById('franchisee-orders-tbody');
    }

    function upsertFranchiseeRow(order) {
        let tbody = document.getElementById('franchisee-orders-tbody');
        if (!tbody) tbody = ensureFranchiseeTable();
        if (!tbody) return;
        const email = order.client_email || '—';
        let row = tbody.querySelector(`tr[data-order-id="${order.id}"]`);
        if (!row) {
            row = document.createElement('tr');
            row.dataset.orderId = String(order.id);
            tbody.insertBefore(row, tbody.firstChild);
            const badge = document.querySelector('[data-franchisee-order-count]');
            if (badge) {
                const n = parseInt(badge.textContent, 10) || 0;
                badge.textContent = String(n + 1);
            }
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
        const row = document.querySelector(`#production-active-tbody tr[data-order-id="${orderId}"]`);
        if (row) row.remove();
        const badge = document.querySelector('[data-production-active-count]');
        if (badge) {
            const rest = document.querySelectorAll('#production-active-tbody tr[data-order-id]').length;
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
        li.className = 'list-card';
        li.dataset.orderId = String(order.id);
        li.innerHTML = `
            <div>
                <strong>#${order.id} — ${escapeHtml(order.product_name)}</strong>
                <p class="muted">Клиент: ${escapeHtml(email)}</p>
            </div>
            <span class="badge">done</span>`;
        list.insertBefore(li, list.firstChild);
        const badge = document.querySelector('[data-production-done-count]');
        if (badge) {
            const n = parseInt(badge.textContent, 10) || 0;
            badge.textContent = String(n + 1);
        }
    }

    function ensureProductionActiveTable() {
        const wrap = document.getElementById('production-active-wrap');
        if (!wrap) return null;
        let tbody = document.getElementById('production-active-tbody');
        if (tbody) return tbody;
        const empty = wrap.querySelector('.empty-state');
        if (empty) empty.remove();
        wrap.innerHTML = `
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Продукт</th>
                            <th>Тип</th>
                            <th>Статус</th>
                            <th>Срок</th>
                            <th>Действие</th>
                        </tr>
                    </thead>
                    <tbody id="production-active-tbody"></tbody>
                </table>
            </div>`;
        const badge = document.querySelector('[data-production-active-count]');
        if (badge) badge.textContent = '0';
        return document.getElementById('production-active-tbody');
    }

    function upsertProductionActiveRow(order) {
        if (order.status !== 'accepted' && order.status !== 'in_production') return;

        let tbody = document.getElementById('production-active-tbody');
        if (!tbody) tbody = ensureProductionActiveTable();
        if (!tbody) return;

        let row = tbody.querySelector(`tr[data-order-id="${order.id}"]`);
        if (!row) {
            row = document.createElement('tr');
            row.dataset.orderId = String(order.id);
            tbody.insertBefore(row, tbody.firstChild);
            const badge = document.querySelector('[data-production-active-count]');
            if (badge) {
                const n = parseInt(badge.textContent, 10) || 0;
                badge.textContent = String(n + 1);
            }
        }
        row.innerHTML = `
            <td>#${order.id}</td>
            <td>${escapeHtml(order.product_name)}</td>
            <td>${escapeHtml(order.type)}</td>
            <td class="js-order-status">${escapeHtml(order.status)}</td>
            <td>${fmtDate(order.deadline)}</td>
            <td class="js-production-actions">${productionActionCell(order.id, order.status)}</td>`;
    }

    function updateOrderRowStatus(order) {
        const row = document.querySelector(`tr[data-order-id="${order.id}"]`);
        if (!row) return;
        const cell = row.querySelector('.status, .js-order-status');
        if (cell) cell.textContent = order.status;

        const fa = row.querySelector('.js-franchisee-actions');
        if (fa) {
            fa.innerHTML = franchiseeActionCell(order.id, order.status);
        }
        const pa = row.querySelector('.js-production-actions');
        if (pa) {
            pa.innerHTML = productionActionCell(order.id, order.status);
        }
    }

    socket.on('connect', () => {
        showAlert('Realtime: подключено (WebSocket)');
    });

    socket.on('disconnect', () => {
        showAlert('Realtime: соединение разорвано');
    });

    socket.on('connect_error', () => {
        showAlert('Realtime: ошибка подключения');
    });

    socket.on('order_created', (payload) => {
        const order = payload && payload.order;
        if (!order) return;

        if (role === 'client' && userId === order.user_id) {
            upsertClientRow(order);
            showAlert(`Заказ #${order.id} создан`);
            return;
        }

        if (role === 'franchisee') {
            upsertFranchiseeRow(order);
            showAlert(`Новый заказ #${order.id}`);
            return;
        }

        if (role === 'production') {
            showAlert(`Новый заказ #${order.id} (ожидайте статус accepted)`);
        }
    });

    socket.on('order_updated', (payload) => {
        const order = payload && payload.order;
        if (!order) return;

        if (role === 'client' && userId === order.user_id) {
            upsertClientRow(order);
            showAlert(`Заказ #${order.id}: ${order.status}`);
            return;
        }

        if (role === 'franchisee') {
            upsertFranchiseeRow(order);
            showAlert(`Заказ #${order.id}: ${order.status}`);
            return;
        }

        if (role === 'production') {
            if (order.status === 'done') {
                removeProductionActiveRow(order.id);
                appendProductionDone(order);
                showAlert(`Заказ #${order.id} завершён`);
                return;
            }
            if (order.status === 'accepted') {
                upsertProductionActiveRow(order);
                showAlert(`Заказ #${order.id} принят в производство`);
                return;
            }
            upsertProductionActiveRow(order);
            updateOrderRowStatus(order);
            showAlert(`Заказ #${order.id}: ${order.status}`);
        }
    });
})();

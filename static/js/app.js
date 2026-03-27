(() => {
    const role = document.body.dataset.userRole;
    const alertNode = document.getElementById('realtime-alert');
    const liveLog = document.getElementById('live-log');

    if (!role || typeof io === 'undefined') {
        return;
    }

    const socket = io();

    const showAlert = (message) => {
        if (!alertNode) {
            return;
        }
        alertNode.textContent = message;
        alertNode.classList.remove('hidden');
        window.clearTimeout(showAlert.timer);
        showAlert.timer = window.setTimeout(() => {
            alertNode.classList.add('hidden');
        }, 4000);
    };

    const appendLog = (message) => {
        if (!liveLog) {
            return;
        }
        const entry = document.createElement('div');
        entry.textContent = message;
        liveLog.prepend(entry);
    };

    const updateOrderRow = (order) => {
        const row = document.querySelector(`[data-order-id="${order.id}"]`);
        if (!row) {
            return;
        }
        const statusCell = row.querySelector('.status, .js-order-status');
        if (statusCell) {
            statusCell.textContent = order.status;
        }
    };

    socket.on('connect', () => {
        socket.emit('ping_server', { role });
    });

    socket.on('connected', (payload) => {
        showAlert(`Realtime connected for role: ${payload.role}`);
    });

    socket.on('pong_server', (payload) => {
        appendLog(`Socket handshake complete: ${payload.message}`);
    });

    socket.on('order_created', (payload) => {
        const { order } = payload;
        showAlert(`Новый заказ #${order.id}: ${order.product_name}`);
        appendLog(`Order #${order.id} created with status ${order.status}`);
    });

    socket.on('order_updated', (payload) => {
        const { order } = payload;
        showAlert(`Заказ #${order.id} обновлен: ${order.status}`);
        appendLog(`Order #${order.id} changed to ${order.status}`);
        updateOrderRow(order);
    });
})();

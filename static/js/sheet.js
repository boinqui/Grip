window.SheetModal = {
    showFieldError(id, message) {
        const el = document.getElementById(id);
        if (!el) return;
        el.textContent = message;
        el.classList.add('visivel');
    },
    clearFieldError(id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.textContent = '';
        el.classList.remove('visivel');
    },
    showMessage() { return Promise.resolve(false); },
    showConfirm() { return Promise.resolve(false); },
    close() {},
};

(function () {
    const modal = document.getElementById('globalModal');
    if (!modal) {
        return;
    }

    const statusContainer = document.getElementById('modalStatusContainer');
    const icon = document.getElementById('modalIcon');
    const title = document.getElementById('modalTitle');
    const description = document.getElementById('modalDescription');
    const closeButton = document.getElementById('modalCloseButton');
    const cancelButton = document.getElementById('modalCancelButton');
    const actionButton = document.getElementById('modalActionButton');

    let resolver = null;

    const setStatus = (type) => {
        statusContainer.classList.remove('msg-info', 'msg-warning', 'msg-error');
        if (type === 'error') {
            statusContainer.classList.add('msg-error');
            icon.textContent = '!';
            return;
        }
        if (type === 'warning') {
            statusContainer.classList.add('msg-warning');
            icon.textContent = '!';
            return;
        }
        statusContainer.classList.add('msg-info');
        icon.textContent = '✓';
    };

    const closeModal = (result = false) => {
        modal.classList.remove('aberto');
        setTimeout(() => {
            if (modal.dataset.autoOpen !== 'true') {
                modal.style.display = 'none';
            }
        }, 300);

        if (resolver) {
            const resolve = resolver;
            resolver = null;
            resolve(result);
        }
    };

    const openModal = ({
        type = 'info',
        modalTitle = 'Aviso',
        message = '',
        confirmText = 'Entendi',
        cancelText = null,
    }) => {
        setStatus(type);
        title.textContent = modalTitle;
        description.textContent = message;
        actionButton.textContent = confirmText;

        if (cancelText) {
            cancelButton.style.display = 'block';
            cancelButton.textContent = cancelText;
        } else {
            cancelButton.style.display = 'none';
        }

        modal.dataset.autoOpen = 'false';
        modal.style.display = 'flex';
        requestAnimationFrame(() => {
            modal.classList.add('aberto');
        });
    };

    closeButton.addEventListener('click', () => closeModal(false));
    cancelButton.addEventListener('click', () => closeModal(false));
    actionButton.addEventListener('click', () => closeModal(true));
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeModal(false);
        }
    });

    window.SheetModal = {
        showMessage({
            type = 'info',
            title: modalTitle = 'Aviso',
            message = '',
            buttonText = 'Entendi',
        }) {
            openModal({
                type,
                modalTitle,
                message,
                confirmText: buttonText,
                cancelText: null,
            });
            return new Promise((resolve) => {
                resolver = resolve;
            });
        },

        showConfirm({
            type = 'warning',
            title: modalTitle = 'Confirmar ação',
            message = '',
            confirmText = 'Confirmar',
            cancelText = 'Cancelar',
        }) {
            openModal({
                type,
                modalTitle,
                message,
                confirmText,
                cancelText,
            });
            return new Promise((resolve) => {
                resolver = resolve;
            });
        },

        close() {
            closeModal(false);
        },
    };

    if (modal.dataset.autoOpen === 'true') {
        cancelButton.style.display = 'none';
    } else {
        modal.style.display = 'none';
    }
})();

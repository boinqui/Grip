document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (!loginForm) {
        return;
    }

    const mostrarErro = (mensagem) => {
        if (window.SheetModal) {
            window.SheetModal.showMessage({
                type: 'error',
                title: 'Erro',
                message: mensagem,
            });
        }
    };

    const validarPattern = (input) => {
        const pattern = input.getAttribute('pattern');
        if (!pattern) {
            return true;
        }
        const source = pattern.startsWith('^') && pattern.endsWith('$')
            ? pattern
            : `^(?:${pattern})$`;
        const regex = new RegExp(source);
        return regex.test(input.value.trim());
    };

    loginForm.addEventListener('submit', (e) => {
        const emailInput = document.getElementById('email');
        const senhaInput = document.getElementById('senha');

        if (!emailInput || !emailInput.value.trim()) {
            e.preventDefault();
            mostrarErro('Informe seu email.');
            return;
        }

        if (!validarPattern(emailInput)) {
            e.preventDefault();
            mostrarErro('Informe um email válido.');
            return;
        }

        if (!senhaInput || !senhaInput.value.trim()) {
            e.preventDefault();
            mostrarErro('Informe sua senha.');
        }
    });

    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('focus', () => {
            input.parentElement.style.transform = 'translateY(-2px)';
            input.parentElement.style.transition = 'transform 0.3s ease';
        });

        input.addEventListener('blur', () => {
            input.parentElement.style.transform = 'translateY(0)';
        });
    });
});

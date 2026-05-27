document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (!loginForm) {
        return;
    }

    const mostrarErro = (id, mensagem) => {
        if (window.SheetModal) window.SheetModal.showFieldError(id, mensagem);
    };
    const limparErro = (id) => {
        if (window.SheetModal) window.SheetModal.clearFieldError(id);
    };

    const validarPattern = (input) => {
        const pattern = input.getAttribute('pattern');
        if (!pattern) return true;
        const source = pattern.startsWith('^') && pattern.endsWith('$') ? pattern : `^(?:${pattern})$`;
        return new RegExp(source).test(input.value.trim());
    };

    loginForm.addEventListener('submit', (e) => {
        const emailInput = document.getElementById('email');
        const senhaInput = document.getElementById('senha');

        ['erro-email', 'erro-senha'].forEach(limparErro);

        let valido = true;

        if (!emailInput || !emailInput.value.trim()) {
            mostrarErro('erro-email', 'Informe seu email.'); valido = false;
        } else if (!validarPattern(emailInput)) {
            mostrarErro('erro-email', 'Informe um email válido.'); valido = false;
        }

        if (!senhaInput || !senhaInput.value.trim()) {
            mostrarErro('erro-senha', 'Informe sua senha.'); valido = false;
        }

        if (!valido) e.preventDefault();
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

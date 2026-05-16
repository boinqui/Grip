document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (!loginForm) {
        return;
    }

    function mostrarErro(id, msg) {
        const el = document.getElementById(id);
        if (!el) return;
        el.textContent = msg;
        el.classList.add('visivel');
    }

    function limparErro(id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.textContent = '';
        el.classList.remove('visivel');
    }

    loginForm.addEventListener('submit', (e) => {
        let valido = true;
        const email = document.getElementById('email');
        const senha = document.getElementById('senha');

        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) {
            mostrarErro('erro-email', 'Informe um e-mail válido.');
            valido = false;
        } else { limparErro('erro-email'); }

        if (!senha || senha.value.trim() === '') {
            mostrarErro('erro-senha', 'Informe sua senha.');
            valido = false;
        } else { limparErro('erro-senha'); }

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
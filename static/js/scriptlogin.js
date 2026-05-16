document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (!loginForm) {
        return;
    }

    loginForm.addEventListener('submit', (e) => {
        const emailInput = document.getElementById('email');
        const email = emailInput ? emailInput.value : '';
        if (!email.includes('@')) {
            e.preventDefault();
            if (window.SheetModal) {
                window.SheetModal.showMessage({
                    type: 'error',
                    title: 'Erro',
                    message: 'Por favor, insira um email válido.',
                });
            }
            return;
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
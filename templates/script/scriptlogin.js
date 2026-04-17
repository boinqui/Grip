document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');

    loginForm.addEventListener('submit', (e) => {
        const email = document.getElementById('email').value;
        const senha = document.getElementById('senha').value;

        // Validação básica apenas para exemplo no console
        if (!email.includes('@')) {
            e.preventDefault();
            alert('Por favor, insira um email válido.');
            return;
        }

        console.log('Tentativa de login enviada para:', email);
    });

    // Animação sutil ao focar nos inputs
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
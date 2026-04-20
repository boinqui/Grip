document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('cadastroForm');
    const senha = document.getElementById('senha');
    const confirmarSenha = document.getElementById('confirmar_senha');

    form.addEventListener('submit', (e) => {
        if (senha.value !== confirmarSenha.value) {
            e.preventDefault();
            alert('As senhas não coincidem!');
            return;
        }

        if (senha.value.length < 8) {
            e.preventDefault();
            alert('A senha deve ter pelo menos 8 caracteres.');
            return;
        }

        console.log('Formulário enviado com sucesso!');
    });

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            if (this.getAttribute('href') !== '#') {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});
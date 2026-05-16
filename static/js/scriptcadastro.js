document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('cadastroForm');
    if (!form) {
        return;
    }

    const senha = document.getElementById('senha');
    const confirmarSenha = document.getElementById('confirmar_senha');
    const telefone = document.getElementById('telefone');
    const cpf = document.getElementById('cpf');

    const formatarCpf = (valor) => {
        const digitos = valor.replace(/\D/g, '').slice(0, 11);

        if (digitos.length <= 3) return digitos;
        if (digitos.length <= 6) return `${digitos.slice(0, 3)}.${digitos.slice(3)}`;
        if (digitos.length <= 9) return `${digitos.slice(0, 3)}.${digitos.slice(3, 6)}.${digitos.slice(6)}`;
        return `${digitos.slice(0, 3)}.${digitos.slice(3, 6)}.${digitos.slice(6, 9)}-${digitos.slice(9, 11)}`;
    };

    const formatarTelefone = (valor) => {
        const digitos = valor.replace(/\D/g, '').slice(0, 11);

        if (!digitos) return '';
        if (digitos.length <= 2) return `(${digitos}`;

        const ddd = digitos.slice(0, 2);
        const numero = digitos.slice(2);

        if (numero.length <= 4) return `(${ddd}) ${numero}`;

        const prefixo = numero.slice(0, numero.length - 4);
        const sufixo = numero.slice(-4);
        return `(${ddd}) ${prefixo}-${sufixo}`;
    };

    if (cpf) {
        cpf.addEventListener('input', () => {
            cpf.value = formatarCpf(cpf.value);
        });
    }

    if (telefone) {
        telefone.addEventListener('input', () => {
            telefone.value = formatarTelefone(telefone.value);
        });
    }

    form.addEventListener('submit', (e) => {
        if (cpf) {
            cpf.value = formatarCpf(cpf.value);
        }

        if (telefone) {
            telefone.value = formatarTelefone(telefone.value);
        }

        if (senha.value !== confirmarSenha.value) {
            e.preventDefault();
            if (window.SheetModal) {
                window.SheetModal.showMessage({
                    type: 'error',
                    title: 'Erro',
                    message: 'As senhas não coincidem!',
                });
            }
            return;
        }

        if (senha.value.length < 8) {
            e.preventDefault();
            if (window.SheetModal) {
                window.SheetModal.showMessage({
                    type: 'error',
                    title: 'Erro',
                    message: 'A senha deve ter pelo menos 8 caracteres.',
                });
            }
            return;
        }
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

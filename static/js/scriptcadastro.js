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

    form.addEventListener('submit', (e) => {
        if (cpf) cpf.value = formatarCpf(cpf.value);
        if (telefone) telefone.value = formatarTelefone(telefone.value);

        let valido = true;
        const nome = document.getElementById('nome');
        const email = document.getElementById('email');
        const dataNasc = document.getElementById('data_nascimento');
        const termos = document.getElementById('termos');

        // Nome
        if (!nome || !/^[A-Za-zÀ-ÖØ-öø-ÿ\s']+$/.test(nome.value.trim())) {
            mostrarErro('erro-nome', 'Nome deve conter apenas letras.');
            valido = false;
        } else { limparErro('erro-nome'); }

        // Email
        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) {
            mostrarErro('erro-email', 'Informe um e-mail válido.');
            valido = false;
        } else { limparErro('erro-email'); }

        // Data de nascimento
        if (!dataNasc || !dataNasc.value) {
            mostrarErro('erro-data', 'Informe sua data de nascimento.');
            valido = false;
        } else {
            const nasc = new Date(dataNasc.value);
            const hoje = new Date();
            const idade = hoje.getFullYear() - nasc.getFullYear() -
                ((hoje.getMonth(), hoje.getDate()) < (nasc.getMonth(), nasc.getDate()) ? 1 : 0);
            if (idade < 18) {
                mostrarErro('erro-data', 'Você deve ter pelo menos 18 anos.');
                valido = false;
            } else if (idade > 100) {
                mostrarErro('erro-data', 'Data de nascimento inválida.');
                valido = false;
            } else { limparErro('erro-data'); }
        }

        // Telefone
        if (!telefone || !/^\(\d{2}\)\s\d{4,5}-\d{4}$/.test(telefone.value)) {
            mostrarErro('erro-telefone', 'Informe um telefone válido: (41) 99999-9999.');
            valido = false;
        } else { limparErro('erro-telefone'); }

        // CPF
        if (!cpf || !/^\d{3}\.\d{3}\.\d{3}-\d{2}$/.test(cpf.value)) {
            mostrarErro('erro-cpf', 'Informe um CPF válido: 000.000.000-00.');
            valido = false;
        } else { limparErro('erro-cpf'); }

        // Senha
        if (!senha || senha.value.length < 8 || !/[A-Za-z]/.test(senha.value) || !/\d/.test(senha.value)) {
            mostrarErro('erro-senha', 'A senha deve ter pelo menos 8 caracteres, uma letra e um número.');
            valido = false;
        } else { limparErro('erro-senha'); }

        // Confirmar senha
        if (!confirmarSenha || confirmarSenha.value !== senha.value) {
            mostrarErro('erro-confirmar', 'As senhas não coincidem.');
            valido = false;
        } else { limparErro('erro-confirmar'); }

        // Termos
        if (!termos || !termos.checked) {
            mostrarErro('erro-termos', 'Você precisa aceitar os termos para continuar.');
            valido = false;
        } else { limparErro('erro-termos'); }

        if (!valido) e.preventDefault();
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

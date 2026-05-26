document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('cadastroForm');
    if (!form) {
        return;
    }

    const nome = document.getElementById('nome');
    const email = document.getElementById('email');
    const dataNasc = document.getElementById('data_nascimento');
    const senha = document.getElementById('senha');
    const confirmarSenha = document.getElementById('confirmar_senha');
    const telefone = document.getElementById('telefone');
    const cpf = document.getElementById('cpf');
    const termos = document.getElementById('termos');

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

    const validarCampo = (input, mensagemObrigatorio, mensagemInvalido) => {
        if (!input) {
            return null;
        }
        const valor = input.value.trim();
        if (input.required && !valor) {
            return mensagemObrigatorio;
        }
        if (valor && !validarPattern(input)) {
            return mensagemInvalido || input.getAttribute('title') || 'Valor inválido.';
        }
        return null;
    };

    const validarCpf = (valor) => {
        const digitos = valor.replace(/\D/g, '');
        if (digitos.length !== 11) {
            return false;
        }
        if (/^(\d)\1+$/.test(digitos)) {
            return false;
        }
        let soma = 0;
        for (let i = 0; i < 9; i += 1) {
            soma += parseInt(digitos.charAt(i), 10) * (10 - i);
        }
        let resto = (soma * 10) % 11;
        if (resto === 10) resto = 0;
        if (resto !== parseInt(digitos.charAt(9), 10)) {
            return false;
        }
        soma = 0;
        for (let i = 0; i < 10; i += 1) {
            soma += parseInt(digitos.charAt(i), 10) * (11 - i);
        }
        resto = (soma * 10) % 11;
        if (resto === 10) resto = 0;
        return resto === parseInt(digitos.charAt(10), 10);
    };

    const validarDataNascimento = () => {
        if (!dataNasc || !dataNasc.value) {
            return 'Informe sua data de nascimento.';
        }
        const nasc = new Date(dataNasc.value);
        if (Number.isNaN(nasc.getTime())) {
            return 'Data de nascimento inválida.';
        }
        const hoje = new Date();
        const idade = hoje.getFullYear() - nasc.getFullYear() -
            ((hoje.getMonth(), hoje.getDate()) < (nasc.getMonth(), nasc.getDate()) ? 1 : 0);
        if (idade < 18) {
            return 'Você deve ter pelo menos 18 anos.';
        }
        if (idade > 100) {
            return 'Data de nascimento inválida.';
        }
        return null;
    };

    form.addEventListener('submit', (e) => {
        if (cpf) {
            cpf.value = formatarCpf(cpf.value);
        }

        if (telefone) {
            telefone.value = formatarTelefone(telefone.value);
        }

        const erroNome = validarCampo(nome, 'Informe seu nome completo.', 'O nome deve conter apenas letras.');
        if (erroNome) {
            e.preventDefault();
            mostrarErro(erroNome);
            return;
        }

        const erroEmail = validarCampo(email, 'Informe seu email.', 'Email inválido.');
        if (erroEmail) {
            e.preventDefault();
            mostrarErro(erroEmail);
            return;
        }

        const erroData = validarDataNascimento();
        if (erroData) {
            e.preventDefault();
            mostrarErro(erroData);
            return;
        }

        const erroTelefone = validarCampo(telefone, 'Informe seu telefone.', 'Telefone inválido.');
        if (erroTelefone) {
            e.preventDefault();
            mostrarErro(erroTelefone);
            return;
        }

        const erroCpf = validarCampo(cpf, 'Informe seu CPF.', 'CPF inválido.');
        if (erroCpf) {
            e.preventDefault();
            mostrarErro(erroCpf);
            return;
        }
        if (cpf && !validarCpf(cpf.value)) {
            e.preventDefault();
            mostrarErro('CPF inválido.');
            return;
        }

        const erroSenha = validarCampo(
            senha,
            'Informe uma senha.',
            'A senha deve ter pelo menos 8 caracteres, incluindo uma letra e um número.'
        );
        if (erroSenha) {
            e.preventDefault();
            mostrarErro(erroSenha);
            return;
        }

        if (senha && confirmarSenha && senha.value !== confirmarSenha.value) {
            e.preventDefault();
            mostrarErro('As senhas não coincidem!');
            return;
        }

        if (termos && !termos.checked) {
            e.preventDefault();
            mostrarErro('Você precisa aceitar os termos para continuar.');
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

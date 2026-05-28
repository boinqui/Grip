function formatarCpf(valor) {
    const digitos = valor.replace(/\D/g, '').slice(0, 11);

    if (digitos.length <= 3) return digitos;
    if (digitos.length <= 6) return `${digitos.slice(0, 3)}.${digitos.slice(3)}`;
    if (digitos.length <= 9) return `${digitos.slice(0, 3)}.${digitos.slice(3, 6)}.${digitos.slice(6)}`;
    return `${digitos.slice(0, 3)}.${digitos.slice(3, 6)}.${digitos.slice(6, 9)}-${digitos.slice(9, 11)}`;
}

function formatarTelefone(valor) {
    const digitos = valor.replace(/\D/g, '').slice(0, 11);

    if (!digitos) return '';
    if (digitos.length <= 2) return `(${digitos}`;

    const ddd = digitos.slice(0, 2);
    const numero = digitos.slice(2);

    if (numero.length <= 4) return `(${ddd}) ${numero}`;

    const prefixo = numero.slice(0, numero.length - 4);
    const sufixo = numero.slice(-4);
    return `(${ddd}) ${prefixo}-${sufixo}`;
}

function aplicarMascaraCpf(input) {
    if (!input) return;
    input.addEventListener('input', () => {
        input.value = formatarCpf(input.value);
    });
}

function aplicarMascaraTelefone(input) {
    if (!input) return;
    input.addEventListener('input', () => {
        input.value = formatarTelefone(input.value);
    });
}

function initMascaras() {
    aplicarMascaraCpf(document.getElementById('cpf'));
    aplicarMascaraTelefone(document.getElementById('telefone'));
}

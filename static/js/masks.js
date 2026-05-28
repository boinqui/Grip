function mascaraTelefone(input) {
    const d = input.value.replace(/\D/g, '').slice(0, 11);
    if (!d) { input.value = ''; return; }
    const ddd = d.slice(0, 2);
    const num = d.slice(2);
    if (d.length <= 2) { input.value = `(${ddd}`; return; }
    if (num.length <= 4) { input.value = `(${ddd}) ${num}`; return; }
    const pre = num.slice(0, num.length - 4);
    const suf = num.slice(-4);
    input.value = `(${ddd}) ${pre}-${suf}`;
}

function mascaraCPF(input) {
    const d = input.value.replace(/\D/g, '').slice(0, 11);
    if (d.length <= 3) { input.value = d; return; }
    if (d.length <= 6) { input.value = `${d.slice(0,3)}.${d.slice(3)}`; return; }
    if (d.length <= 9) { input.value = `${d.slice(0,3)}.${d.slice(3,6)}.${d.slice(6)}`; return; }
    input.value = `${d.slice(0,3)}.${d.slice(3,6)}.${d.slice(6,9)}-${d.slice(9,11)}`;
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('input[data-mask="telefone"]').forEach(function (el) {
        el.addEventListener('input', function () { mascaraTelefone(el); });
    });
    document.querySelectorAll('input[data-mask="cpf"]').forEach(function (el) {
        el.addEventListener('input', function () { mascaraCPF(el); });
    });
});

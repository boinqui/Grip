document.addEventListener('DOMContentLoaded', () => {
    const filtros = document.querySelectorAll('.filtro');
    const cards = document.querySelectorAll('#profs-grid .card');
    const vazio = document.getElementById('no-results');

    if (filtros.length && cards.length) {
        const aplicarFiltro = (filtro) => {
            let visiveis = 0;
            cards.forEach((card) => {
                const categoria = card.getAttribute('data-category');
                const exibir = filtro === 'todos' || categoria === filtro;
                card.classList.toggle('hidden', !exibir);
                if (exibir) visiveis += 1;
            });
            if (vazio) {
                vazio.style.display = visiveis ? 'none' : 'block';
            }
        };

        filtros.forEach((botao) => {
            botao.addEventListener('click', () => {
                filtros.forEach((item) => item.classList.remove('active'));
                botao.classList.add('active');
                aplicarFiltro(botao.dataset.filter || 'todos');
            });
        });
    }

    const opcoesTipoAula = document.querySelectorAll('.tipos .opcao');
    if (opcoesTipoAula.length) {
        opcoesTipoAula.forEach((opcao) => {
            const input = opcao.querySelector('input[type="radio"]');
            if (!input) return;
            opcao.addEventListener('click', () => {
                opcoesTipoAula.forEach((item) => item.classList.remove('active'));
                input.checked = true;
                opcao.classList.add('active');
            });
        });
    }
});

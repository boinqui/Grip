const toggle = document.querySelector('.nav-toggle');
const menu = document.querySelector('.menu');

if (toggle && menu) {
    toggle.addEventListener('click', () => {
        const isOpen = menu.classList.toggle('aberto');
        toggle.classList.toggle('aberto', isOpen);
        toggle.setAttribute('aria-expanded', String(isOpen));
    });

    menu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            menu.classList.remove('aberto');
            toggle.classList.remove('aberto');
            toggle.setAttribute('aria-expanded', 'false');
        });
    });
}

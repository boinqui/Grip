const toggle = document.querySelector('.nav-toggle');
const menu = document.querySelector('.navbar');

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

function previewImagem(event) {
    const input = event.target;
    const file = input.files[0];
    const preview = document.getElementById('previewFoto');
    const erro = document.getElementById('erroFoto');
    const fallback = document.getElementById('previewFallback');
    const btnSalvar = document.getElementById('btnSalvarFoto'); 
    
    if(erro) erro.style.display = 'none';
    if(btnSalvar) btnSalvar.disabled = true;
    
    if (file) {
        const tiposPermitidos = ['image/jpeg', 'image/png', 'image/jpg'];
        if (!tiposPermitidos.includes(file.type)) {
            if(erro) {
                erro.textContent = "Apenas imagens JPG, JPEG e PNG são permitidas.";
                erro.style.display = 'block';
            }
            input.value = "";
            return;
        }
        
        if (file.size > 16 * 1024 * 1024) {
            if(erro) {
                erro.textContent = "A imagem deve ter menos de 16MB.";
                erro.style.display = 'block';
            }
            input.value = "";
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            if(preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
            if(fallback) fallback.style.display = 'none'; // Some com as iniciais
            if(btnSalvar) btnSalvar.disabled = false;     // <-- HABILITA O BOTÃO!
        }
        reader.readAsDataURL(file);
    }
}
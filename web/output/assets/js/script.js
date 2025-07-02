// Tab switching functionality
document.addEventListener('DOMContentLoaded', function() {
    // Gestione tab
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', function() {
            const lang = this.getAttribute('data-lang');
            const card = this.closest('.algorithm-card');

            // Rimuovi la classe active da tutti i tab
            card.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            // Aggiungi la classe active al tab cliccato
            this.classList.add('active');

            // Nascondi tutti i contenitori di codice
            card.querySelectorAll('.code-container').forEach(container => {
                container.classList.remove('active');
            });
            // Mostra solo il contenitore di codice corrispondente
            const codeContainer = card.querySelector(`#code-${lang}`);
            if (codeContainer) {
                codeContainer.classList.add('active');
            }
        });
    });

    // Funzionalità copia codice
    document.querySelectorAll('.copy-btn').forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const codeContainer = document.getElementById(targetId);
            if (codeContainer) {
                const codeElement = codeContainer.querySelector('code');
                if (codeElement) {
                    const text = codeElement.innerText;
                    navigator.clipboard.writeText(text).then(() => {
                        const originalText = this.innerHTML;
                        this.innerHTML = 'Copiato! <i class="fas fa-check"></i>';
                        setTimeout(() => {
                            this.innerHTML = originalText;
                        }, 2000);
                    });
                }
            }
        });
    });
});
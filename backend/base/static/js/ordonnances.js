document.addEventListener('DOMContentLoaded', function() {
    // Animation des cartes
    const cards = document.querySelectorAll('.ordonnance-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.animationDelay = `${index * 0.1}s`;
        card.style.animation = 'fadeIn 0.5s ease-in forwards';
    });

    // Recherche en temps réel
    const searchInput = document.getElementById("searchInput");

    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        
        cards.forEach(card => {
            const content = card.textContent.toLowerCase();
            const doctorName = card.querySelector('.card-header h5').textContent.toLowerCase();
            
            if (content.includes(searchTerm) || doctorName.includes(searchTerm)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    });
}); 
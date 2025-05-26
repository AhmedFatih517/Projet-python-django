document.getElementById("loginForm").addEventListener("submit", function(e) {
    e.preventDefault();
    const email = this.querySelector('input[type="email"]').value;
    const password = this.querySelector('input[type="password"]').value;
    alert(`Connexion de ${email}`);
    // Ici, une requête AJAX pour vérifier les identifiants côté serveur
  });
  
  document.getElementById("registerForm").addEventListener("submit", function(e) {
    e.preventDefault();
    const inputs = this.querySelectorAll('input');
    const userData = {
      nom: inputs[0].value,
      prenom: inputs[1].value,
      email: inputs[2].value,
      password: inputs[3].value
    };
    alert(`Inscription de ${userData.prenom} ${userData.nom}`);
    // Envoi des données au serveur pour enregistrement
  });
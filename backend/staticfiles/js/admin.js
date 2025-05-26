// admin.js

// Ajouter un utilisateur
document.getElementById('userForm')?.addEventListener('submit', function (e) {
    e.preventDefault();
    const nom = document.getElementById('nomUtilisateur').value;
    const role = document.getElementById('roleUtilisateur').value;
  
    const usersDiv = document.getElementById('usersList');
    usersDiv.innerHTML += `
      <div class="alert alert-secondary">
        Utilisateur ajouté : <strong>${nom}</strong> (${role})
      </div>
    `;
    this.reset();
  });
  
  // Afficher les paramètres de la plateforme
  function afficherParametres() {
    const parametresDiv = document.getElementById('parametresResultat');
    parametresDiv.innerHTML = `
      <div class="alert alert-dark">
        <strong>Paramètres actuels :</strong><br>
        - Mode : Production<br>
        - Langue : Français<br>
        - Sécurité : Active (authentification à double facteur)
      </div>
    `;
  }
  document.addEventListener("DOMContentLoaded", () => {
    chargerUtilisateurs();
    chargerConfigurations();
  });
  
  function chargerUtilisateurs() {
    const liste = document.getElementById("liste-utilisateurs");
    liste.innerHTML = '<ul><li>Jean Martin (Patient)</li></ul>';
  }
  
  function chargerConfigurations() {
    const config = document.getElementById("config");
    config.innerHTML = '<p>Notifications : Activées</p>';
  }
  
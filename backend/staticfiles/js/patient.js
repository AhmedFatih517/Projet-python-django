// patient.js

// Simuler les rappels de traitement
document.getElementById('traitementForm')?.addEventListener('submit', function (e) {
    e.preventDefault();
    const traitement = document.getElementById('traitement').value;
    alert(`Rappel enregistré pour : ${traitement}`);
    document.getElementById('traitementForm').reset();
  });
  
  // Journal de santé
  document.getElementById('journalForm')?.addEventListener('submit', function (e) {
    e.preventDefault();
    const symptomes = document.getElementById('symptomes').value;
    const mesures = document.getElementById('mesures').value;
  
    const journalDiv = document.getElementById('journalResultat');
    journalDiv.innerHTML = `
      <div class="alert alert-info">
        <strong>Symptômes :</strong> ${symptomes}<br>
        <strong>Mesures :</strong> ${mesures}
      </div>
    `;
    this.reset();
  });
  
  // Planification de rendez-vous
  document.getElementById('rdvForm')?.addEventListener('submit', function (e) {
    e.preventDefault();
    const medecin = document.getElementById('medecin').value;
    const date = document.getElementById('dateRdv').value;
  
    const resultDiv = document.getElementById('rdvResultat');
    resultDiv.innerHTML = `
      <div class="alert alert-success">
        Rendez-vous confirmé avec le Dr. ${medecin} le ${date}.
      </div>
    `;
    this.reset();
  });
  
  // Accès aux infos d'urgence
  function afficherUrgence() {
    const urgenceDiv = document.getElementById('urgenceInfo');
    urgenceDiv.innerHTML = `
      <div class="alert alert-danger">
        <strong>Nom :</strong> Amine B.<br>
        <strong>Groupe sanguin :</strong> O+<br>
        <strong>Allergies :</strong> Aucun<br>
        <strong>Traitement actuel :</strong> Metformine 500mg
      </div>
    `;
  }
  document.addEventListener("DOMContentLoaded", () => {
    chargerRendezVous();
    chargerAlertes();
    chargerOrdonnances();
    chargerDossier();
  });
  
  function chargerRendezVous() {
    const container = document.getElementById("liste-rdv");
    container.innerHTML = '<ul><li>Dr Martin - 21/04/2025 à 10h</li></ul>';
  }
  
  function chargerAlertes() {
    const alertes = document.getElementById("alertes");
    alertes.innerHTML = '<p>Prendre Paracétamol à 8h</p>';
  }
  
  function chargerOrdonnances() {
    const ord = document.getElementById("ordonnances");
    ord.innerHTML = '<p>Ibuprofène - 3x/jour</p>';
  }
  
  function chargerDossier() {
    const dossier = document.getElementById("dossier");
    dossier.innerHTML = '<p>Antécédents : Asthme</p>';
  }
  
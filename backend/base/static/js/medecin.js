// medecin.js

// Afficher le dossier d’un patient
function afficherDossier() {
    const patientId = document.getElementById('patientId').value;
    const dossierDiv = document.getElementById('dossierResultat');
  
    // Simuler les données récupérées
    dossierDiv.innerHTML = `
      <div class="alert alert-info">
        <strong>ID Patient :</strong> ${patientId}<br>
        <strong>Antécédents :</strong> Diabète, Hypertension<br>
        <strong>Traitement :</strong> Insuline, Bétabloquants<br>
        <strong>Consultations récentes :</strong> 03/03/2025, 20/02/2025
      </div>
    `;
  }
  
  // Gérer l’emploi du temps
  function gererAgenda() {
    const agendaDiv = document.getElementById('agendaResultat');
    agendaDiv.innerHTML = `
      <div class="alert alert-warning">
        <strong>Agenda du jour :</strong><br>
        09:00 - Consultation avec Patient A<br>
        10:00 - Téléconsultation avec Patient B<br>
        11:30 - Suivi post-hospitalisation
      </div>
    `;
  }
  
  // Enregistrer une prescription
  document.getElementById('prescriptionForm')?.addEventListener('submit', function (e) {
    e.preventDefault();
    const patient = document.getElementById('patientNom').value;
    const medicament = document.getElementById('medicament').value;
  
    const result = document.getElementById('prescriptionResultat');
    result.innerHTML = `
      <div class="alert alert-success">
        Ordonnance enregistrée pour ${patient} : ${medicament}
      </div>
    `;
    this.reset();
  });
  document.addEventListener("DOMContentLoaded", () => {
    chargerAgenda();
    chargerDossiersPatients();
  });
  
  function chargerAgenda() {
    const agenda = document.getElementById("agenda");
    agenda.innerHTML = '<ul><li>10h - Mme Dupont</li></ul>';
  }
  
  function chargerDossiersPatients() {
    const dossiers = document.getElementById("dossiers-patients");
    dossiers.innerHTML = '<p>M. Durand : Glycémie instable</p>';
  }
  
  document.getElementById("form-prescription").addEventListener("submit", function(e) {
    e.preventDefault();
    const [medicament, dosage, duree] = this.querySelectorAll('input');
    alert(`Prescription : ${medicament.value}, ${dosage.value}, ${duree.value}`);
  });
  
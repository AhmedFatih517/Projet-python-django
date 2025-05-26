document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("ordonnance-form");
    const ordonnancesContainer = document.getElementById("ordonnances-patient");
  
    // Charger les ordonnances existantes
    afficherOrdonnances();
  
    form.addEventListener("submit", (e) => {
      e.preventDefault();
  
      const data = {
        date: form.date.value,
        patient: form.patient.value,
        medecin: form.medecin.value,
        categorie: form.categorie.value,
        medicaments: form.medicaments.value,
        date_fin: form.date_fin.value,
        remarques: form.remarques.value,
        rappel: form.rappel.checked,
        langue: form.langue.value,
      };
  
      // Récupération des données actuelles
      const ordonnances = JSON.parse(localStorage.getItem("ordonnances")) || [];
  
      // Ajout de la nouvelle ordonnance
      ordonnances.push(data);
      localStorage.setItem("ordonnances", JSON.stringify(ordonnances));
  
      // Réinitialiser le formulaire
      form.reset();
  
      // Afficher les ordonnances mises à jour
      afficherOrdonnances();
    });
  
    function afficherOrdonnances() {
      const ordonnances = JSON.parse(localStorage.getItem("ordonnances")) || [];
      ordonnancesContainer.innerHTML = "";
  
      if (ordonnances.length === 0) {
        ordonnancesContainer.innerHTML = "<p>Aucune ordonnance enregistrée.</p>";
        return;
      }
  
      ordonnances.forEach((o, index) => {
        const div = document.createElement("div");
        div.className = "ordonnance-card fade-in";
  
        div.innerHTML = `
          <h3>Ordonnance ${index + 1}</h3>
          <p><strong>Date :</strong> ${o.date}</p>
          <p><strong>Patient :</strong> ${o.patient}</p>
          <p><strong>Médecin :</strong> ${o.medecin}</p>
          <p><strong>Catégorie :</strong> ${o.categorie}</p>
          <p><strong>Médicaments :</strong> ${o.medicaments}</p>
          <p><strong>Fin du traitement :</strong> ${o.date_fin || "Non précisé"}</p>
          <p><strong>Remarques :</strong> ${o.remarques || "Aucune"}</p>
          <p><strong>Langue :</strong> ${o.langue}</p>
          <p><strong>Rappel :</strong> ${o.rappel ? "Oui" : "Non"}</p>
        `;
  
        ordonnancesContainer.appendChild(div);
      });
    }
    document.addEventListener("DOMContentLoaded", () => {
        const form = document.getElementById("ordonnance-form");
        const ordonnancesContainer = document.getElementById("ordonnances-patient");
      
        // Charger les ordonnances existantes au démarrage
        afficherOrdonnances();
      
        // Soumission du formulaire
        form.addEventListener("submit", (e) => {
          e.preventDefault();
      
          const data = {
            date: form.date.value,
            patient: form.patient.value,
            medecin: form.medecin.value,
            categorie: form.categorie.value,
            medicaments: form.medicaments.value,
            date_fin: form.date_fin.value,
            remarques: form.remarques.value,
            rappel: form.rappel.checked,
            langue: form.langue.value,
          };
      
          // Sauvegarder l'ordonnance dans le localStorage
          const ordonnances = recupererOrdonnances();
          ordonnances.push(data);
          localStorage.setItem("ordonnances", JSON.stringify(ordonnances));
      
          form.reset();
          afficherOrdonnances();
        });
      
        // Fonction pour récupérer les ordonnances
        function recupererOrdonnances() {
          return JSON.parse(localStorage.getItem("ordonnances")) || [];
        }
      
        // Fonction pour afficher les ordonnances
        function afficherOrdonnances() {
          const ordonnances = recupererOrdonnances();
          ordonnancesContainer.innerHTML = "";
      
          if (ordonnances.length === 0) {
            ordonnancesContainer.innerHTML = "<p>Aucune ordonnance enregistrée.</p>";
            return;
          }
      
          ordonnances.forEach((o, index) => {
            const div = document.createElement("div");
            div.className = "ordonnance-card fade-in";
      
            div.innerHTML = `
              <h3>Ordonnance ${index + 1}</h3>
              <p><strong>Date :</strong> ${o.date}</p>
              <p><strong>Patient :</strong> ${o.patient}</p>
              <p><strong>Médecin :</strong> ${o.medecin}</p>
              <p><strong>Catégorie :</strong> ${o.categorie}</p>
              <p><strong>Médicaments :</strong> ${o.medicaments}</p>
              <p><strong>Fin du traitement :</strong> ${o.date_fin || "Non précisé"}</p>
              <p><strong>Remarques :</strong> ${o.remarques || "Aucune"}</p>
              <p><strong>Langue :</strong> ${o.langue}</p>
              <p><strong>Rappel :</strong> ${o.rappel ? "Oui" : "Non"}</p>
            `;
      
            ordonnancesContainer.appendChild(div);
          });
        }
      });
      
  });
  
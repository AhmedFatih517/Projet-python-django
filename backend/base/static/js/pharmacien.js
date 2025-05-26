// pharmacien.js

// Afficher les stocks de médicaments
function gererStock() {
    const stockDiv = document.getElementById('stockResultat');
    stockDiv.innerHTML = `
      <div class="alert alert-info">
        <strong>Stocks disponibles :</strong><br>
        Paracétamol : 120 unités<br>
        Metformine : 85 unités<br>
        Amoxicilline : 40 unités
      </div>
    `;
  }
  
  // Valider une ordonnance
  document.getElementById('validationForm')?.addEventListener('submit', function (e) {
    e.preventDefault();
    const ordonnanceId = document.getElementById('ordonnanceId').value;
    const result = document.getElementById('validationResultat');
  
    result.innerHTML = `
      <div class="alert alert-success">
        Ordonnance #${ordonnanceId} validée avec succès.
      </div>
    `;
    this.reset();
  });
  document.addEventListener("DOMContentLoaded", () => {
    afficherOrdonnances();
    afficherStocks();
  });
  
  function afficherOrdonnances() {
    const ordDiv = document.getElementById("ordonnances-a-valider");
    ordDiv.innerHTML = '<p>Ordonnance #001 - Valider ?</p>';
  }
  
  function afficherStocks() {
    const stocks = document.getElementById("stocks");
    stocks.innerHTML = '<p>Doliprane : 120 boîtes</p>';
  }
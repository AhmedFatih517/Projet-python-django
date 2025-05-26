document.getElementById("rdvForm").addEventListener("submit", function(e) {
    e.preventDefault();
    const date = this.querySelector('input[type="date"]').value;
    const heure = this.querySelector('input[type="time"]').value;
    const medecin = this.querySelector('input[type="text"]').value;
    alert(`Rendez-vous prévu le ${date} à ${heure} avec Dr ${medecin}`);
  });
  
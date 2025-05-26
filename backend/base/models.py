from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# --------------------------
# PROFIL ET ROLES UTILISATEUR
# --------------------------

ROLE_CHOICES = [
    ('patient', 'Patient'),
    ('medecin', 'Médecin'),
    ('pharmacien', 'Pharmacien'),
    ('admin', 'Administrateur'),
]

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    date_naissance = models.DateField(null=True, blank=True)
    adresse = models.CharField(max_length=200, null=True, blank=True)
    telephone = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        # Affiche le username et le rôle pour l'admin Django
        return f"{self.user.username} - {self.role}"

# Infos spécifiques Patient
class PatientInfo(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='patientinfo')
    numero_secu = models.CharField(max_length=50, null=True, blank=True)
    # Ajoute ici d'autres champs spécifiques patient

    def __str__(self):
        # Affiche le nom d'utilisateur du patient
        return f"Infos Patient de {self.profile.user.username}"

# Infos spécifiques Médecin
class MedecinInfo(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='medecininfo')
    specialite = models.CharField(max_length=100, null=True, blank=True)
    numero_ordre = models.CharField(max_length=50, null=True, blank=True)
    # Ajoute ici d'autres champs spécifiques médecin

    def __str__(self):
        # Affiche le nom d'utilisateur du médecin
        return f"Infos Médecin de {self.profile.user.username}"

# Infos spécifiques Pharmacien
class PharmacienInfo(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='pharmacieninfo')
    numero_pharmacie = models.CharField(max_length=50, null=True, blank=True)
    adresse_pharmacie = models.CharField(max_length=200, null=True, blank=True)
    # Ajoute ici d'autres champs spécifiques pharmacien

    def __str__(self):
        # Affiche le nom d'utilisateur du pharmacien
        return f"Infos Pharmacien de {self.profile.user.username}"

# ---------------------
# RENDEZ-VOUS & JOURNAL
# ---------------------

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('à venir', 'À venir'),
        ('passé', 'Passé'),
        ('en attente', 'En attente'),
        ('terminé', 'Terminé')
    ]
    patient = models.ForeignKey(PatientInfo, on_delete=models.CASCADE)
    doctor = models.ForeignKey(MedecinInfo, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    time = models.TimeField()
    reason = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    is_cancelled = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='à venir')

    def __str__(self):
        return f"Rendez-vous {self.date} à {self.time} avec Dr {self.doctor.profile.user.get_full_name()}"

    def is_past(self):
        today = timezone.now().date()
        return self.date < today

class HealthJournal(models.Model):
    patient = models.ForeignKey(PatientInfo, on_delete=models.CASCADE)
    doctor = models.ForeignKey(MedecinInfo, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    tension_art = models.DecimalField(max_digits=5, decimal_places=2, default=120.0)
    glycemie = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        # Affiche le nom d'utilisateur du patient
        return f"Journal de santé de {self.patient.profile.user.username} - {self.date}"

# ---------------------
# DOSSIER MÉDICAL & ORDONNANCES
# ---------------------

class MedicalRecord(models.Model):
    patient = models.OneToOneField(PatientInfo, on_delete=models.CASCADE)
    doctor = models.ForeignKey(MedecinInfo, on_delete=models.CASCADE)
    diagnosis = models.TextField(blank=True)
    antecedents = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    observations = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Affiche le nom d'utilisateur du patient
        return f"Dossier médical de {self.patient.profile.user.username}"

class Ordonnance(models.Model):
    patient = models.ForeignKey(PatientInfo, on_delete=models.CASCADE)
    doctor = models.ForeignKey(MedecinInfo, on_delete=models.CASCADE)
    content = models.TextField()
    issued_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=50, null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    language = models.CharField(max_length=2, default='fr')
    reminder = models.BooleanField(default=False)
    scanned_prescription = models.FileField(upload_to='ordonnances/', null=True, blank=True)

    def __str__(self):
        return f"Ordonnance pour {self.patient} par Dr. {self.doctor}"

# ---------------------
# LIVRAISONS & NOTIFICATIONS
# ---------------------

class Delivery(models.Model):
    ordonnance = models.ForeignKey(Ordonnance, on_delete=models.CASCADE)
    delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Livraison de l'ordonnance {self.ordonnance.id} - {'Livrée' if self.delivered else 'En attente'}"

class Notification(models.Model):
    doctor = models.ForeignKey(MedecinInfo, on_delete=models.CASCADE)
    message = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return self.message[:50]

class Room(models.Model):
    ROOM_TYPES = [
        ('Consultation', 'Consultation'),
        ('Opération', 'Opération'),
        ('Urgence', 'Urgence'),
        ('Radiologie', 'Radiologie'),
        ('Laboratoire', 'Laboratoire'),
    ]
    
    ROOM_STATUS = [
        ('Disponible', 'Disponible'),
        ('Occupée', 'Occupée'),
        ('En maintenance', 'En maintenance'),
    ]
    
    numero = models.CharField(max_length=10, unique=True)
    type = models.CharField(max_length=20, choices=ROOM_TYPES)
    status = models.CharField(max_length=20, choices=ROOM_STATUS, default='Disponible')
    capacite = models.IntegerField()
    equipements = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Salle {self.numero} ({self.type})"

class Equipment(models.Model):
    EQUIPMENT_TYPES = [
        ('Imagerie', 'Imagerie'),
        ('Diagnostic', 'Diagnostic'),
        ('Chirurgie', 'Chirurgie'),
        ('Urgence', 'Urgence'),
        ('Monitoring', 'Monitoring'),
    ]
    
    EQUIPMENT_STATUS = [
        ('Opérationnel', 'Opérationnel'),
        ('En maintenance', 'En maintenance'),
        ('Hors service', 'Hors service'),
    ]
    
    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=EQUIPMENT_TYPES)
    status = models.CharField(max_length=20, choices=EQUIPMENT_STATUS, default='Opérationnel')
    salle = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nom} ({self.type})"

class RoomSchedule(models.Model):
    salle = models.ForeignKey(Room, on_delete=models.CASCADE)
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    motif = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    is_cancelled = models.BooleanField(default=False)

    def __str__(self):
        return f"Réservation {self.salle.numero} le {self.date}"

class Maintenance(models.Model):
    MAINTENANCE_TYPES = [
        ('Préventive', 'Préventive'),
        ('Corrective', 'Corrective'),
        ('Inspection', 'Inspection'),
        ('Calibration', 'Calibration'),
    ]
    
    MAINTENANCE_STATUS = [
        ('Planifiée', 'Planifiée'),
        ('En cours', 'En cours'),
        ('Terminée', 'Terminée'),
    ]
    
    equipement = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    status = models.CharField(max_length=20, choices=MAINTENANCE_STATUS, default='Planifiée')
    description = models.TextField()
    date_prevue = models.DateField()
    date_debut = models.DateTimeField(null=True, blank=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Maintenance de {self.equipement.nom} ({self.type})"

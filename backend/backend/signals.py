from base.models import CustomUser, PatientProfile, DoctorProfile, PharmacistProfile
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model



@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crée automatiquement le profil associé à un utilisateur selon son rôle.
    """
    if created:
        if instance.role == 'patient':
            PatientProfile.objects.create(user=instance)
        elif instance.role == 'doctor':
            DoctorProfile.objects.create(user=instance)
        elif instance.role == 'pharmacist':
            PharmacistProfile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """
    Sauvegarde automatiquement le profil lié lorsque l'utilisateur est modifié.
    """
    try:
        if instance.role == 'patient':
            instance.patientprofile.save()
        elif instance.role == 'doctor':
            instance.doctorprofile.save()
        elif instance.role == 'pharmacist':
            instance.pharmacistprofile.save()
    except Exception:
        # Évite l'erreur si le profil n'existe pas encore
        pass
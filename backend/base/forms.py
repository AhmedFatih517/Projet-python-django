from django import forms
from django.contrib.auth.models import User
from .models import Appointment, HealthJournal, PatientInfo, MedecinInfo, PharmacienInfo, Profile, Ordonnance, MedicalRecord

# ----------- FORMULAIRE INSCRIPTION MULTI-ROLE -----------

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmer le mot de passe', widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=Profile._meta.get_field('role').choices)

    # Champs profil généraux
    date_naissance = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    adresse = forms.CharField(required=False)
    telephone = forms.CharField(required=False)

    # Champs spécifiques (s'affichent selon le rôle dans le template)
    numero_secu = forms.CharField(required=False, label="Numéro sécurité sociale (patient)")
    specialite = forms.CharField(required=False, label="Spécialité (médecin)")
    numero_ordre = forms.CharField(required=False, label="Numéro d'ordre (médecin)")
    numero_pharmacie = forms.CharField(required=False, label="Numéro pharmacie (pharmacien)")
    adresse_pharmacie = forms.CharField(required=False, label="Adresse pharmacie (pharmacien)")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd.get('password') != cd.get('password2'):
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cd.get('password2')

    def save(self, commit=True):
        # Création de l'utilisateur User natif
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()

            # Création du profil général lié au user
            profile = Profile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                date_naissance=self.cleaned_data.get('date_naissance'),
                adresse=self.cleaned_data.get('adresse'),
                telephone=self.cleaned_data.get('telephone'),
            )

            # Création des infos spécifiques selon le rôle choisi
            if profile.role == 'patient':
                PatientInfo.objects.create(
                    profile=profile,
                    numero_secu=self.cleaned_data.get('numero_secu')
                )
            elif profile.role == 'medecin':
                MedecinInfo.objects.create(
                    profile=profile,
                    specialite=self.cleaned_data.get('specialite'),
                    numero_ordre=self.cleaned_data.get('numero_ordre')
                )
            elif profile.role == 'pharmacien':
                PharmacienInfo.objects.create(
                    profile=profile,
                    numero_pharmacie=self.cleaned_data.get('numero_pharmacie'),
                    adresse_pharmacie=self.cleaned_data.get('adresse_pharmacie')
                )
        return user

# ----------- AUTRES FORMULAIRES -----------

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'time', 'reason']
        widgets = {
            'doctor': forms.Select(attrs={
                'class': 'form-control',
                'style': 'padding: 10px; border-radius: 8px; border: 1px solid #ddd;'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'style': 'padding: 10px; border-radius: 8px; border: 1px solid #ddd;'
            }),
            'time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'style': 'padding: 10px; border-radius: 8px; border: 1px solid #ddd;'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'style': 'padding: 10px; border-radius: 8px; border: 1px solid #ddd;'
            }),
        }
        labels = {
            'doctor': 'Médecin',
            'date': 'Date',
            'time': 'Heure',
            'reason': 'Motif du rendez-vous',
        }

    def __init__(self, *args, **kwargs):
        super(AppointmentForm, self).__init__(*args, **kwargs)
        # Récupérer tous les médecins avec leurs informations
        medecins = MedecinInfo.objects.select_related('profile__user').all()
        # Créer une liste de tuples (id, nom_complet) pour le choix
        choices = [(m.id, f"Dr. {m.profile.user.get_full_name()} - {m.specialite}") for m in medecins]
        # Ajouter un choix vide au début
        choices.insert(0, ('', 'Sélectionnez un médecin'))
        # Mettre à jour les choix du champ doctor
        self.fields['doctor'].choices = choices
        # Ajouter des classes CSS pour le style
        self.fields['doctor'].widget.attrs.update({
            'class': 'form-control select2',
            'data-placeholder': 'Sélectionnez un médecin'
        })

class HealthJournalForm(forms.ModelForm):
    class Meta:
        model = HealthJournal
        fields = ['date', 'tension_art', 'glycemie', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'tension_art': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'glycemie': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'date': 'Date',
            'tension_art': 'Tension Artérielle (mmHg)',
            'glycemie': 'Glycémie (mg/dL)',
            'notes': 'Notes',
        }

class OrdonnanceForm(forms.ModelForm):
    class Meta:
        model = Ordonnance
        fields = ['patient', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'patient': forms.Select(attrs={'class': 'form-control'})
        }

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['diagnosis', 'antecedents', 'allergies', 'medications', 'observations']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'antecedents': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'medications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'diagnosis': 'Diagnostic',
            'antecedents': 'Antécédents',
            'allergies': 'Allergies',
            'medications': 'Médicaments',
            'observations': 'Observations',
        }

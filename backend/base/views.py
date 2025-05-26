from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
import logging
from django.http import JsonResponse, HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from django.urls import reverse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import ExtractWeekDay
import random
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect

from .forms import UserRegistrationForm, AppointmentForm, HealthJournalForm, OrdonnanceForm, MedicalRecordForm
from .models import (
    Profile, PatientInfo, MedecinInfo, PharmacienInfo,
    Appointment, HealthJournal, Ordonnance, Delivery, MedicalRecord,
    Room, Equipment, RoomSchedule, Maintenance
)

logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_authenticated and user.is_staff

### --- ADMIN ET PAGES CLASSIQUES ---
@login_required
@user_passes_test(is_admin)
def admin_view(request):
    try:
        # Statistiques pour le tableau de bord
        today = timezone.now().date()
        current_month = timezone.now().month
        
        stats = {
            'total_patients': PatientInfo.objects.count(),
            'total_doctors': MedecinInfo.objects.count(),
            'appointments_today': Appointment.objects.filter(
                date__month=current_month,
                status='terminé'
            ).count() * 50  # exemple de calcul de revenus
        }
        
        context = {
            'stats': stats,
            'user': request.user
        }
        
        return render(request, 'admin.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors de l'accès au tableau de bord: {str(e)}")
        logger.error(f"Erreur dans admin_view: {str(e)}")
        return redirect('index')

@login_required
def agenda_view(request):
    try:
        # Vérifier si l'utilisateur a un profil
        if not hasattr(request.user, 'profile'):
            messages.error(request, "Profil utilisateur introuvable.")
            return redirect('index')
            
        profile = request.user.profile
        
        # Vérifier si le profil est celui d'un médecin
        if profile.role != 'medecin':
            messages.error(request, "Accès non autorisé. Cette page est réservée aux médecins.")
            return redirect('index')
            
        try:
            medecin_info = profile.medecininfo
        except MedecinInfo.DoesNotExist:
            messages.error(request, "Profil médecin introuvable.")
            return redirect('index')
            
        # Gérer l'ajout d'un nouveau rendez-vous
        if request.method == 'POST':
            try:
                patient_id = request.POST.get('patient_id')
                date = request.POST.get('date')
                time = request.POST.get('time')
                reason = request.POST.get('reason')
                
                if not all([patient_id, date, time]):
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'error',
                            'message': "Tous les champs obligatoires doivent être remplis."
                        })
                    messages.error(request, "Tous les champs obligatoires doivent être remplis.")
                    return redirect('agenda_view')
                
                patient = PatientInfo.objects.get(id=patient_id)
                
                # Créer le rendez-vous
                appointment = Appointment.objects.create(
                    patient=patient,
                    doctor=medecin_info,
                    date=date,
                    time=time,
                    reason=reason,
                    notes=request.POST.get('notes', ''),
                    status='à venir'
                )
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': "Rendez-vous ajouté avec succès.",
                        'appointment': {
                            'patient_name': patient.profile.user.get_full_name(),
                            'date': date,
                            'time': time,
                            'reason': reason,
                            'notes': request.POST.get('notes', '')
                        }
                    })
                
                messages.success(request, "Rendez-vous ajouté avec succès.")
                return redirect('agenda_view')
                
            except PatientInfo.DoesNotExist:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': "Patient introuvable."
                    })
                messages.error(request, "Patient introuvable.")
            except Exception as e:
                logger.error(f"Erreur lors de la création du rendez-vous: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': f"Une erreur est survenue lors de la création du rendez-vous: {str(e)}"
                    })
                messages.error(request, "Une erreur est survenue lors de la création du rendez-vous.")
        
        # Récupérer les rendez-vous du médecin
        today = timezone.now().date()
        rendezvous = Appointment.objects.filter(
            doctor=medecin_info,
            date__gte=today,
            is_cancelled=False
        ).order_by('date', 'time')
        
        # Récupérer les demandes de rendez-vous en attente
        pending_appointments = Appointment.objects.filter(
            doctor=medecin_info,
            status='en attente',
            is_cancelled=False
        ).order_by('date', 'time')
        
        # Récupérer tous les patients pour le formulaire d'ajout
        patients = PatientInfo.objects.all()
        
        context = {
            'rendezvous': rendezvous,
            'pending_appointments': pending_appointments,
            'medecin_info': medecin_info,
            'patients': patients
        }
        
        return render(request, 'agenda.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans agenda_view: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': f"Une erreur est survenue: {str(e)}"
            })
        messages.error(request, "Une erreur est survenue lors de l'accès à l'agenda.")
        return redirect('index')

def alerte_view(request):
    return render(request, 'alerte.html')

def choix_dossier_view(request):
    return render(request, 'choix_dossier.html')

def dossier_classique_view(request):
    return render(request, 'dossier_classique.html')

def dossier_consultation_view(request):
    return render(request, 'dossier_consultation.html')

def dossier_journalier_view(request):
    return render(request, 'dossier_journalier.html')

def index_view(request):
    return render(request, 'index.html')

def mot_de_passe_oublie_view(request):
    return render(request, 'mot_de_passe_oublie.html')

@login_required
def ordonnance_view(request):
    try:
        # Vérifier si l'utilisateur a un profil
        if not hasattr(request.user, 'profile'):
            messages.error(request, "Profil utilisateur introuvable.")
            return redirect('index')
            
        profile = request.user.profile
        
        # Vérifier si le profil est celui d'un médecin
        if profile.role != 'medecin':
            messages.error(request, "Accès non autorisé. Cette page est réservée aux médecins.")
            return redirect('index')
            
        try:
            medecin_info = profile.medecininfo
        except MedecinInfo.DoesNotExist:
            messages.error(request, "Profil médecin introuvable.")
            return redirect('index')
            
        # Récupérer les ordonnances du médecin
        ordonnances = Ordonnance.objects.filter(
            doctor=medecin_info
        ).order_by('-issued_at')
        
        # Récupérer uniquement les patients qui ont des rendez-vous avec ce médecin
        patients = PatientInfo.objects.filter(
            appointment__doctor=medecin_info,
            appointment__is_cancelled=False
        ).distinct()
        
        if request.method == 'POST':
            try:
                # Récupérer les données du formulaire
                patient_id = request.POST.get('patient')
                date = request.POST.get('date')
                medicaments = request.POST.get('medicaments')
                categorie = request.POST.get('categorie')
                date_fin = request.POST.get('date_fin')
                remarques = request.POST.get('remarques')
                langue = request.POST.get('langue')
                rappel = request.POST.get('rappel') == 'on'

                # Validation des champs obligatoires
                if not all([patient_id, date, medicaments, categorie]):
                    messages.error(request, "Veuillez remplir tous les champs obligatoires.")
                    return redirect('ordonnance_view')

                # Créer l'ordonnance
                patient = PatientInfo.objects.get(id=patient_id)
                
                # Convertir la date en datetime
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                
                # Créer l'ordonnance
                ordonnance = Ordonnance.objects.create(
                    doctor=medecin_info,
                    patient=patient,
                    content=medicaments,
                    issued_at=date_obj,
                    category=categorie,
                    end_date=date_fin if date_fin else None,
                    notes=remarques,
                    language=langue,
                    reminder=rappel
                )

                # Gérer le fichier d'ordonnance scannée s'il existe
                if 'fichier_ordonnance_originale' in request.FILES:
                    ordonnance.scanned_prescription = request.FILES['fichier_ordonnance_originale']
                    ordonnance.save()

                messages.success(request, "Ordonnance créée avec succès.")
                return redirect('ordonnance_view')

            except Exception as e:
                logger.error(f"Erreur lors de la création de l'ordonnance: {str(e)}")
                messages.error(request, f"Une erreur est survenue lors de la création de l'ordonnance: {str(e)}")
                return redirect('ordonnance_view')
        
        # Initialiser le formulaire avec les patients filtrés
        form = OrdonnanceForm()
        form.fields['patient'].queryset = patients
        
        context = {
            'ordonnances': ordonnances,
            'medecin_info': medecin_info,
            'form': form,
            'patients': patients
        }
        
        return render(request, 'ordonnance.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans ordonnance_view: {str(e)}")
        messages.error(request, f"Une erreur est survenue lors de l'accès aux ordonnances: {str(e)}")
        return redirect('index')

def rendezvous_view(request):
    try:
        profile = request.user.profile
        patient_info = profile.patientinfo
        # Récupérer tous les médecins avec leurs informations
        medecins = MedecinInfo.objects.select_related('profile__user').all()
        if request.method == "POST":
            form = AppointmentForm(request.POST)
            if form.is_valid():
                try:
                    appointment = form.save(commit=False)
                    appointment.patient = patient_info
                    appointment.save()
                    messages.success(request, "Rendez-vous pris avec succès !")
                    logger.info(f"Rendez-vous créé avec succès pour le patient {patient_info.profile.user.username}")
                    return redirect('mes_rdv')
                except Exception as e:
                    logger.error(f"Erreur lors de la création du rendez-vous: {str(e)}")
                    messages.error(request, "Une erreur est survenue lors de la création du rendez-vous.")
            else:
                logger.warning(f"Formulaire de rendez-vous invalide: {form.errors}")
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        else:
            form = AppointmentForm()
        return render(request, "rendezvous.html", {
            "form": form,
            "patient_info": patient_info,
            "medecins": medecins
        })
    except PatientInfo.DoesNotExist:
        messages.error(request, "Profil patient introuvable.")
        return redirect('logout')
    except Exception as e:
        logger.error(f"Erreur dans rendezvous_view: {str(e)}")
        messages.error(request, "Une erreur est survenue lors de l'accès au formulaire de rendez-vous.")
        return redirect('patient_view')

### --- AUTHENTIFICATION ---


  # compatible avec CustomUser si tu en as un

def inscription_view(request):
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            email = request.POST.get('email')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            nom = request.POST.get('nom')
            prenom = request.POST.get('prenom')
            role = request.POST.get('role')
            telephone = request.POST.get('telephone')
            adresse = request.POST.get('adresse')
            date_naissance = request.POST.get('date_naissance')
            sexe = request.POST.get('sexe')
            numero_secu = request.POST.get('numero_secu')

            logger.info(f"Tentative d'inscription pour l'email: {email} avec le rôle: {role}")
            logger.info(f"Données reçues - Nom: {nom}, Prénom: {prenom}, Role: {role}")

            # Validation des données
            if not all([email, password, confirm_password, nom, prenom, role]):
                logger.warning("Champs obligatoires manquants dans le formulaire d'inscription")
                messages.error(request, "Les champs suivants sont obligatoires : email, mot de passe, nom, prénom et rôle")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': 'Les champs obligatoires sont manquants'})
                return redirect('inscription')

            if password != confirm_password:
                logger.warning("Les mots de passe ne correspondent pas")
                messages.error(request, "Les mots de passe ne correspondent pas")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': 'Les mots de passe ne correspondent pas'})
                return redirect('inscription')

            # Vérification si l'email existe déjà
            if User.objects.filter(email=email).exists():
                logger.warning(f"Email déjà utilisé: {email}")
                messages.error(request, "Cet email est déjà utilisé")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': 'Cet email est déjà utilisé'})
                return redirect('inscription')

            # Vérification si l'username existe déjà
            if User.objects.filter(username=email).exists():
                logger.warning(f"Username déjà utilisé: {email}")
                messages.error(request, "Cet email est déjà utilisé comme nom d'utilisateur")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': 'Cet email est déjà utilisé comme nom d\'utilisateur'})
                return redirect('inscription')

            try:
                # Création de l'utilisateur
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=prenom,
                    last_name=nom
                )

                # Si c'est un administrateur, donner les permissions appropriées
                if role == 'admin':
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()

                logger.info(f"Utilisateur créé avec succès: {email}")

                # Créer le profil utilisateur
                profile = Profile.objects.create(
                    user=user,
                    role=role,
                    telephone=telephone,
                    adresse=adresse,
                    date_naissance=date_naissance
                )
                logger.info(f"Profil créé avec succès pour: {email}")

                # Créer le profil spécifique selon le rôle
                if role == 'patient':
                    patient_info = PatientInfo.objects.create(
                        profile=profile,
                        numero_secu=numero_secu
                    )
                    logger.info(f"Profil patient créé avec succès pour: {email}")
                elif role == 'medecin':
                    medecin_info = MedecinInfo.objects.create(
                        profile=profile,
                        specialite=request.POST.get('specialite', ''),
                        numero_ordre=request.POST.get('numero_ordre', '')
                    )
                    logger.info(f"Profil médecin créé avec succès pour: {email}")
                elif role == 'pharmacien':
                    pharmacien_info = PharmacienInfo.objects.create(
                        profile=profile,
                        numero_pharmacie=request.POST.get('numero_pharmacie', ''),
                        adresse_pharmacie=request.POST.get('adresse_pharmacie', '')
                    )
                    logger.info(f"Profil pharmacien créé avec succès pour: {email}")

                messages.success(request, f'Votre compte a été créé avec succès ! Vous pouvez maintenant vous connecter avec votre email ({email}) et votre mot de passe.')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Inscription réussie',
                        'redirect': reverse('connexion')
                    })
                return redirect('connexion')

            except Exception as e:
                logger.error(f"Erreur lors de la création du profil: {str(e)}")
                messages.error(request, f"Une erreur est survenue lors de la création du profil: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': f'Une erreur est survenue lors de la création du profil: {str(e)}'})
                return redirect('inscription')

        except Exception as e:
            logger.error(f"Erreur lors de l'inscription: {str(e)}")
            messages.error(request, f"Une erreur est survenue lors de l'inscription: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': f'Une erreur est survenue l\'inscription: {str(e)}'})
            return redirect('inscription')

    return render(request, 'inscription.html')

@csrf_protect
@ensure_csrf_cookie
def connexion_view(request):
    if request.method == "POST":
        try:
            username = request.POST.get("username")
            password = request.POST.get("password")
            
            logger.info(f"Tentative de connexion pour l'utilisateur: {username}")
            
            if not username or not password:
                logger.warning("Nom d'utilisateur ou mot de passe manquant")
                messages.error(request, "Veuillez remplir tous les champs.")
                return render(request, "connexion.html")

            # Essayer d'authentifier avec l'email comme username
            user = authenticate(request, username=username, password=password)
            
            # Si l'authentification échoue, essayer de trouver l'utilisateur par email
            if user is None:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            
            if user is not None:
                try:
                    login(request, user)
                    logger.info(f"Utilisateur connecté avec succès: {username}")
                    
                    # Si l'utilisateur est un superuser/staff, rediriger vers l'admin
                    if user.is_staff or user.is_superuser:
                        return redirect('admin')
                    
                    # Vérifier si l'utilisateur a un profil
                    if not hasattr(user, 'profile'):
                        logger.error(f"L'utilisateur {username} n'a pas de profil")
                        messages.error(request, "Erreur de profil utilisateur.")
                        return render(request, "connexion.html")
                    
                    role = user.profile.role
                    logger.info(f"Rôle de l'utilisateur: {role}")
                    
                    # Redirection basée sur le rôle
                    if role == 'patient':
                        return redirect('patient_view')
                    elif role == 'medecin':
                        logger.info(f"Redirection vers l'espace médecin pour: {username}")
                        try:
                            # Vérifier si le profil médecin existe
                            medecin_info = user.profile.medecininfo
                            return redirect('medecin_view')
                        except MedecinInfo.DoesNotExist:
                            logger.error(f"MedecinInfo introuvable pour l'utilisateur {username}")
                            messages.error(request, "Profil médecin incomplet. Veuillez contacter l'administrateur.")
                            return redirect('index')
                    elif role == 'pharmacien':
                        return redirect('pharmacien_view')
                    else:
                        logger.warning(f"Rôle inconnu pour l'utilisateur {username}: {role}")
                        messages.warning(request, "Rôle utilisateur non reconnu.")
                        return redirect('index')
                        
                except Exception as e:
                    logger.error(f"Erreur lors de la connexion: {str(e)}")
                    messages.error(request, "Une erreur est survenue lors de la connexion.")
                    return render(request, "connexion.html")
            else:
                logger.warning(f"Échec de l'authentification pour l'utilisateur: {username}")
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
                return render(request, "connexion.html")
                
        except Exception as e:
            logger.error(f"Erreur lors de la connexion: {str(e)}")
            messages.error(request, "Une erreur est survenue lors de la connexion.")
            return render(request, "connexion.html")
            
    # Assurez-vous que le cookie CSRF est défini
    response = render(request, "connexion.html")
    if not request.COOKIES.get('csrftoken'):
        response.set_cookie('csrftoken', request.META.get('CSRF_COOKIE', ''))
    return response

@login_required
def custom_logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('connexion')

### --- ESPACES SELON ROLES ---
@login_required
def patient_view(request):
    profile = request.user.profile
    try:
        patient_info = profile.patientinfo
    except PatientInfo.DoesNotExist:
        messages.error(request, "Profil patient introuvable.")
        return redirect('logout')
    appointments = Appointment.objects.filter(patient=patient_info).order_by('-date')
    journals = HealthJournal.objects.filter(patient=patient_info).order_by('-date')
    ordonnances = Ordonnance.objects.filter(patient=patient_info).order_by('-issued_at')
    return render(request, 'patient.html', {
        'appointments': appointments,
        'journals': journals,
        'ordonnances': ordonnances,
        'profile': profile,
        'patient_info': patient_info,
    })

@login_required
def medecin_view(request):
    try:
        logger.info(f"Tentative d'accès à l'espace médecin pour l'utilisateur: {request.user.username}")
        
        # Vérifier si l'utilisateur est authentifié
        if not request.user.is_authenticated:
            logger.error("Utilisateur non authentifié tentant d'accéder à l'espace médecin")
            messages.error(request, "Veuillez vous connecter pour accéder à votre espace.")
            return redirect('connexion')

        # Vérifier si l'utilisateur a un profil
        if not hasattr(request.user, 'profile'):
            logger.error(f"L'utilisateur {request.user.username} n'a pas de profil")
            messages.error(request, "Profil utilisateur introuvable. Veuillez contacter l'administrateur.")
            return redirect('connexion')
            
        profile = request.user.profile
        logger.info(f"Profil trouvé avec le rôle: {profile.role}")
        
        # Vérifier si le profil est celui d'un médecin
        if profile.role != 'medecin':
            logger.error(f"L'utilisateur {request.user.username} n'est pas un médecin (rôle: {profile.role})")
            messages.error(request, "Accès non autorisé. Cette page est réservée aux médecins.")
            return redirect('index')
            
        try:
            medecin_info = profile.medecininfo
            logger.info(f"Informations médecin trouvées pour: {request.user.username}")
            
            # Récupérer les rendez-vous du médecin
            today = timezone.now().date()
            
            # Rendez-vous à venir
            upcoming_appointments = Appointment.objects.filter(
                doctor=medecin_info,
                date__gte=today,
                is_cancelled=False
            ).order_by('date', 'time')[:5]  # Limiter aux 5 prochains rendez-vous
            logger.info(f"Nombre de rendez-vous à venir récupérés: {upcoming_appointments.count()}")
            
            # Récupérer les ordonnances du médecin
            ordonnances = Ordonnance.objects.filter(
                doctor=medecin_info
            ).order_by('-issued_at')[:5]  # Limiter aux 5 dernières ordonnances
            logger.info(f"Nombre d'ordonnances récupérées: {ordonnances.count()}")
            
            # Récupérer les statistiques avec gestion des erreurs
            try:
                total_patients = PatientInfo.objects.filter(
                    appointment__doctor=medecin_info
                ).distinct().count()
            except Exception as e:
                logger.error(f"Erreur lors du calcul du nombre total de patients: {str(e)}")
                total_patients = 0
            
            try:
                total_appointments_today = Appointment.objects.filter(
                    doctor=medecin_info,
                    date=today,
                    is_cancelled=False
                ).count()
            except Exception as e:
                logger.error(f"Erreur lors du calcul des rendez-vous du jour: {str(e)}")
                total_appointments_today = 0
            
            try:
                total_appointments_month = Appointment.objects.filter(
                    doctor=medecin_info,
                    date__month=today.month,
                    date__year=today.year,
                    is_cancelled=False
                ).count()
            except Exception as e:
                logger.error(f"Erreur lors du calcul des rendez-vous du mois: {str(e)}")
                total_appointments_month = 0
            
            context = {
                'medecin_info': medecin_info,
                'upcoming_appointments': upcoming_appointments,
                'ordonnances': ordonnances,
                'current_date': today,
                'stats': {
                    'total_patients': total_patients,
                    'appointments_today': total_appointments_today,
                    'appointments_month': total_appointments_month
                }
            }
            
            logger.info(f"Données récupérées avec succès pour le médecin: {request.user.username}")
            return render(request, 'medecin.html', context)
            
        except MedecinInfo.DoesNotExist:
            logger.error(f"MedecinInfo introuvable pour l'utilisateur {request.user.username}")
            messages.error(request, "Profil médecin incomplet. Veuillez contacter l'administrateur.")
            return redirect('index')
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données pour le médecin {request.user.username}: {str(e)}")
            messages.error(request, "Une erreur est survenue lors de la récupération de vos données. Veuillez réessayer.")
            return render(request, 'medecin.html', {'medecin_info': medecin_info})
            
    except Exception as e:
        logger.error(f"Erreur dans medecin_view pour l'utilisateur {request.user.username}: {str(e)}")
        messages.error(request, "Une erreur est survenue lors de l'accès à l'espace médecin. Veuillez réessayer.")
        return redirect('index')

@login_required
def pharmacien_view(request):
    if not hasattr(request.user, 'profile'):
        messages.error(request, "Vous n'avez pas de profil utilisateur.")
        return redirect('index')
    
    if request.user.profile.role != 'pharmacien':
        messages.error(request, "Accès non autorisé.")
        return redirect('index')
    
    try:
        pharmacien_info = request.user.profile.pharmacieninfo
    except PharmacienInfo.DoesNotExist:
        # Créer un nouveau PharmacienInfo si n'existe pas
        pharmacien_info = PharmacienInfo.objects.create(
            profile=request.user.profile,
            numero_pharmacie="",  # Valeur par défaut
            adresse_pharmacie=""  # Valeur par défaut
        )
        messages.info(request, "Veuillez compléter vos informations de pharmacien.")
    
    context = {
        'user_profile': request.user.profile,
        'pharmacien': pharmacien_info
    }
    return render(request, 'pharmacien.html', context)

### --- ACTIONS PATIENT ---
@login_required
def journal_sante(request):
    try:
        # Vérifier si l'utilisateur a un profil
        if not hasattr(request.user, 'profile'):
            messages.error(request, "Profil utilisateur introuvable.")
            logger.error(f"L'utilisateur {request.user.username} n'a pas de profil")
            return redirect('index')
        profile = request.user.profile
        # Vérifier si le profil est celui d'un patient
        if profile.role != 'patient':
            messages.error(request, "Accès non autorisé. Cette page est réservée aux patients.")
            logger.error(f"L'utilisateur {request.user.username} n'est pas un patient (rôle: {profile.role})")
            return redirect('index')
        try:
            patient_info = profile.patientinfo
        except PatientInfo.DoesNotExist:
            messages.error(request, "Profil patient introuvable.")
            logger.error(f"PatientInfo introuvable pour l'utilisateur {request.user.username}")
            return redirect('index')
        entries = HealthJournal.objects.filter(patient=patient_info).order_by('-date')
        if request.method == 'POST':
            form = HealthJournalForm(request.POST)
            if form.is_valid():
                entry = form.save(commit=False)
                entry.patient = patient_info
                entry.save()
                messages.success(request, 'Entrée ajoutée avec succès au journal de santé.')
                logger.info(f"Entrée ajoutée au journal de santé pour le patient {patient_info.profile.user.username}")
                return redirect('journal_sante')
            else:
                messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
                logger.error(f"Erreur de validation du formulaire: {form.errors}")
        else:
            form = HealthJournalForm()
        context = {
            'form': form,
            'entries': entries,
            'patient_info': patient_info
        }
        return render(request, 'journal_sante.html', context)
    except Exception as e:
        logger.error(f"Erreur dans journal_sante: {str(e)}")
        messages.error(request, "Une erreur est survenue lors de l'accès au journal de santé.")
        return redirect('patient_view')

@login_required
@csrf_protect
@ensure_csrf_cookie
def ordonnances_patient_view(request):
    try:
        # Vérifier si l'utilisateur a un profil
        if not hasattr(request.user, 'profile'):
            messages.error(request, "Profil utilisateur introuvable.")
            return redirect('index')
            
        profile = request.user.profile
        
        # Vérifier si le profil est celui d'un patient
        if profile.role != 'patient':
            messages.error(request, "Accès non autorisé. Cette page est réservée aux patients.")
            return redirect('index')
            
        try:
            patient_info = profile.patientinfo
        except PatientInfo.DoesNotExist:
            messages.error(request, "Profil patient introuvable.")
            return redirect('index')
            
        # Récupérer toutes les ordonnances du patient
        ordonnances = Ordonnance.objects.filter(
            patient=patient_info,
        ).order_by('-date_creation')
        
        context = {
            'ordonnances': ordonnances,
            'patient_info': patient_info
        }
        
        return render(request, 'ordonnances_patient.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans ordonnances_patient_view: {str(e)}")
        messages.error(request, "Une erreur est survenue lors de l'accès aux ordonnances.")
        return redirect('index')

@login_required
def mes_rdv(request):
    try:
        # Vérifier si l'utilisateur a un profil
        if not hasattr(request.user, 'profile'):
            messages.error(request, "Profil utilisateur introuvable.")
            logger.error(f"L'utilisateur {request.user.username} n'a pas de profil")
            return redirect('index')
            
        profile = request.user.profile
        
        # Vérifier si le profil est celui d'un patient
        if profile.role != 'patient':
            messages.error(request, "Accès non autorisé. Cette page est réservée aux patients.")
            logger.error(f"L'utilisateur {request.user.username} n'est pas un patient (rôle: {profile.role})")
            return redirect('index')
            
        try:
            patient_info = profile.patientinfo
        except PatientInfo.DoesNotExist:
            messages.error(request, "Profil patient introuvable.")
            logger.error(f"PatientInfo introuvable pour l'utilisateur {request.user.username}")
            return redirect('index')
            
        today = timezone.now().date()
        
        # Récupérer les rendez-vous à venir
        upcoming_appointments = Appointment.objects.filter(
            patient=patient_info, 
            date__gte=today,
            is_cancelled=False
        ).order_by('date', 'time')
        
        # Récupérer les rendez-vous passés
        past_appointments = Appointment.objects.filter(
            patient=patient_info, 
            date__lt=today,
            is_cancelled=False
        ).order_by('-date', '-time')
        
        # Si aucun rendez-vous n'existe, créer un rendez-vous de test
        if upcoming_appointments.count() == 0 and past_appointments.count() == 0:
            try:
                # Vérifier s'il existe un médecin
                medecin = MedecinInfo.objects.first()
                if not medecin:
                    # Créer un médecin de test si aucun n'existe
                    logger.info("Création d'un médecin de test")
                    # Créer l'utilisateur médecin
                    medecin_user = User.objects.create_user(
                        username='medecin.test@example.com',
                        email='medecin.test@example.com',
                        password='test123',
                        first_name='Jean',
                        last_name='Dupont'
                    )
                    # Créer le profil médecin
                    medecin_profile = Profile.objects.create(
                        user=medecin_user,
                        role='medecin',
                        date_naissance='1980-01-01',
                        adresse='123 rue du Test',
                        telephone='0123456789'
                    )
                    # Créer les infos médecin
                    medecin = MedecinInfo.objects.create(
                        profile=medecin_profile,
                        specialite='Médecine générale',
                        numero_ordre='12345'
                    )
                    logger.info(f"Médecin de test créé: {medecin_user.username}")

                # Créer un rendez-vous de test
                logger.info(f"Création d'un rendez-vous de test avec le médecin: {medecin.profile.user.username}")
                appointment_test = Appointment.objects.create(
                    patient=patient_info,
                    doctor=medecin,
                    date=today + timezone.timedelta(days=7),
                    time=timezone.now().time(),
                    reason="Consultation de routine"
                )
                logger.info(f"Rendez-vous de test créé avec succès pour: {request.user.username}")
                upcoming_appointments = Appointment.objects.filter(
                    patient=patient_info,
                    date__gte=today,
                    is_cancelled=False
                ).order_by('date', 'time')
            except Exception as e:
                logger.error(f"Erreur lors de la création du rendez-vous de test: {str(e)}")
                messages.error(request, f"Erreur lors de la création du rendez-vous de test: {str(e)}")
        
        context = {
            'upcoming_appointments': upcoming_appointments,
            'past_appointments': past_appointments,
            'patient_info': patient_info
        }
        return render(request, 'mes_rdv.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans mes_rdv: {str(e)}")
        messages.error(request, "Une erreur est survenue lors de l'accès aux rendez-vous.")
        return redirect('patient_view')

@login_required
def annuler_rdv(request, rdv_id):
    appointment = get_object_or_404(Appointment, id=rdv_id)
    appointment.is_cancelled = True
    appointment.save()
    messages.success(request, "Rendez-vous annulé avec succès.")
    return redirect('mes_rdv')

### --- ACTIONS MEDECIN & DOSSIERS ---
@login_required
def dossier_medical(request, patient_name=None):
    try:
        # Vérifier si l'utilisateur a un profil
        if not hasattr(request.user, 'profile'):
            messages.error(request, "Profil utilisateur introuvable.")
            return redirect('index')
            
        profile = request.user.profile
        
        # Si c'est un médecin qui accède à la vue
        if profile.role == 'medecin':
            try:
                medecin_info = profile.medecininfo
                
                if patient_name:
                    # Afficher le dossier d'un patient spécifique
                    try:
                        patient_user = User.objects.get(username=patient_name)
                        patient_info = patient_user.profile.patientinfo
                    except (User.DoesNotExist, Profile.DoesNotExist, PatientInfo.DoesNotExist):
                        messages.error(request, "Patient introuvable.")
                        return redirect('medecin_view')
                else:
                    # Afficher la liste des patients du médecin
                    patients = PatientInfo.objects.filter(
                        appointment__doctor=medecin_info
                    ).distinct()
                    
                    return render(request, 'dossiers_medicaux_liste.html', {
                        'patients': patients,
                        'medecin_info': medecin_info
                    })
                    
            except MedecinInfo.DoesNotExist:
                messages.error(request, "Profil médecin incomplet.")
                return redirect('index')
                
        # Si c'est un patient qui accède à son propre dossier
        elif profile.role == 'patient':
            try:
                patient_info = profile.patientinfo
            except PatientInfo.DoesNotExist:
                messages.error(request, "Profil patient introuvable.")
                return redirect('index')
        else:
            messages.error(request, "Accès non autorisé.")
            return redirect('index')
            
        # Récupérer le dossier médical
        try:
            medical_record = MedicalRecord.objects.filter(patient=patient_info).latest('created_at')
        except MedicalRecord.DoesNotExist:
            medical_record = None
            
        # Récupérer les ordonnances
        ordonnances = Ordonnance.objects.filter(patient=patient_info).order_by('-issued_at')
        
        context = {
            'medical_record': medical_record,
            'ordonnances': ordonnances,
            'patient_info': patient_info,
            'is_doctor_view': profile.role == 'medecin'
        }
        
        return render(request, 'dossier_medical.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans dossier_medical: {str(e)}")
        messages.error(request, "Une erreur est survenue lors de l'accès au dossier médical.")
        return redirect('index')

@login_required
def export_journal_pdf(request):
    try:
        profile = request.user.profile
        patient_info = profile.patientinfo
        journals = HealthJournal.objects.filter(patient=patient_info).order_by('-date')

        # Créer le nom du fichier
        filename = f"journal_sante_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Créer le document PDF
        doc = SimpleDocTemplate(response, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        elements.append(Paragraph("Journal de Santé", title_style))
        elements.append(Spacer(1, 20))

        # Informations du patient
        patient_info_style = ParagraphStyle(
            'PatientInfo',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20
        )
        elements.append(Paragraph(f"Patient: {request.user.get_full_name()}", patient_info_style))
        elements.append(Paragraph(f"Date de naissance: {profile.date_naissance}", patient_info_style))
        elements.append(Spacer(1, 20))

        # En-tête du tableau
        data = [['Date', 'Tension Artérielle', 'Glycémie', 'Notes']]
        
        # Données du journal
        for journal in journals:
            data.append([
                journal.date.strftime('%d/%m/%Y'),
                f"{journal.tension_art} mmHg",
                f"{journal.glycemie} mg/dL",
                journal.notes or ''
            ])

        # Créer le tableau
        table = Table(data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(table)
        
        # Pied de page
        elements.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey
        )
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", footer_style))

        # Construire le PDF
        doc.build(elements)
        return response

    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF: {str(e)}")
        messages.error(request, "Une erreur est survenue lors de la génération du PDF.")
        return redirect('journal_sante')

@login_required
def export_ordonnance(request, ordonnance_id):
    try:
        ordonnance = get_object_or_404(Ordonnance, id=ordonnance_id)
        
        # Vérifier que l'ordonnance appartient bien au patient connecté
        if ordonnance.patient.profile.user != request.user:
            messages.error(request, "Vous n'avez pas accès à cette ordonnance.")
            return redirect('ordonnances_patient')
        
        # Créer le nom du fichier
        filename = f"ordonnance_{ordonnance.issued_at.strftime('%Y%m%d')}.pdf"
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Créer le document PDF
        doc = SimpleDocTemplate(response, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        elements.append(Paragraph("Ordonnance Médicale", title_style))
        elements.append(Spacer(1, 20))
        
        # Informations du médecin
        doctor_info_style = ParagraphStyle(
            'DoctorInfo',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20
        )
        elements.append(Paragraph(f"Médecin: Dr. {ordonnance.doctor.profile.user.get_full_name()}", doctor_info_style))
        elements.append(Paragraph(f"Spécialité: {ordonnance.doctor.specialite}", doctor_info_style))
        elements.append(Spacer(1, 20))
        
        # Informations du patient
        patient_info_style = ParagraphStyle(
            'PatientInfo',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20
        )
        elements.append(Paragraph(f"Patient: {ordonnance.patient.profile.user.get_full_name()}", patient_info_style))
        elements.append(Paragraph(f"Date: {ordonnance.issued_at.strftime('%d/%m/%Y')}", patient_info_style))
        elements.append(Spacer(1, 20))
        
        # Contenu de l'ordonnance
        content_style = ParagraphStyle(
            'Content',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Courier',
            spaceAfter=20
        )
        elements.append(Paragraph("Prescriptions:", content_style))
        elements.append(Paragraph(ordonnance.content, content_style))
        
        # Pied de page
        elements.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey
        )
        elements.append(Paragraph(f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", footer_style))
        
        # Construire le PDF
        doc.build(elements)
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF: {str(e)}")
        messages.error(request, "Une erreur est survenue lors de la génération du PDF.")
        return redirect('ordonnances_patient')

@login_required
def export_ordonnance_pdf(request, ordonnance_id):
    try:
        ordonnance = get_object_or_404(Ordonnance, id=ordonnance_id)
        
        # Vérifier que l'ordonnance appartient bien au patient connecté
        if ordonnance.patient.profile.user != request.user:
            messages.error(request, "Vous n'avez pas accès à cette ordonnance.")
            return redirect('ordonnances_patient_view')
        
        # Créer le nom du fichier
        filename = f"ordonnance_{ordonnance.issued_at.strftime('%Y%m%d')}.pdf"
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Créer le document PDF
        doc = SimpleDocTemplate(response, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        elements.append(Paragraph("Ordonnance Médicale", title_style))
        elements.append(Spacer(1, 20))
        
        # Informations du médecin
        doctor_info_style = ParagraphStyle(
            'DoctorInfo',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20
        )
        elements.append(Paragraph(f"Médecin: Dr. {ordonnance.doctor.profile.user.get_full_name()}", doctor_info_style))
        elements.append(Paragraph(f"Spécialité: {ordonnance.doctor.specialite}", doctor_info_style))
        elements.append(Spacer(1, 20))
        
        # Informations du patient
        patient_info_style = ParagraphStyle(
            'PatientInfo',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20
        )
        elements.append(Paragraph(f"Patient: {ordonnance.patient.profile.user.get_full_name()}", patient_info_style))
        elements.append(Paragraph(f"Date: {ordonnance.issued_at.strftime('%d/%m/%Y')}", patient_info_style))
        elements.append(Spacer(1, 20))
        
        # Contenu de l'ordonnance
        content_style = ParagraphStyle(
            'Content',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Courier',
            spaceAfter=20
        )
        elements.append(Paragraph("Prescriptions:", content_style))
        elements.append(Paragraph(ordonnance.content, content_style))
        
        # Pied de page
        elements.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey
        )
        elements.append(Paragraph(f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", footer_style))
        
        # Construire le PDF
        doc.build(elements)
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF: {str(e)}")
        messages.error(request, "Une erreur est survenue lors de la génération du PDF.")
        return redirect('ordonnances_patient_view')

@login_required
def create_medical_record(request, patient_id):
    try:
        # Vérifier si l'utilisateur a un profil
        if not hasattr(request.user, 'profile'):
            messages.error(request, "Profil utilisateur introuvable.")
            return redirect('index')
            
        profile = request.user.profile
        
        # Vérifier si le profil est celui d'un médecin
        if profile.role != 'medecin':
            messages.error(request, "Accès non autorisé. Cette page est réservée aux médecins.")
            return redirect('index')
            
        try:
            medecin_info = profile.medecininfo
            patient_info = PatientInfo.objects.get(id=patient_id)
        except (MedecinInfo.DoesNotExist, PatientInfo.DoesNotExist):
            messages.error(request, "Profil médecin ou patient introuvable.")
            return redirect('index')
            
        if request.method == 'POST':
            form = MedicalRecordForm(request.POST)
            if form.is_valid():
                medical_record = form.save(commit=False)
                medical_record.doctor = medecin_info
                medical_record.patient = patient_info
                medical_record.save()
                messages.success(request, "Dossier médical créé avec succès.")
                return redirect('dossier_medical_patient', patient_name=patient_info.profile.user.username)
            else:
                messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
        else:
            form = MedicalRecordForm()
        
        context = {
            'form': form,
            'patient_info': patient_info,
            'medecin_info': medecin_info
        }
        
        return render(request, 'create_medical_record.html', context)
        
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la création du dossier médical: {str(e)}")
        return redirect('index')

@login_required
def medecin_rdv(request):
    if request.user.profile.role != 'medecin':
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('index')
    
    today = timezone.now().date()
    medecin = request.user.profile.medecininfo
    
    # Rendez-vous à venir
    upcoming_appointments = Appointment.objects.filter(
        doctor=medecin,
        date__gte=today,
        is_cancelled=False
    ).order_by('date', 'time')
    
    # Rendez-vous passés
    past_appointments = Appointment.objects.filter(
        doctor=medecin,
        date__lt=today,
        is_cancelled=False
    ).order_by('-date', '-time')
    
    context = {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
    }
    
    return render(request, 'medecin_rdv.html', context)

@login_required
def accept_appointment(request, appointment_id):
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Vérifier que le médecin connecté est bien le médecin du rendez-vous
        if appointment.doctor != request.user.profile.medecininfo:
            messages.error(request, "Vous n'êtes pas autorisé à modifier ce rendez-vous.")
            return redirect('agenda_view')
        
        # Mettre à jour le statut du rendez-vous
        appointment.status = 'à venir'
        appointment.save()
        
        messages.success(request, "Rendez-vous accepté avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de l'acceptation du rendez-vous: {str(e)}")
        messages.error(request, "Une erreur est survenue lors de l'acceptation du rendez-vous.")
    
    return redirect('agenda_view')

@login_required
def reject_appointment(request, appointment_id):
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Vérifier que le médecin connecté est bien le médecin du rendez-vous
        if appointment.doctor != request.user.profile.medecininfo:
            messages.error(request, "Vous n'êtes pas autorisé à modifier ce rendez-vous.")
            return redirect('agenda_view')
        
        # Marquer le rendez-vous comme annulé
        appointment.is_cancelled = True
        appointment.save()
        
        messages.success(request, "Rendez-vous refusé avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors du rejet du rendez-vous: {str(e)}")
        messages.error(request, "Une erreur est survenue lors du rejet du rendez-vous.")
    
    return redirect('agenda_view')

@login_required
def agenda_data(request):
    try:
        # Vérifier si l'utilisateur a un profil
        if not hasattr(request.user, 'profile'):
            return JsonResponse({'error': 'Profil utilisateur introuvable'}, status=400)
            
        profile = request.user.profile
        
        # Vérifier si le profil est celui d'un médecin
        if profile.role != 'medecin':
            return JsonResponse({'error': 'Accès non autorisé'}, status=403)
            
        try:
            medecin_info = profile.medecininfo
        except MedecinInfo.DoesNotExist:
            return JsonResponse({'error': 'Profil médecin introuvable'}, status=400)
            
        # Récupérer les rendez-vous du médecin
        today = timezone.now().date()
        rendezvous = Appointment.objects.filter(
            doctor=medecin_info,
            date__gte=today,
            is_cancelled=False
        ).order_by('date', 'time')
        
        # Formater les données pour le frontend
        rendezvous_data = [{
            'patient_name': rdv.patient.profile.user.get_full_name(),
            'date': rdv.date.strftime('%Y-%m-%d'),
            'time': rdv.time.strftime('%H:%M'),
            'reason': rdv.reason,
            'notes': rdv.notes
        } for rdv in rendezvous]
        
        return JsonResponse({'rendezvous': rendezvous_data})
        
    except Exception as e:
        logger.error(f"Erreur dans agenda_data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def admin_appointments_view(request):
    try:
        # Récupérer tous les rendez-vous
        today = timezone.now().date()
        upcoming_appointments = Appointment.objects.filter(
            date__gte=today,
            is_cancelled=False
        ).select_related('patient__profile__user', 'doctor__profile__user').order_by('date', 'time')
        
        past_appointments = Appointment.objects.filter(
            date__lt=today,
            is_cancelled=False
        ).select_related('patient__profile__user', 'doctor__profile__user').order_by('-date', '-time')[:50]
        
        context = {
            'upcoming_appointments': upcoming_appointments,
            'past_appointments': past_appointments,
        }
        
        return render(request, 'admin_appointments.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors de l'accès aux rendez-vous: {str(e)}")
        return redirect('admin')

@login_required
@user_passes_test(is_admin)
def admin_schedules_view(request):
    try:
        doctors = MedecinInfo.objects.select_related('profile__user').all()
        
        if request.method == 'POST':
            doctor_id = request.POST.get('doctor_id')
            day_of_week = request.POST.get('day_of_week')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            
            # Ici vous pouvez ajouter la logique pour sauvegarder les horaires
            messages.success(request, "Horaires mis à jour avec succès")
            return redirect('admin_schedules')
            
        context = {
            'doctors': doctors,
            'days_of_week': [
                'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 
                'Vendredi', 'Samedi', 'Dimanche'
            ]
        }
        
        return render(request, 'admin_schedules.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors de l'accès aux horaires: {str(e)}")
        return redirect('admin')

@login_required
@user_passes_test(is_admin)
def admin_appointment_stats_view(request):
    try:
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        
        # Statistiques mensuelles
        monthly_stats = {
            'total': Appointment.objects.filter(
                date__year=today.year,
                date__month=today.month
            ).count(),
            'completed': Appointment.objects.filter(
                date__year=today.year,
                date__month=today.month,
                date__lt=today
            ).count(),
            'cancelled': Appointment.objects.filter(
                date__year=today.year,
                date__month=today.month,
                is_cancelled=True
            ).count(),
        }
        
        # Statistiques par médecin
        doctor_stats = MedecinInfo.objects.annotate(
            appointment_count=Count('appointment', filter=Q(
                appointment__date__gte=start_of_month
            ))
        ).select_related('profile__user').order_by('-appointment_count')
        
        # Statistiques par jour de la semaine
        weekday_stats = Appointment.objects.filter(
            date__gte=start_of_month
        ).annotate(
            weekday=ExtractWeekDay('date')
        ).values('weekday').annotate(
            count=Count('id')
        ).order_by('weekday')
        
        context = {
            'monthly_stats': monthly_stats,
            'doctor_stats': doctor_stats,
            'weekday_stats': weekday_stats,
        }
        
        return render(request, 'admin_appointment_stats.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors de l'accès aux statistiques: {str(e)}")
        return redirect('admin')

@login_required
@user_passes_test(is_admin)
def admin_view_appointment(request, appointment_id):
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        data = {
            'id': appointment.id,
            'patient': appointment.patient.profile.user.get_full_name(),
            'doctor': f"Dr. {appointment.doctor.profile.user.get_full_name()}",
            'date': appointment.date.strftime('%Y-%m-%d'),
            'time': appointment.time.strftime('%H:%M'),
            'reason': appointment.reason,
            'notes': appointment.notes or '',
            'status': 'Annulé' if appointment.is_cancelled else 'À venir' if appointment.date >= timezone.now().date() else 'Terminé'
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@user_passes_test(is_admin)
def admin_edit_appointment(request, appointment_id):
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        if request.method == 'POST':
            date = request.POST.get('date')
            time = request.POST.get('time')
            reason = request.POST.get('reason')
            notes = request.POST.get('notes')
            
            if date and time:
                appointment.date = date
                appointment.time = time
                appointment.reason = reason
                appointment.notes = notes
                appointment.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Rendez-vous modifié avec succès'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Date et heure requises'
                }, status=400)
                
        return JsonResponse({
            'id': appointment.id,
            'patient': appointment.patient.profile.user.get_full_name(),
            'doctor': f"Dr. {appointment.doctor.profile.user.get_full_name()}",
            'date': appointment.date.strftime('%Y-%m-%d'),
            'time': appointment.time.strftime('%H:%M'),
            'reason': appointment.reason,
            'notes': appointment.notes or ''
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@user_passes_test(is_admin)
def admin_cancel_appointment(request, appointment_id):
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        appointment.is_cancelled = True
        appointment.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Rendez-vous annulé avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@user_passes_test(is_admin)
def admin_filter_appointments(request):
    try:
        filter_type = request.GET.get('type')
        date = request.GET.get('date')
        period = request.GET.get('period')
        
        if filter_type == 'patients':
            # Récupérer la liste des patients
            patients = User.objects.filter(profile__role='patient')
            data = [{
                'id': patient.id,
                'name': f"{patient.first_name} {patient.last_name}",
                'email': patient.email,
                'phone': patient.profile.telephone if hasattr(patient, 'profile') else ''
            } for patient in patients]
            return JsonResponse({'patients': data})
            
        elif filter_type == 'doctors':
            # Récupérer la liste des médecins
            doctors = User.objects.filter(profile__role='medecin')
            data = [{
                'id': doctor.id,
                'name': f"{doctor.first_name} {doctor.last_name}",
                'speciality': doctor.profile.medecininfo.specialite if hasattr(doctor.profile, 'medecininfo') else '',
                'email': doctor.email
            } for doctor in doctors]
            return JsonResponse({'doctors': data})
            
        elif filter_type == 'revenue':
            # Calculer les revenus du mois
            current_month = timezone.now().month
            current_year = timezone.now().year
            
            appointments = Appointment.objects.filter(
                date__year=current_year,
                date__month=current_month,
                is_cancelled=False
            )
            
            total_appointments = appointments.count()
            total_revenue = total_appointments * 50  # 50€ par rendez-vous
            
            # Calculer la répartition par service
            services = {}
            for apt in appointments:
                service = apt.reason or 'Consultation générale'
                if service not in services:
                    services[service] = {'count': 0, 'amount': 0}
                services[service]['count'] += 1
                services[service]['amount'] += 50
            
            # Calculer les pourcentages
            services_data = []
            for service, data in services.items():
                percentage = (data['amount'] / total_revenue * 100) if total_revenue > 0 else 0
                services_data.append({
                    'name': service,
                    'amount': data['amount'],
                    'percentage': round(percentage, 1)
                })
            
            return JsonResponse({
                'total': total_revenue,
                'appointments_count': total_appointments,
                'services': services_data
            })
            
        elif filter_type == 'invoices':
            # Simuler des données de factures
            invoices = [{
                'id': i,
                'number': f'FACT-{2024}0{i}',
                'patient': f'Patient {i}',
                'date': (timezone.now() - timedelta(days=i)).strftime('%d/%m/%Y'),
                'amount': random.randint(50, 500),
                'status': random.choice(['Payée', 'En attente', 'Retard'])
            } for i in range(1, 11)]
            return JsonResponse({'invoices': invoices})
            
        elif filter_type == 'payments':
            # Simuler des données de paiements
            payments = [{
                'date': (timezone.now() - timedelta(days=i)).strftime('%d/%m/%Y'),
                'patient': f'Patient {i}',
                'amount': random.randint(50, 500),
                'method': random.choice(['Carte', 'Espèces', 'Virement']),
                'status': random.choice(['Validé', 'En attente', 'Refusé'])
            } for i in range(1, 11)]
            return JsonResponse({'payments': payments})
            
        elif filter_type == 'monthly_stats':
            # Calculer les statistiques mensuelles
            current_month = timezone.now().month
            current_year = timezone.now().year
            appointments = Appointment.objects.filter(
                date__year=current_year,
                date__month=current_month
            )
            
            services = {}
            total_revenue = 0
            for apt in appointments:
                service = apt.reason or 'Consultation'
                if service not in services:
                    services[service] = {'count': 0, 'revenue': 0}
                services[service]['count'] += 1
                # Calculer le revenu (50€ par défaut si non spécifié)
                revenue = getattr(apt, 'cost', 50)
                services[service]['revenue'] += revenue
                total_revenue += revenue
            
            services_data = [{
                'name': service,
                'count': data['count'],
                'revenue': data['revenue']
            } for service, data in services.items()]
            
            return JsonResponse({
                'appointments_count': appointments.count(),
                'total_revenue': total_revenue,
                'services': services_data
            })
            
        elif filter_type == 'trends':
            # Générer des données de tendances sur 6 mois
            months = []
            appointments_data = []
            revenue_data = []
            
            for i in range(6):
                date = timezone.now() - timedelta(days=30*i)
                months.insert(0, date.strftime('%B %Y'))
                appointments = Appointment.objects.filter(
                    date__month=date.month,
                    date__year=date.year
                )
                count = appointments.count()
                # Calculer le revenu total pour le mois (50€ par défaut par rendez-vous)
                revenue = sum(getattr(apt, 'cost', 50) for apt in appointments)
                
                appointments_data.insert(0, count)
                revenue_data.insert(0, revenue)
            
            return JsonResponse({
                'appointments_data': {
                    'labels': months,
                    'values': appointments_data
                },
                'revenue_data': {
                    'labels': months,
                    'values': revenue_data
                }
            })
            
        elif filter_type == 'service_performance':
            # Calculer les performances réelles des services
            current_month = timezone.now().month
            current_year = timezone.now().year
            appointments = Appointment.objects.filter(
                date__year=current_year,
                date__month=current_month
            )
            
            services = {}
            for apt in appointments:
                service = apt.reason or 'Consultation générale'
                if service not in services:
                    services[service] = {
                        'appointments': 0,
                        'revenue': 0,
                        'satisfaction': random.randint(85, 98),  # Simulé pour l'exemple
                        'performance': 0
                    }
                services[service]['appointments'] += 1
                services[service]['revenue'] += getattr(apt, 'cost', 50)
            
            # Calculer le score de performance (basé sur le nombre de rendez-vous et les revenus)
            max_appointments = max((s['appointments'] for s in services.values()), default=1)
            max_revenue = max((s['revenue'] for s in services.values()), default=1)
            
            services_data = []
            for name, data in services.items():
                # Calculer un score de performance normalisé
                performance = (
                    (data['appointments'] / max_appointments) * 50 +  # 50% basé sur le nombre de rendez-vous
                    (data['revenue'] / max_revenue) * 50  # 50% basé sur les revenus
                )
                services_data.append({
                    'name': name,
                    'appointments': data['appointments'],
                    'revenue': data['revenue'],
                    'satisfaction': data['satisfaction'],
                    'performance': round(performance)
                })
            
            return JsonResponse({'services': services_data})
            
        elif filter_type == 'satisfaction':
            # Calculer la satisfaction réelle basée sur les rendez-vous terminés
            current_month = timezone.now().month
            current_year = timezone.now().year
            completed_appointments = Appointment.objects.filter(
                date__year=current_year,
                date__month=current_month,
                status='terminé'
            ).count()
            
            # Pour l'exemple, nous simulons les notes
            total_reviews = completed_appointments
            reviews = []
            total = 0
            
            for i in range(5, 0, -1):
                # Distribuer les notes de manière réaliste
                if i >= 4:  # Notes 4-5 étoiles
                    count = int(total_reviews * random.uniform(0.3, 0.4))
                elif i == 3:  # Notes 3 étoiles
                    count = int(total_reviews * random.uniform(0.15, 0.2))
                else:  # Notes 1-2 étoiles
                    count = int(total_reviews * random.uniform(0.05, 0.1))
                
                total += count
                reviews.append({
                    'rating': i,
                    'count': count,
                    'percentage': 0
                })
            
            # Ajuster pour que le total corresponde au nombre de rendez-vous
            if total != total_reviews:
                diff = total_reviews - total
                reviews[0]['count'] += diff
            
            # Calculer les pourcentages
            for review in reviews:
                review['percentage'] = round((review['count'] / total_reviews) * 100, 1) if total_reviews > 0 else 0
            
            # Calculer la satisfaction globale (moyenne pondérée)
            global_satisfaction = round(sum(r['rating'] * r['count'] for r in reviews) / total_reviews * 20, 1) if total_reviews > 0 else 0
            
            return JsonResponse({
                'global_satisfaction': global_satisfaction,
                'total_reviews': total_reviews,
                'reviews': reviews
            })
        
        elif date == 'today':
            # Récupérer les rendez-vous d'aujourd'hui
            today = timezone.now().date()
            appointments = Appointment.objects.filter(
                date=today,
                is_cancelled=False
            ).select_related('patient__profile__user', 'doctor__profile__user')
            
            appointments_data = [{
                'id': apt.id,
                'time': apt.time.strftime('%H:%M'),
                'patient': apt.patient.profile.user.get_full_name(),
                'doctor': apt.doctor.profile.user.get_full_name(),
                'reason': apt.reason,
                'status': 'En cours' if apt.time <= timezone.now().time() else 'À venir'
            } for apt in appointments]
            
            return JsonResponse({'appointments': appointments_data})
            
    except Exception as e:
        logger.error(f"Erreur dans admin_filter_appointments: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def create_invoice(request):
    if request.method == 'POST':
        try:
            # Créer une nouvelle facture
            # Note: Ceci est un exemple, vous devrez adapter selon votre modèle de données
            patient_id = request.POST.get('patient')
            service = request.POST.get('service')
            montant = request.POST.get('montant')
            description = request.POST.get('description')
            
            # Ici, vous créeriez la facture dans votre base de données
            
            return JsonResponse({
                'success': True,
                'message': 'Facture créée avec succès'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@login_required
@user_passes_test(is_admin)
def export_reports(request):
    try:
        # Récupérer les paramètres
        date_range = request.GET.get('dateRange', 'month')
        format = request.GET.get('format', 'pdf')
        
        # Générer le rapport selon les paramètres
        # Note: Ceci est un exemple, vous devrez implémenter la génération réelle des rapports
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_{date_range}.{format}"'
        
        # Ici, vous généreriez le contenu du rapport
        
        return response
    except Exception as e:
        messages.error(request, f"Erreur lors de l'export: {str(e)}")
        return redirect('admin')

@login_required
@user_passes_test(is_admin)
def download_archive(request, archive_id):
    try:
        # Récupérer l'archive
        # Note: Ceci est un exemple, vous devrez adapter selon votre système d'archivage
        
        response = HttpResponse(content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="archive_{archive_id}.zip"'
        
        # Ici, vous ajouteriez le contenu de l'archive
        
        return response
    except Exception as e:
        messages.error(request, f"Erreur lors du téléchargement: {str(e)}")
        return redirect('admin')

@login_required
@user_passes_test(is_admin)
def view_patient_details(request, patient_id):
    try:
        patient = User.objects.get(id=patient_id, groups__name='Patient')
        appointments = Appointment.objects.filter(patient=patient).order_by('-date')[:5]
        
        data = {
            'name': f"{patient.first_name} {patient.last_name}",
            'email': patient.email,
            'phone': patient.profile.phone if hasattr(patient, 'profile') else '',
            'birth_date': patient.profile.birth_date.strftime('%d/%m/%Y') if hasattr(patient, 'profile') and patient.profile.birth_date else '',
            'address': patient.profile.address if hasattr(patient, 'profile') else '',
            'appointments': [{
                'date': apt.date.strftime('%d/%m/%Y'),
                'doctor': f"{apt.doctor.first_name} {apt.doctor.last_name}",
                'reason': apt.reason
            } for apt in appointments]
        }
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Patient non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def view_doctor_details(request, doctor_id):
    try:
        doctor = User.objects.get(id=doctor_id, groups__name='Médecin')
        today = timezone.now().date()
        appointments = Appointment.objects.filter(doctor=doctor, date=today).order_by('time')
        
        data = {
            'name': f"{doctor.first_name} {doctor.last_name}",
            'speciality': doctor.profile.speciality if hasattr(doctor, 'profile') else '',
            'email': doctor.email,
            'phone': doctor.profile.phone if hasattr(doctor, 'profile') else '',
            'appointments': [{
                'time': apt.time.strftime('%H:%M'),
                'patient': f"{apt.patient.first_name} {apt.patient.last_name}",
                'reason': apt.reason
            } for apt in appointments]
        }
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Médecin non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def view_appointment_details(request, appointment_id):
    try:
        apt = Appointment.objects.get(id=appointment_id)
        data = {
            'id': apt.id,
            'patient': f"{apt.patient.first_name} {apt.patient.last_name}",
            'doctor': f"{apt.doctor.first_name} {apt.doctor.last_name}",
            'date': apt.date.strftime('%d/%m/%Y'),
            'time': apt.time.strftime('%H:%M'),
            'reason': apt.reason,
            'status': apt.status,
            'notes': apt.notes
        }
        return JsonResponse(data)
    except Appointment.DoesNotExist:
        return JsonResponse({'error': 'Rendez-vous non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
            elif hasattr(user, 'doctor'):
                return redirect('doctor_dashboard')
            elif hasattr(user, 'patient'):
                return redirect('patient_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "Vous n'avez pas les permissions d'administrateur.")
        return redirect('connexion')
    
    # Statistiques pour le tableau de bord
    today = timezone.now().date()
    current_month = timezone.now().month
    
    try:
        stats = {
            'total_patients': PatientInfo.objects.count(),
            'total_doctors': MedecinInfo.objects.count(),
            'appointments_today': Appointment.objects.filter(date=today).count(),
            'total_revenue': Appointment.objects.filter(
                date__month=current_month,
                status='terminé'
            ).count() * 50  # exemple de calcul de revenus
        }
        
        context = {
            'stats': stats,
            'user': request.user
        }
        
        return render(request, 'admin.html', context)
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement du tableau de bord: {str(e)}")
        logger.error(f"Erreur dans admin_dashboard: {str(e)}")
        return redirect('index')

@login_required
def doctor_dashboard(request):
    if not hasattr(request.user, 'doctor'):
        return redirect('login')
    return render(request, 'doctor.html')

@login_required
def patient_dashboard(request):
    if not hasattr(request.user, 'patient'):
        return redirect('login')
    return render(request, 'patient.html')

### --- GESTION DES RESSOURCES ---
@login_required
@user_passes_test(is_admin)
def gestion_salles_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_room':
            numero = request.POST.get('numero')
            type_salle = request.POST.get('type_salle')
            capacite = request.POST.get('capacite')
            equipements = request.POST.get('equipements')
            
            Room.objects.create(
                numero=numero,
                type=type_salle,
                capacite=capacite,
                equipements=equipements
            )
            messages.success(request, "Salle ajoutée avec succès")
            
        elif action == 'edit_room':
            room_id = request.POST.get('room_id')
            room = Room.objects.get(id=room_id)
            room.numero = request.POST.get('numero')
            room.type = request.POST.get('type_salle')
            room.capacite = request.POST.get('capacite')
            room.equipements = request.POST.get('equipements')
            room.save()
            messages.success(request, "Salle modifiée avec succès")
            
        elif action == 'delete_room':
            room_id = request.POST.get('room_id')
            Room.objects.get(id=room_id).delete()
            messages.success(request, "Salle supprimée avec succès")
    
    salles = Room.objects.all().order_by('numero')
    context = {
        'salles': salles,
        'types_salles': [t[0] for t in Room.ROOM_TYPES]
    }
    return render(request, 'gestion_salles.html', context)

@login_required
@user_passes_test(is_admin)
def equipements_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_equipment':
            nom = request.POST.get('nom')
            type_equip = request.POST.get('type_equip')
            salle_id = request.POST.get('salle')
            description = request.POST.get('description')
            
            Equipment.objects.create(
                nom=nom,
                type=type_equip,
                salle_id=salle_id if salle_id else None,
                description=description
            )
            messages.success(request, "Équipement ajouté avec succès")
            
        elif action == 'edit_equipment':
            equip_id = request.POST.get('equip_id')
            equipment = Equipment.objects.get(id=equip_id)
            equipment.nom = request.POST.get('nom')
            equipment.type = request.POST.get('type_equip')
            equipment.salle_id = request.POST.get('salle')
            equipment.description = request.POST.get('description')
            equipment.save()
            messages.success(request, "Équipement modifié avec succès")
            
        elif action == 'delete_equipment':
            equip_id = request.POST.get('equip_id')
            Equipment.objects.get(id=equip_id).delete()
            messages.success(request, "Équipement supprimé avec succès")
    
    equipements = Equipment.objects.all().select_related('salle')
    salles = Room.objects.all()
    context = {
        'equipements': equipements,
        'salles': salles,
        'types_equipements': [t[0] for t in Equipment.EQUIPMENT_TYPES]
    }
    return render(request, 'equipements.html', context)

@login_required
@user_passes_test(is_admin)
def planning_salles_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_reservation':
            salle_id = request.POST.get('salle')
            date = request.POST.get('date')
            heure_debut = request.POST.get('heure_debut')
            heure_fin = request.POST.get('heure_fin')
            motif = request.POST.get('motif')
            
            RoomSchedule.objects.create(
                salle_id=salle_id,
                date=date,
                heure_debut=heure_debut,
                heure_fin=heure_fin,
                motif=motif
            )
            messages.success(request, "Réservation ajoutée avec succès")
            
        elif action == 'cancel_reservation':
            reservation_id = request.POST.get('reservation_id')
            reservation = RoomSchedule.objects.get(id=reservation_id)
            reservation.is_cancelled = True
            reservation.save()
            messages.success(request, "Réservation annulée avec succès")
    
    reservations = RoomSchedule.objects.filter(
        is_cancelled=False,
        date__gte=timezone.now().date()
    ).select_related('salle')
    salles = Room.objects.filter(status='Disponible')
    
    context = {
        'reservations': reservations,
        'salles': salles
    }
    return render(request, 'planning_salles.html', context)

@login_required
@user_passes_test(is_admin)
def maintenance_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_maintenance':
            equipement_id = request.POST.get('equipement')
            type_maintenance = request.POST.get('type_maintenance')
            description = request.POST.get('description')
            date_prevue = request.POST.get('date_prevue')
            
            Maintenance.objects.create(
                equipement_id=equipement_id,
                type=type_maintenance,
                description=description,
                date_prevue=date_prevue
            )
            
            # Mettre à jour le statut de l'équipement
            equipment = Equipment.objects.get(id=equipement_id)
            equipment.status = 'En maintenance'
            equipment.save()
            
            messages.success(request, "Maintenance planifiée avec succès")
            
        elif action == 'complete_maintenance':
            maintenance_id = request.POST.get('maintenance_id')
            maintenance = Maintenance.objects.get(id=maintenance_id)
            maintenance.status = 'Terminée'
            maintenance.date_fin = timezone.now()
            maintenance.save()
            
            # Mettre à jour le statut de l'équipement
            equipment = maintenance.equipement
            equipment.status = 'Opérationnel'
            equipment.save()
            
            messages.success(request, "Maintenance terminée avec succès")
    
    maintenances = Maintenance.objects.all().select_related('equipement')
    equipements = Equipment.objects.all()
    
    context = {
        'maintenances': maintenances,
        'equipements': equipements,
        'types_maintenance': [t[0] for t in Maintenance.MAINTENANCE_TYPES]
    }
    return render(request, 'maintenance.html', context)

@login_required
@user_passes_test(is_admin)
def get_room_details(request, room_id):
    try:
        room = Room.objects.get(id=room_id)
        data = {
            'id': room.id,
            'numero': room.numero,
            'type': room.type,
            'status': room.status,
            'capacite': room.capacite,
            'equipements': room.equipements
        }
        return JsonResponse(data)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Salle non trouvée'}, status=404)

@login_required
@user_passes_test(is_admin)
def get_equipment_details(request, equipment_id):
    try:
        equipment = Equipment.objects.get(id=equipment_id)
        data = {
            'id': equipment.id,
            'nom': equipment.nom,
            'type': equipment.type,
            'status': equipment.status,
            'salle': equipment.salle.numero if equipment.salle else None,
            'description': equipment.description
        }
        return JsonResponse(data)
    except Equipment.DoesNotExist:
        return JsonResponse({'error': 'Équipement non trouvé'}, status=404)

@login_required
def medecin_dashboard(request):
    try:
        # Vérifier si l'utilisateur a un profil
        if not hasattr(request.user, 'profile'):
            logger.error(f"L'utilisateur {request.user.username} n'a pas de profil")
            messages.error(request, "Profil utilisateur introuvable.")
            return redirect('connexion')
            
        profile = request.user.profile
        
        # Vérifier si le profil est celui d'un médecin
        if profile.role != 'medecin':
            logger.error(f"L'utilisateur {request.user.username} n'est pas un médecin (rôle: {profile.role})")
            messages.error(request, "Accès non autorisé. Cette page est réservée aux médecins.")
            return redirect('index')
            
        try:
            # Vérifier si le profil médecin existe
            medecin_info = profile.medecininfo
            logger.info(f"Redirection vers l'espace médecin pour: {request.user.username}")
            return redirect('medecin_view')
        except MedecinInfo.DoesNotExist:
            logger.error(f"MedecinInfo introuvable pour l'utilisateur {request.user.username}")
            messages.error(request, "Profil médecin incomplet. Veuillez contacter l'administrateur.")
            return redirect('index')
            
    except Exception as e:
        logger.error(f"Erreur dans medecin_dashboard: {str(e)}")
        messages.error(request, "Une erreur est survenue lors de l'accès à l'espace médecin.")
        return redirect('index')

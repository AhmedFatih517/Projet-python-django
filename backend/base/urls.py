from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('connexion/', views.connexion_view, name='connexion'),
    path('inscription/', views.inscription_view, name='inscription'),
    path('logout/', views.custom_logout_view, name='logout'),
    
    # URLs pour les différents tableaux de bord
    path('admin/', views.admin_view, name='admin'),
    path('patient/', views.patient_view, name='patient_view'),
    path('medecin/', views.medecin_view, name='medecin_view'),
    path('medecin/dashboard/', views.medecin_dashboard, name='medecin_dashboard'),
    path('pharmacien/', views.pharmacien_view, name='pharmacien_view'),
    
    # URLs pour les rendez-vous
    path('agenda/', views.agenda_view, name='agenda_view'),
    path('mes-rdv/', views.mes_rdv, name='mes_rdv'),
    path('rendezvous/', views.rendezvous_view, name='rendezvous'),
    path('annuler-rdv/<int:rdv_id>/', views.annuler_rdv, name='annuler_rdv'),
    path('accept-appointment/<int:appointment_id>/', views.accept_appointment, name='accept_appointment'),
    path('reject-appointment/<int:appointment_id>/', views.reject_appointment, name='reject_appointment'),
    
    # URLs pour les ordonnances et dossiers médicaux
    path('ordonnance/', views.ordonnance_view, name='ordonnance_view'),
    path('ordonnances-patient/', views.ordonnances_patient_view, name='ordonnances_patient'),
    path('dossier-medical/', views.dossier_medical, name='dossier_medical'),
    path('dossier-medical/<str:patient_name>/', views.dossier_medical, name='dossier_medical_patient'),
    path('create-medical-record/<int:patient_id>/', views.create_medical_record, name='create_medical_record'),
    
    # URLs pour le journal de santé
    path('journal-sante/', views.journal_sante, name='journal_sante'),
    path('export-journal-pdf/', views.export_journal_pdf, name='export_journal_pdf'),
    path('export-ordonnance/<int:ordonnance_id>/', views.export_ordonnance, name='export_ordonnance'),
    path('export-ordonnance-pdf/<int:ordonnance_id>/', views.export_ordonnance_pdf, name='export_ordonnance_pdf'),
    
    # URLs pour l'administration
    path('admin/appointments/', views.admin_appointments_view, name='admin_appointments'),
    path('admin/schedules/', views.admin_schedules_view, name='admin_schedules'),
    path('admin/appointment-stats/', views.admin_appointment_stats_view, name='admin_appointment_stats'),
    path('admin/view-appointment/<int:appointment_id>/', views.admin_view_appointment, name='admin_view_appointment'),
    path('admin/edit-appointment/<int:appointment_id>/', views.admin_edit_appointment, name='admin_edit_appointment'),
    path('admin/cancel-appointment/<int:appointment_id>/', views.admin_cancel_appointment, name='admin_cancel_appointment'),
    path('admin/filter-appointments/', views.admin_filter_appointments, name='admin_filter_appointments'),
    
    # URLs pour la facturation et les rapports
    path('admin/create-invoice/', views.create_invoice, name='create_invoice'),
    path('admin/export-reports/', views.export_reports, name='export_reports'),
    path('admin/download-archive/<int:archive_id>/', views.download_archive, name='download_archive'),
    
    # URLs pour la gestion des ressources
    path('admin/gestion-salles/', views.gestion_salles_view, name='gestion_salles'),
    path('admin/equipements/', views.equipements_view, name='equipements'),
    path('admin/planning-salles/', views.planning_salles_view, name='planning_salles'),
    path('admin/maintenance/', views.maintenance_view, name='maintenance'),
    
    # URLs pour les actions AJAX
    path('admin/room/<int:room_id>/', views.get_room_details, name='get_room_details'),
    path('admin/equipment/<int:equipment_id>/', views.get_equipment_details, name='get_equipment_details'),
    path('admin/view-patient/<int:patient_id>/', views.view_patient_details, name='view_patient_details'),
    path('admin/view-doctor/<int:doctor_id>/', views.view_doctor_details, name='view_doctor_details'),
    path('admin/view-appointment/<int:appointment_id>/', views.view_appointment_details, name='view_appointment_details'),
    
    # Autres URLs
    path('alerte/', views.alerte_view, name='alerte'),
    path('choix-dossier/', views.choix_dossier_view, name='choix_dossier'),
    path('dossier-classique/', views.dossier_classique_view, name='dossier_classique'),
    path('dossier-consultation/', views.dossier_consultation_view, name='dossier_consultation'),
    path('dossier-journalier/', views.dossier_journalier_view, name='dossier_journalier'),
    path('mot-de-passe-oublie/', views.mot_de_passe_oublie_view, name='mot_de_passe_oublie'),
]

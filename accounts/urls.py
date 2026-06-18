"""
================================================================================
FICHIER     : accounts/urls.py
PROJET      : POS_BAKERY — Système de Point de Vente pour Boulangerie
AUTEUR      : Abdoul Aziz Atonfo
VERSION     : 1.2.0
DATE        : 15 juin 2026
================================================================================

RÔLE DE CE FICHIER :
--------------------
Définit les URLs spécifiques à l'application "accounts".
Ces URLs sont préfixées par /accounts/ grâce au include() dans config/urls.py.

URLS DISPONIBLES :
------------------
    /accounts/redirect/            → Redirige vers le bon dashboard selon le rôle
    /accounts/dashboard/admin/     → Tableau de bord du gérant
    /accounts/dashboard/cashier/   → Redirige le caissier vers la caisse

NOTE SUR LA DÉCONNEXION :
--------------------------
La déconnexion (/accounts/logout/) est gérée directement par Django via
django.contrib.auth.urls (inclus dans config/urls.py). Depuis Django 5+,
cette vue n'accepte que les requêtes POST pour des raisons de sécurité.
C'est pourquoi le bouton de déconnexion dans base.html est un formulaire
POST et non un simple lien <a href>.

HISTORIQUE DES MODIFICATIONS :
-------------------------------
v1.0.0 - Création avec redirect_by_role, admin_dashboard, cashier_dashboard,
         accountant_dashboard
v1.1.0 - Ajout du préfixe de nommage app_name pour éviter les conflits d'URL
v1.2.0 - Suppression de accountant_dashboard (rôle comptable abandonné)
================================================================================
"""

from django.urls import path
# On importe le module views plutôt que les fonctions individuellement
# C'est plus lisible et évite les imports multiples si on ajoute des vues
from . import views

# Espace de nommage de l'application
# Permet d'utiliser {% url 'accounts:admin_dashboard' %} dans les templates
# pour éviter les conflits si deux apps ont des URLs du même nom
#app_name = 'accounts'

urlpatterns = [

    # ── Redirection post-login ───────────────────────────────────────────────
    # Appelée automatiquement après une connexion réussie
    # (configuré via LOGIN_REDIRECT_URL = 'redirect_by_role' dans settings.py)
    # Analyse le rôle et redirige vers le bon dashboard
    path('redirect/', views.redirect_by_role, name='redirect_by_role'),

    # ── Dashboard Gérant ─────────────────────────────────────────────────────
    # Tableau de bord avec données temps réel : CA du jour, ventes, alertes stock
    # Accessible uniquement aux utilisateurs avec role='admin'
    # URL complète : http://127.0.0.1:8000/accounts/dashboard/admin/
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),

    # ── Dashboard Caissier ───────────────────────────────────────────────────
    # Simple redirection vers l'interface de caisse
    # Accessible aux utilisateurs avec role='admin' ou role='cashier'
    # URL complète : http://127.0.0.1:8000/accounts/dashboard/cashier/
    path('dashboard/cashier/', views.cashier_dashboard, name='cashier_dashboard'),
]
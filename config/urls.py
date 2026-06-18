"""
================================================================================
FICHIER     : config/urls.py
PROJET      : POS_BAKERY — Système de Point de Vente pour Boulangerie
AUTEUR      : Abdoul Aziz Atonfo
VERSION     : 1.1.0
DATE        : 15 juin 2026
================================================================================

RÔLE DE CE FICHIER :
--------------------
C'est le fichier d'URLs RACINE du projet. Il reçoit TOUTES les requêtes HTTP
et les distribue vers le bon module (accounts, inventory, sales).

Fonctionnement :
    Navigateur → http://127.0.0.1:8000/sales/caisse/
    Django lit ce fichier → trouve path('sales/', ...) → délègue à sales/urls.py
    sales/urls.py → trouve path('caisse/', ...) → appelle cashier_interface()

STRUCTURE DES URLs :
--------------------
    /                           → Redirige automatiquement vers /accounts/login/
    /admin/                     → Interface d'administration Django (superuser)
    /accounts/login/            → Page de connexion (fournie par Django)
    /accounts/logout/           → Déconnexion (fournie par Django)
    /accounts/redirect/         → Redirige selon le rôle après connexion
    /accounts/dashboard/admin/  → Tableau de bord gérant
    /inventory/management/      → Gestion des stocks
    /sales/caisse/              → Interface de caisse

HISTORIQUE DES MODIFICATIONS :
-------------------------------
v1.0.0 - Création initiale
v1.1.0 - Ajout de la redirection racine vers /accounts/login/
================================================================================
"""

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include  # 'include' permet de déléguer à d'autres fichiers urls.py


# ─────────────────────────────────────────────────────────────────────────────
# FONCTION UTILITAIRE : Redirection de la racine
# ─────────────────────────────────────────────────────────────────────────────
def redirect_to_login(request):
    """
    Redirige automatiquement la page d'accueil (/) vers la page de connexion.
    Sans ça, visiter http://127.0.0.1:8000/ afficherait une erreur 404.
    
    Paramètre :
        request : la requête HTTP reçue (ignorée ici, on redirige toujours)
    
    Retourne :
        Une réponse HTTP 302 (redirection) vers la vue nommée 'login'
    """
    return redirect('login')  # 'login' est le nom de la vue fournie par django.contrib.auth.urls


# ─────────────────────────────────────────────────────────────────────────────
# TABLE DE ROUTAGE PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────
urlpatterns = [

    # ── Racine du site ──────────────────────────────────────────────────────
    # Quand l'utilisateur visite http://127.0.0.1:8000/
    # → redirige automatiquement vers la page de connexion
    path('', redirect_to_login, name='root_redirect'),

    # ── Interface d'administration Django ───────────────────────────────────
    # Interface auto-générée par Django pour gérer les données en base.
    # Accessible uniquement aux superusers (is_superuser=True).
    # URL : http://127.0.0.1:8000/admin/
    path('admin/', admin.site.urls),

    # ── URLs d'authentification fournies par Django ──────────────────────────
    # Django fournit automatiquement ces vues prêtes à l'emploi :
    #   /accounts/login/   → affiche le formulaire de connexion
    #   /accounts/logout/  → déconnecte l'utilisateur (requête POST uniquement)
    # Les templates sont dans templates/registration/ (login.html, etc.)
    path('accounts/', include('django.contrib.auth.urls')),

    # ── URLs de notre application "accounts" ────────────────────────────────
    # Contient nos propres vues : redirect_by_role, admin_dashboard, etc.
    # Voir : accounts/urls.py pour le détail des chemins
    path('accounts/', include('accounts.urls')),

    # ── URLs de notre application "inventory" ───────────────────────────────
    # Contient toutes les vues de gestion des stocks et des catégories.
    # Toutes les URLs commenceront par /inventory/...
    # Voir : inventory/urls.py pour le détail des chemins
    path('inventory/', include('inventory.urls')),

    # ── URLs de notre application "sales" ───────────────────────────────────
    # Contient toutes les vues de vente : caisse, tickets, stats, clôture.
    # Toutes les URLs commenceront par /sales/...
    # Voir : sales/urls.py pour le détail des chemins
    path('sales/', include('sales.urls')),
]
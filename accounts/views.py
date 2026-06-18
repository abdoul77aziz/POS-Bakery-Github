"""
================================================================================
FICHIER     : accounts/views.py
PROJET      : POS_BAKERY — Système de Point de Vente pour Boulangerie
AUTEUR      : Abdoul Aziz Atonfo
VERSION     : 1.3.0
DATE        : 15 juin 2026
================================================================================

RÔLE DE CE FICHIER :
--------------------
Contient toutes les "vues" liées à la gestion des utilisateurs et des rôles.
En Django, une vue est une fonction Python qui :
  1. Reçoit une requête HTTP (GET, POST...)
  2. Effectue un traitement (calculs, requêtes base de données...)
  3. Retourne une réponse HTTP (page HTML, redirection, JSON...)

VUES DISPONIBLES :
------------------
  redirect_by_role()   → Redirige l'utilisateur vers son dashboard selon son rôle
  admin_dashboard()    → Tableau de bord du gérant avec données temps réel
  cashier_dashboard()  → Redirige le caissier directement vers la caisse

PROTECTION DES VUES :
---------------------
Toutes les vues sont protégées par deux décorateurs empilés :
  @login_required      → Redirige vers /accounts/login/ si l'utilisateur n'est pas connecté
  @role_required(...)  → Retourne une erreur 403 si le rôle est insuffisant

HISTORIQUE DES MODIFICATIONS :
-------------------------------
v1.0.0 - Création avec redirect_by_role basique
v1.1.0 - Ajout de admin_dashboard et cashier_dashboard
v1.2.0 - admin_dashboard réécrit avec un vrai template (suppression du HttpResponse brut)
         redirect_by_role corrigé pour utiliser request.user.role au lieu de groups
v1.3.0 - Suppression de accountant_dashboard (rôle comptable abandonné)
         Suppression de l'import HttpResponse devenu inutile
         Enrichissement du dashboard admin avec données temps réel
================================================================================
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
# get_object_or_404 : récupère un objet en base ou retourne automatiquement une page 404
from django.shortcuts import get_object_or_404
# Notre décorateur personnalisé pour vérifier les rôles (voir accounts/decorators.py)
from accounts.decorators import role_required


# ─────────────────────────────────────────────────────────────────────────────
# VUE : redirect_by_role
# ─────────────────────────────────────────────────────────────────────────────
@login_required  # Étape 1 : L'utilisateur doit être connecté
def redirect_by_role(request):
    """
    Vue de redirection intelligente appelée juste après la connexion.

    Django appelle cette vue après un login réussi grâce au paramètre
    LOGIN_REDIRECT_URL = 'redirect_by_role' dans settings.py.

    Elle lit le rôle de l'utilisateur connecté et le redirige vers
    son espace de travail adapté :
      - admin   → /accounts/dashboard/admin/  (tableau de bord gérant)
      - cashier → /sales/caisse/              (interface de caisse)

    Paramètre :
        request : contient request.user (l'utilisateur connecté) et
                  request.user.role (son rôle dans la boulangerie)

    Retourne :
        Une redirection HTTP 302 vers la vue appropriée
    """
    if request.user.role == 'admin':
        # Le gérant va vers son tableau de bord avec les stats du jour
        return redirect('admin_dashboard')
    else:
        # Le caissier va directement à la caisse
        return redirect('cashier_interface')


# ─────────────────────────────────────────────────────────────────────────────
# VUE : admin_dashboard
# ─────────────────────────────────────────────────────────────────────────────
@login_required                              # Doit être connecté
@role_required(allowed_roles=['admin'])      # Doit avoir le rôle 'admin'
def admin_dashboard(request):
    """
    Tableau de bord principal du gérant de la boulangerie.

    Affiche en temps réel (recalculé à chaque chargement de page) :
      - Le chiffre d'affaires du jour en cours
      - Le nombre de tickets de caisse du jour
      - Le nombre de produits en alerte stock bas (actifs uniquement)
      - Des boutons d'accès rapide vers les autres modules

    Les imports sont faits à l'intérieur de la fonction (imports locaux)
    pour éviter les imports circulaires potentiels entre les apps Django.

    Paramètre :
        request : la requête HTTP avec l'utilisateur connecté

    Retourne :
        Le template 'accounts/admin_dashboard.html' avec le contexte calculé
    """
    # Imports locaux pour éviter les dépendances circulaires entre apps
    from django.utils import timezone       # Gestion du fuseau horaire (Africa/Douala)
    from django.db.models import Sum        # Fonction SQL d'agrégation (somme)
    from inventory.models import Product    # Modèle produit de l'app inventory
    from sales.models import Order          # Modèle commande de l'app sales

    # Date d'aujourd'hui dans le fuseau horaire configuré (Africa/Douala)
    # ⚠️ On utilise timezone.now().date() et non datetime.today() pour respecter
    #    le fuseau horaire défini dans settings.py TIME_ZONE = 'Africa/Douala'
    today = timezone.now().date()

    # Récupération de toutes les commandes passées aujourd'hui
    # __date est un lookup Django qui extrait la partie date d'un DateTimeField
    today_orders = Order.objects.filter(created_at__date=today)

    # Calcul du chiffre d'affaires du jour
    # aggregate(Sum(...)) exécute un SUM() SQL en une seule requête — très efficace
    # Le résultat est un dictionnaire : {'total_amount__sum': 168.50} ou {'total_amount__sum': None}
    # On utilise "or 0" pour remplacer None par 0 si aucune vente n'a été faite aujourd'hui
    ca_jour = today_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Nombre total de tickets de caisse du jour
    ventes_jour = today_orders.count()

    # Calcul des alertes stock
    # On ne compte que les produits ACTIFS (is_active=True)
    # Un produit désactivé n'est plus en vente, son stock n'a plus d'importance
    alertes_stock = Product.objects.filter(is_active=True)
    # is_low_stock est une propriété calculée définie dans inventory/models.py
    # Elle retourne True si stock_quantity <= low_stock_threshold
    alertes_count = sum(1 for p in alertes_stock if p.is_low_stock)

    # Préparation du contexte : dictionnaire de variables accessibles dans le template
    # Dans le template HTML, on écrira {{ ca_jour }}, {{ ventes_jour }}, etc.
    context = {
        'ca_jour': ca_jour,
        'ventes_jour': ventes_jour,
        'alertes_count': alertes_count,
    }

    return render(request, 'accounts/admin_dashboard.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# VUE : cashier_dashboard
# ─────────────────────────────────────────────────────────────────────────────
@login_required                                          # Doit être connecté
@role_required(allowed_roles=['admin', 'cashier'])       # Admin ou caissier
def cashier_dashboard(request):
    """
    Vue d'accueil pour les caissiers.

    Redirige directement vers l'interface de caisse.
    Le caissier n'a pas besoin d'un tableau de bord complexe —
    son travail commence directement à la caisse.

    Paramètre :
        request : la requête HTTP avec l'utilisateur connecté

    Retourne :
        Une redirection HTTP 302 vers la vue 'cashier_interface' (sales/views.py)
    """
    return redirect('cashier_dashboard')
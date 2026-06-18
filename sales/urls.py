"""
================================================================================
FICHIER     : sales/urls.py
PROJET      : POS_BAKERY — Système de Point de Vente pour Boulangerie
AUTEUR      : Abdoul Aziz Atonfo
VERSION     : 1.2.0
DATE        : 15 juin 2026
================================================================================

RÔLE DE CE FICHIER :
--------------------
Définit toutes les URLs de l'application "sales".
Ces URLs sont préfixées par /sales/ grâce au include() dans config/urls.py.

URLS DISPONIBLES :
------------------
    /sales/caisse/              → Interface de caisse tactile (caissier + admin)
    /sales/process/             → Endpoint AJAX de traitement des ventes (POST uniquement)
    /sales/receipt/<id>/        → Ticket de caisse imprimable (popup)
    /sales/cloture/             → Bilan de clôture du jour
    /sales/cloture/historique/  → Historique des 30 derniers jours
    /sales/statistiques/        → Tableau de bord statistiques (admin uniquement)

NOTE SUR process_sale :
------------------------
L'URL /sales/process/ n'est jamais visitée directement dans le navigateur.
Elle est appelée en coulisse par le JavaScript de la caisse via fetch() :
    fetch('/sales/process/', { method: 'POST', body: JSON.stringify(cart) })
C'est ce qu'on appelle une "API endpoint" ou "vue AJAX".

NOTE SUR order_receipt :
-------------------------
<int:order_id> capture l'identifiant numérique de la commande dans l'URL.
Exemple : /sales/receipt/42/ → appelle order_receipt(request, order_id=42)
Cette URL est ouverte dans un popup navigateur par JavaScript après une vente.

HISTORIQUE DES MODIFICATIONS :
-------------------------------
v1.0.0 - Création avec cashier_interface, process_sale, order_receipt
v1.1.0 - Ajout de daily_cloture et dashboard_stats
v1.2.0 - Ajout de cloture_historique
================================================================================
"""

from django.urls import path
from sales import views

urlpatterns = [

    # ── Interface de caisse ──────────────────────────────────────────────────
    # Page principale du caissier : grille de produits + panier JavaScript
    # Accessible aux rôles 'admin' et 'cashier'
    # URL complète : http://127.0.0.1:8000/sales/caisse/
    path('caisse/', views.cashier_interface, name='cashier_interface'),

    # ── Endpoint AJAX de traitement des ventes ───────────────────────────────
    # Reçoit le panier en JSON (POST), crée la commande, retourne {success, order_id}
    # Jamais visitée directement — appelée uniquement par le JavaScript de la caisse
    # Protégée par @transaction.atomic pour garantir l'intégrité des données
    path('process/', views.process_sale, name='process_sale'),

    # ── Ticket de caisse imprimable ──────────────────────────────────────────
    # Affiche le reçu de la commande dans un popup (format rouleau thermique 75mm)
    # <int:order_id> : identifiant de la commande, extrait de l'URL
    # Exemple : /sales/receipt/42/ affiche le ticket de la commande n°42
    path('receipt/<int:order_id>/', views.order_receipt, name='order_receipt'),

    # ── Clôture journalière ──────────────────────────────────────────────────
    # Bilan du jour par mode de paiement (espèces / carte / mobile)
    # Permet au caissier/gérant de vérifier sa caisse physique en fin de journée
    # Accessible aux rôles 'admin' et 'cashier'
    path('cloture/', views.daily_cloture, name='daily_cloture'),

    # ── Historique des clôtures ──────────────────────────────────────────────
    # Tableau des 30 derniers jours + détail d'un jour sélectionnable
    # Filtre par date possible via le paramètre GET : /sales/cloture/historique/?date=2026-06-10
    # Accessible uniquement au rôle 'admin'
    path('cloture/historique/', views.cloture_historique, name='cloture_historique'),

    # ── Tableau de bord statistiques ─────────────────────────────────────────
    # CA global, marge brute, panier moyen, Top 5 produits
    # Toutes les stats sont calculées via des requêtes SQL optimisées (annotate/aggregate)
    # Accessible uniquement au rôle 'admin'
    path('statistiques/', views.dashboard_stats, name='dashboard_stats'),
]
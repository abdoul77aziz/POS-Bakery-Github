"""
================================================================================
FICHIER     : inventory/urls.py
PROJET      : POS_BAKERY — Système de Point de Vente pour Boulangerie
AUTEUR      : Abdoul Aziz Atonfo
VERSION     : 1.2.0
DATE        : 15 juin 2026
================================================================================

RÔLE DE CE FICHIER :
--------------------
Définit toutes les URLs de l'application "inventory".
Ces URLs sont préfixées par /inventory/ grâce au include() dans config/urls.py.

URLS DISPONIBLES :
------------------
PRODUITS :
    /inventory/management/                  → Liste de tous les produits
    /inventory/product/add/                 → Formulaire d'ajout d'un produit
    /inventory/product/edit/<id>/           → Formulaire de modification d'un produit
    /inventory/product/toggle/<id>/         → Active ou désactive un produit

CATÉGORIES :
    /inventory/categories/                  → Liste de toutes les catégories
    /inventory/categories/add/              → Formulaire d'ajout d'une catégorie
    /inventory/categories/edit/<id>/        → Formulaire de modification d'une catégorie

NOTATION <int:product_id> :
----------------------------
Le segment <int:product_id> dans une URL est un "convertisseur de chemin".
  - int  : Django vérifie que la valeur est un entier (sécurité)
  - product_id : nom du paramètre passé à la fonction vue correspondante
Exemple : /inventory/product/edit/5/ → appelle product_update(request, product_id=5)

HISTORIQUE DES MODIFICATIONS :
-------------------------------
v1.0.0 - Création avec product_list et soft_delete_product
v1.1.0 - Ajout de product_create et product_update
v1.2.0 - Ajout des URLs pour la gestion des catégories
================================================================================
"""

from django.urls import path
from inventory import views

urlpatterns = [

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 : URLs des PRODUITS
    # ══════════════════════════════════════════════════════════════════════════

    # Liste complète de l'inventaire avec marges et alertes stock
    # Accessible via le lien "Stocks" dans la navbar (réservé aux admins)
    path('management/', views.product_list, name='product_list'),

    # Formulaire pour ajouter un nouveau produit au catalogue
    # Accessible via le bouton "+ Ajouter un produit" dans product_list.html
    path('product/add/', views.product_create, name='product_create'),

    # Formulaire pré-rempli pour modifier un produit existant
    # <int:product_id> capture l'identifiant du produit depuis l'URL
    # Exemple : /inventory/product/edit/12/ modifie le produit avec id=12
    path('product/edit/<int:product_id>/', views.product_update, name='product_update'),

    # Bascule l'état actif/inactif d'un produit sans confirmation
    # Action rapide via le bouton Désactiver/Réactiver dans product_list.html
    path('product/toggle/<int:product_id>/', views.soft_delete_product, name='soft_delete_product'),


    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 : URLs des CATÉGORIES
    # ══════════════════════════════════════════════════════════════════════════

    # Liste de toutes les catégories avec compteur de produits liés
    # Accessible via le bouton "Gérer les catégories" dans product_list.html
    path('categories/', views.category_list, name='category_list'),

    # Formulaire pour créer une nouvelle catégorie (nom + description)
    # Accessible via le bouton "+ Ajouter une catégorie" dans category_list.html
    path('categories/add/', views.category_create, name='category_create'),

    # Formulaire pré-rempli pour modifier une catégorie existante
    # <int:category_id> capture l'identifiant de la catégorie depuis l'URL
    path('categories/edit/<int:category_id>/', views.category_update, name='category_update'),
]
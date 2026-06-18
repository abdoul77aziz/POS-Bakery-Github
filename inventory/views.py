"""
================================================================================
FICHIER     : inventory/views.py
PROJET      : POS_BAKERY — Système de Point de Vente pour Boulangerie
AUTEUR      : Abdoul Aziz Atonfo
VERSION     : 1.2.0
DATE        : 15 juin 2026
================================================================================

RÔLE DE CE FICHIER :
--------------------
Contient toutes les vues de gestion de l'inventaire (stocks et catégories).
Ces vues permettent au gérant (rôle 'admin') de :
  - Consulter la liste des produits avec leurs marges et alertes stock
  - Ajouter, modifier, activer et désactiver des produits
  - Gérer les catégories (liste, ajout, modification)

TOUTES ces vues sont réservées au gérant (role='admin').
Un caissier qui tenterait d'y accéder recevrait une erreur 403 Forbidden.

VUES DISPONIBLES :
------------------
  product_list()      → Liste tous les produits avec marges et alertes
  soft_delete_product()→ Active ou désactive un produit (toggle)
  product_create()    → Formulaire d'ajout d'un nouveau produit
  product_update()    → Formulaire de modification d'un produit existant
  category_list()     → Liste toutes les catégories avec compteur de produits
  category_create()   → Formulaire d'ajout d'une nouvelle catégorie
  category_update()   → Formulaire de modification d'une catégorie

CONCEPT DE SOFT DELETE :
-------------------------
Au lieu de supprimer définitivement un produit de la base de données,
on le "désactive" en mettant is_active=False. Avantages :
  - L'historique des ventes reste cohérent (les tickets anciens restent valides)
  - On peut réactiver le produit à tout moment
  - Aucune perte de données accidentelle

HISTORIQUE DES MODIFICATIONS :
-------------------------------
v1.0.0 - Création de product_list et soft_delete_product
v1.1.0 - Ajout de product_create et product_update
v1.2.0 - Ajout de category_list, category_create, category_update
         Ajout des imports Category, CategoryForm et models
================================================================================
"""

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.db import models  # Nécessaire pour models.Count dans category_list
from accounts.decorators import role_required
# Import des deux modèles et des deux formulaires de cette application
from .models import Product, Category
from .forms import ProductForm, CategoryForm


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1 : GESTION DES PRODUITS
# ═════════════════════════════════════════════════════════════════════════════

@login_required
@role_required(allowed_roles=['admin'])
def product_list(request):
    """
    Affiche le tableau de bord complet de l'inventaire.

    Pour chaque produit, on calcule dynamiquement :
      - La marge brute (selling_price - purchase_price)
      - L'état du stock (normal ou en alerte)

    On affiche également un compteur global des produits en alerte
    en haut du tableau pour une vue d'ensemble rapide.

    Les produits désactivés (is_active=False) sont inclus dans la liste
    afin que le gérant puisse les réactiver si besoin.
    Ils apparaissent visuellement différenciés dans le template.

    Paramètre :
        request : la requête HTTP

    Retourne :
        Le template 'inventory/product_list.html' avec le contexte
    """
    # Récupération de tous les produits, triés par catégorie puis par nom
    # L'ordre catégorie → nom facilite la lecture du tableau
    products = Product.objects.all().order_by('category', 'name')

    # Calcul de la marge pour chaque produit
    # On attache la marge directement à l'objet Python (pas en base de données)
    # Cela permet d'écrire {{ product.margin }} dans le template
    for product in products:
        product.margin = product.selling_price - product.purchase_price

    # Comptage des produits actifs en alerte stock bas
    # is_low_stock est une propriété du modèle Product (voir inventory/models.py)
    # On n'inclut que les produits is_active=True : un produit désactivé
    # n'est plus en vente, donc son stock n'a plus d'importance
    low_stock_count = sum(1 for p in products if p.is_low_stock and p.is_active)

    context = {
        'products': products,               # Liste de tous les produits (avec .margin calculé)
        'low_stock_count': low_stock_count, # Compteur global d'alertes pour le bandeau
    }
    return render(request, 'inventory/product_list.html', context)


@login_required
@role_required(allowed_roles=['admin'])
def soft_delete_product(request, product_id):
    """
    Bascule l'état actif/inactif d'un produit (Soft Delete / Réactivation).

    Cette vue agit comme un interrupteur (toggle) :
      - Si le produit est actif   (is_active=True)  → on le désactive (False)
      - Si le produit est inactif (is_active=False) → on le réactive (True)

    Un produit désactivé :
      - N'apparaît plus dans l'interface de caisse
      - Reste dans la liste d'inventaire (avec indicateur visuel)
      - Conserve tout son historique de ventes
      - Peut être réactivé à tout moment

    Paramètre :
        request    : la requête HTTP
        product_id : l'identifiant (clé primaire) du produit à basculer

    Retourne :
        Une redirection vers la liste des produits après la modification
    """
    # get_object_or_404 : récupère le produit avec cet id, ou retourne une page 404
    # si aucun produit ne correspond (protection contre les URL falsifiées)
    product = get_object_or_404(Product, id=product_id)

    # Inversion booléenne : True devient False, False devient True
    product.is_active = not product.is_active

    # Sauvegarde en base de données
    # update_fields=['is_active'] optimise la requête SQL en ne mettant à jour
    # que cette colonne plutôt que toutes les colonnes du produit
    product.save()

    # Redirection vers la liste après modification
    return redirect('product_list')


@login_required
@role_required(allowed_roles=['admin'])
def product_create(request):
    """
    Affiche et traite le formulaire d'ajout d'un nouveau produit.

    Fonctionnement en deux phases selon la méthode HTTP :
      GET  → Affiche le formulaire vide pour saisir les informations
      POST → Valide et sauvegarde le nouveau produit, puis redirige

    Ce pattern GET/POST est la convention standard Django pour les formulaires.

    Paramètre :
        request : la requête HTTP (request.method indique GET ou POST)

    Retourne :
        GET  → Template 'inventory/product_form.html' avec formulaire vide
        POST valide   → Redirection vers la liste des produits
        POST invalide → Template avec le formulaire et les erreurs affichées
    """
    if request.method == 'POST':
        # L'utilisateur a soumis le formulaire
        # request.POST contient toutes les valeurs saisies dans le formulaire HTML
        form = ProductForm(request.POST)

        if form.is_valid():
            # Toutes les validations sont passées (champs requis, types corrects, etc.)
            # form.save() insère une nouvelle ligne dans la table inventory_product
            form.save()
            # Redirection vers la liste pour voir le nouveau produit
            return redirect('product_list')
        # Si le formulaire est invalide, on "tombe" en dessous
        # et on réaffiche le formulaire avec les erreurs de validation
    else:
        # Requête GET : on affiche un formulaire vide
        form = ProductForm()

    # Rendu du template avec le formulaire (vide ou avec erreurs)
    # 'title' est utilisé dans le template pour l'en-tête de la carte
    return render(request, 'inventory/product_form.html', {
        'form': form,
        'title': "Ajouter un produit"
    })


@login_required
@role_required(allowed_roles=['admin'])
def product_update(request, product_id):
    """
    Affiche et traite le formulaire de modification d'un produit existant.

    Même logique GET/POST que product_create, mais avec une instance
    pré-existante : le formulaire est pré-rempli avec les valeurs actuelles
    du produit, et la sauvegarde met à jour l'enregistrement existant
    au lieu d'en créer un nouveau.

    Paramètre :
        request    : la requête HTTP
        product_id : l'identifiant du produit à modifier (extrait de l'URL)

    Retourne :
        GET  → Template avec formulaire pré-rempli des valeurs actuelles
        POST valide   → Redirection vers la liste des produits
        POST invalide → Template avec le formulaire et les erreurs affichées
    """
    # Récupération du produit à modifier (ou 404 si inexistant)
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        # instance=product : Django sait qu'il doit mettre à jour CE produit
        # et non en créer un nouveau lors du form.save()
        form = ProductForm(request.POST, instance=product)

        if form.is_valid():
            form.save()  # UPDATE en base de données (pas INSERT)
            return redirect('product_list')
    else:
        # instance=product : pré-remplit le formulaire avec les valeurs actuelles
        form = ProductForm(instance=product)

    return render(request, 'inventory/product_form.html', {
        'form': form,
        'title': "Modifier le produit"
    })


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2 : GESTION DES CATÉGORIES
# ═════════════════════════════════════════════════════════════════════════════

@login_required
@role_required(allowed_roles=['admin'])
def category_list(request):
    """
    Affiche la liste de toutes les catégories avec leur nombre de produits liés.

    Utilise annotate() pour ajouter dynamiquement un compteur de produits
    à chaque catégorie via une requête SQL optimisée (COUNT avec GROUP BY).
    C'est plus efficace qu'une boucle Python qui ferait une requête par catégorie.

    Exemple SQL généré :
        SELECT *, COUNT(products.id) as product_count
        FROM inventory_category
        LEFT JOIN inventory_product ON category_id = inventory_category.id
        GROUP BY inventory_category.id
        ORDER BY name

    Paramètre :
        request : la requête HTTP

    Retourne :
        Le template 'inventory/category_list.html' avec la liste annotée
    """
    # annotate() ajoute un attribut calculé à chaque objet de la queryset
    # models.Count('products') compte les produits liés via la relation ForeignKey
    # 'products' est le related_name défini dans le modèle Product (voir inventory/models.py)
    categories = Category.objects.annotate(
        product_count=models.Count('products')  # Ajoute .product_count à chaque catégorie
    ).order_by('name')  # Tri alphabétique

    context = {'categories': categories}
    return render(request, 'inventory/category_list.html', context)


@login_required
@role_required(allowed_roles=['admin'])
def category_create(request):
    """
    Affiche et traite le formulaire d'ajout d'une nouvelle catégorie.

    Même pattern GET/POST que product_create.
    Le formulaire CategoryForm ne demande que le nom et la description.

    Paramètre :
        request : la requête HTTP

    Retourne :
        GET  → Template avec formulaire vide
        POST valide   → Redirection vers la liste des catégories
        POST invalide → Template avec erreurs
    """
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm()

    return render(request, 'inventory/category_form.html', {
        'form': form,
        'title': 'Ajouter une catégorie'
    })


@login_required
@role_required(allowed_roles=['admin'])
def category_update(request, category_id):
    """
    Affiche et traite le formulaire de modification d'une catégorie existante.

    Même pattern que product_update : instance pré-remplie en GET,
    mise à jour en base sur POST valide.

    Paramètre :
        request     : la requête HTTP
        category_id : l'identifiant de la catégorie à modifier (extrait de l'URL)

    Retourne :
        GET  → Template avec formulaire pré-rempli
        POST valide   → Redirection vers la liste des catégories
        POST invalide → Template avec erreurs
    """
    # Récupération de la catégorie à modifier (ou 404 si inexistante)
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()  # UPDATE en base de données
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'inventory/category_form.html', {
        'form': form,
        'title': 'Modifier la catégorie'
    })
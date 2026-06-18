"""
================================================================================
FICHIER     : inventory/forms.py
PROJET      : POS_BAKERY — Système de Point de Vente pour Boulangerie
AUTEUR      : Abdoul Aziz Atonfo
VERSION     : 1.1.0
DATE        : 15 juin 2026
================================================================================

RÔLE DE CE FICHIER :
--------------------
Définit les formulaires HTML de l'application inventory.
En Django, un formulaire (Form/ModelForm) est une classe Python qui :
  1. Génère automatiquement les champs HTML (<input>, <select>, etc.)
  2. Valide les données soumises par l'utilisateur
  3. Sauvegarde les données en base de données (pour les ModelForm)

DIFFÉRENCE FORM VS MODELFORM :
-------------------------------
  forms.Form      → Formulaire générique, champs définis manuellement
  forms.ModelForm → Formulaire lié à un modèle, champs générés automatiquement
                    depuis les colonnes de la table SQL correspondante

On utilise ModelForm ici car nos formulaires correspondent directement
aux modèles Product et Category.

FORMULAIRES DISPONIBLES :
--------------------------
  ProductForm  → Ajout et modification d'un produit du catalogue
  CategoryForm → Ajout et modification d'une catégorie

HISTORIQUE DES MODIFICATIONS :
-------------------------------
v1.0.0 - Création de ProductForm
v1.1.0 - Ajout de CategoryForm pour la gestion des catégories
         Ajout de l'import Category dans les modèles
================================================================================
"""

from django import forms
# On importe les deux modèles dont on a besoin pour générer les formulaires
from .models import Product, Category


class ProductForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier un produit du catalogue.

    Ce formulaire est utilisé dans deux vues :
      - product_create() : création d'un nouveau produit (instance vide)
      - product_update() : modification d'un produit existant (instance pré-remplie)

    Django génère automatiquement les champs HTML depuis le modèle Product.
    On spécifie uniquement les champs qu'on veut afficher dans le formulaire
    (on exclut par exemple 'is_active' qui se gère via le bouton dédié).
    """

    class Meta:
        """
        Configuration du formulaire — indique à Django quel modèle utiliser
        et quels champs inclure.
        """
        # Modèle source : Django lit les colonnes de la table inventory_product
        model = Product

        # Liste des champs à afficher dans le formulaire HTML.
        # L'ordre ici détermine l'ordre d'affichage dans la page.
        fields = [
            'category',          # Sélecteur déroulant des catégories disponibles
            'name',              # Nom du produit
            'purchase_price',    # Prix d'achat (coût des ingrédients)
            'selling_price',     # Prix de vente affiché en caisse
            'stock_quantity',    # Quantité en stock actuelle
            'low_stock_threshold', # Seuil en dessous duquel une alerte est déclenchée
        ]

    def __init__(self, *args, **kwargs):
        """
        Méthode d'initialisation du formulaire.
        Appelée automatiquement à chaque instanciation du formulaire.

        On y personnalise l'apparence des champs en ajoutant des classes CSS Bootstrap.
        Sans ça, les champs HTML auraient un rendu brut sans style.

        *args et **kwargs : permettent de passer des arguments supplémentaires
        à la classe parente (notamment l'instance du produit à modifier).
        """
        # Appel obligatoire à __init__ de la classe parente (ModelForm)
        # pour que Django initialise correctement le formulaire
        super().__init__(*args, **kwargs)

        # On parcourt tous les champs du formulaire pour leur ajouter
        # la classe CSS Bootstrap 'form-control' qui leur donne un style cohérent
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            # Note : on pourrait personnaliser chaque champ individuellement ici
            # Exemple : self.fields['name'].widget.attrs['placeholder'] = 'Ex: Croissant'


class CategoryForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier une catégorie de produits.

    Ce formulaire est utilisé dans deux vues :
      - category_create() : création d'une nouvelle catégorie
      - category_update() : modification d'une catégorie existante

    Les catégories permettent d'organiser les produits dans la caisse
    (Viennoiseries, Pâtisseries, Boissons, Pains, etc.)
    """

    class Meta:
        """
        Configuration du formulaire catégorie.
        """
        # Modèle source : table inventory_category
        model = Category

        # On affiche uniquement le nom et la description
        # L'identifiant (id) est auto-généré par Django, on ne l'expose pas
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        """
        Initialisation avec ajout du style Bootstrap sur tous les champs.
        Même logique que ProductForm.__init__().
        """
        super().__init__(*args, **kwargs)

        # Application de la classe Bootstrap sur tous les champs du formulaire
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
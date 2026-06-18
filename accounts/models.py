"""
================================================================================
FICHIER     : accounts/models.py
PROJET      : POS_BAKERY — Système de Point de Vente pour Boulangerie
AUTEUR      : Équipe POS_BAKERY
VERSION     : 1.2.0
DATE        : 15 juin 2026
================================================================================

RÔLE DE CE FICHIER :
--------------------
Définit la structure des données liées aux utilisateurs dans la base de données.
En Django, un "modèle" est une classe Python qui correspond à une table SQL.
Ce fichier contient un seul modèle : CustomUser, qui étend le modèle User
par défaut de Django en y ajoutant les champs métier dont on a besoin.

POURQUOI PERSONNALISER LE MODÈLE USER ?
-----------------------------------------
Django fournit un modèle User de base avec username, password, email, etc.
Mais pour une boulangerie, on a besoin de deux choses supplémentaires :
  1. Un RÔLE : savoir si l'utilisateur est gérant ou caissier
  2. Un TÉLÉPHONE : numéro de contact optionnel

La bonne pratique Django est de créer ce modèle personnalisé DÈS LE DÉBUT
du projet (avant la première migration), car le changer ensuite est complexe.
Ce modèle est référencé dans settings.py via AUTH_USER_MODEL = 'accounts.CustomUser'

TABLE CRÉÉE EN BASE :
---------------------
    accounts_customuser
    ├── id           (entier, clé primaire, auto-incrémenté)
    ├── username     (texte, unique — hérité de Django)
    ├── password     (texte hashé — hérité de Django)
    ├── email        (texte — hérité de Django)
    ├── first_name   (texte — hérité de Django)
    ├── last_name    (texte — hérité de Django)
    ├── is_active    (booléen — hérité de Django)
    ├── is_staff     (booléen — hérité de Django)
    ├── is_superuser (booléen — hérité de Django)
    ├── date_joined  (date — hérité de Django)
    ├── role         (texte choix : 'admin' ou 'cashier') ← AJOUTÉ PAR NOUS
    └── phone        (texte optionnel) ← AJOUTÉ PAR NOUS

HISTORIQUE DES MODIFICATIONS :
-------------------------------
v1.0.0 - Création avec les rôles admin, cashier, accountant
v1.1.0 - Ajout du champ phone
v1.2.0 - Suppression du rôle accountant (fonctionnalité non implémentée)
         Migration 0002_alter_customuser_role générée et appliquée
================================================================================
"""

from django.db import models
# AbstractUser contient déjà tous les champs et méthodes d'un utilisateur Django
# (username, password, email, is_staff, is_superuser, etc.)
# On en hérite pour ne pas réécrire tout ça depuis zéro.
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Modèle utilisateur personnalisé de la boulangerie.

    Hérite de AbstractUser (qui hérite lui-même de AbstractBaseUser et
    PermissionsMixin), ce qui nous donne gratuitement :
      - La gestion des mots de passe (hashage, vérification)
      - Le système de groupes et permissions Django
      - Les champs username, email, first_name, last_name, is_active, etc.
      - Les méthodes is_authenticated, is_anonymous, etc.

    On y ajoute uniquement ce dont on a besoin pour la boulangerie.
    """

    # ── Choix de rôles disponibles ───────────────────────────────────────────
    # Format : liste de tuples (valeur_en_base, libellé_affiché)
    # La valeur en base est ce qui sera stocké dans la colonne SQL.
    # Le libellé est ce qui sera affiché dans les formulaires et l'admin Django.
    ROLE_CHOICES = [
        ('admin', 'Gérant / Admin'),    # Accès complet : caisse, stocks, stats, clôture
        ('cashier', 'Caissier'),         # Accès restreint : caisse et clôture uniquement
    ]

    # ── Champ rôle ───────────────────────────────────────────────────────────
    # max_length=20 : longueur maximale de la valeur stockée en base ('cashier' = 7 caractères)
    # choices : limite les valeurs acceptées à la liste ROLE_CHOICES
    # default='cashier' : si on crée un utilisateur sans préciser le rôle, il sera caissier
    # Ce choix par défaut est sécurisé : un nouvel utilisateur n'aura jamais les droits admin accidentellement
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='cashier',
        verbose_name="Rôle dans la boulangerie"  # Libellé affiché dans l'interface admin Django
    )

    # ── Champ téléphone ──────────────────────────────────────────────────────
    # max_length=20 : suffisant pour tous les formats de numéros internationaux
    # blank=True : le champ est optionnel dans les formulaires (validation Django)
    # null=True  : la colonne SQL peut contenir NULL (valeur absente en base de données)
    # Sans blank=True et null=True, le champ serait obligatoire partout.
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Numéro de téléphone"
    )

    # ── Représentation textuelle de l'objet ──────────────────────────────────
    def __str__(self):
        """
        Définit comment un objet CustomUser est affiché sous forme de texte.
        Utilisé dans l'interface admin Django, les logs, le shell, etc.

        Exemple : CustomUser.objects.get(id=1) → affiche "admin (Gérant / Admin)"
        get_role_display() est une méthode auto-générée par Django pour les champs
        avec choices — elle retourne le libellé lisible plutôt que la valeur interne.
        """
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        """
        Métadonnées du modèle — options qui ne correspondent pas à des colonnes SQL.
        """
        # Libellés affichés dans l'interface d'administration Django
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
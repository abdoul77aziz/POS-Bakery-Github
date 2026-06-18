"""
================================================================================
FICHIER     : config/settings.py
PROJET      : POS_BAKERY — Système de Point de Vente pour Boulangerie
AUTEUR      : Abdoul Aziz Atonfo
VERSION     : 1.2.0
DATE        : 15 juin 2026
================================================================================

RÔLE DE CE FICHIER :
--------------------
C'est le fichier de configuration central de tout le projet Django.
Il contrôle absolument tout : la sécurité, les applications installées,
la base de données, les templates HTML, les fichiers statiques (CSS/JS),
la langue, le fuseau horaire, etc.

HISTORIQUE DES MODIFICATIONS :
-------------------------------
v1.0.0 - Création initiale par django-admin startproject
v1.1.0 - Ajout du modèle utilisateur personnalisé (AUTH_USER_MODEL)
         Ajout des redirections LOGIN/LOGOUT
v1.2.0 - SECRET_KEY sécurisée via variable d'environnement
         TIME_ZONE corrigé sur Africa/Douala (UTC+1, Cameroun)
         Ajout de STATICFILES_DIRS et STATIC_ROOT pour le mode hors ligne
================================================================================
"""

import os          # Permet de lire les variables d'environnement du système
from pathlib import Path  # Permet de construire des chemins de fichiers compatibles Windows/Mac/Linux

# ─────────────────────────────────────────────────────────────────────────────
# CHEMIN DE BASE DU PROJET
# ─────────────────────────────────────────────────────────────────────────────
# BASE_DIR pointe vers le dossier racine du projet (là où se trouve manage.py).
# Tous les autres chemins sont construits à partir de lui.
# Exemple : BASE_DIR / 'templates' → C:\...\POS_BAKERY\templates
BASE_DIR = Path(__file__).resolve().parent.parent


# ─────────────────────────────────────────────────────────────────────────────
# SÉCURITÉ
# ─────────────────────────────────────────────────────────────────────────────

# SECRET_KEY : clé cryptographique utilisée par Django pour signer les cookies,
# les tokens CSRF, et d'autres mécanismes de sécurité.
# ⚠️  IMPORTANT : En production, cette valeur DOIT être une vraie clé secrète
#     stockée dans une variable d'environnement, jamais directement dans le code.
#     En local, si la variable d'environnement n'existe pas, on utilise
#     la clé de développement (commence par 'django-insecure-').
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-8hxhvujwac8bwbqqfs4u3vg+rixroyeov+=**_lzt39m(ithhi'
)

# DEBUG : Quand True, Django affiche les erreurs détaillées dans le navigateur.
# ⚠️  IMPORTANT : Ne JAMAIS laisser DEBUG=True en production — cela exposerait
#     le code source et la configuration aux visiteurs malveillants.
#     La variable d'environnement DJANGO_DEBUG permet de le désactiver en prod.
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# ALLOWED_HOSTS : liste des domaines/IP autorisés à accéder à l'application.
# En local, on autorise uniquement 127.0.0.1 (localhost).
# En production, on ajoutera le vrai domaine (ex: 'pos-bakery.railway.app').
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Si une variable d'environnement DJANGO_ALLOWED_HOSTS est définie (en prod),
# on l'ajoute automatiquement à la liste. Format : "domaine1.com,domaine2.com"
if os.environ.get('DJANGO_ALLOWED_HOSTS'):
    ALLOWED_HOSTS.extend(os.environ.get('DJANGO_ALLOWED_HOSTS').split(','))


# ─────────────────────────────────────────────────────────────────────────────
# APPLICATIONS INSTALLÉES
# ─────────────────────────────────────────────────────────────────────────────
# Liste de toutes les "apps" actives dans le projet.
# Django a besoin de les connaître pour les migrations, les templates, etc.
INSTALLED_APPS = [
    # Applications natives Django (ne pas toucher)
    'django.contrib.admin',        # Interface d'administration Django (/admin/)
    'django.contrib.auth',         # Système d'authentification (login/logout)
    'django.contrib.contenttypes', # Gestion des types de contenu (nécessaire pour auth)
    'django.contrib.sessions',     # Gestion des sessions utilisateur (cookies)
    'django.contrib.messages',     # Système de messages flash (succès, erreurs...)
    'django.contrib.staticfiles',  # Gestion des fichiers statiques (CSS, JS, images)

    # Nos applications métier (créées pour ce projet)
    'accounts',    # Gestion des utilisateurs et des rôles (gérant, caissier)
    'inventory',   # Gestion du catalogue produits et des stocks
    'sales',       # Gestion des ventes, de la caisse et des statistiques
]


# ─────────────────────────────────────────────────────────────────────────────
# MIDDLEWARE (Couches de traitement des requêtes HTTP)
# ─────────────────────────────────────────────────────────────────────────────
# Chaque requête HTTP passe à travers ces couches dans l'ordre.
# Elles ajoutent des fonctionnalités comme la sécurité, la gestion des sessions,
# la protection CSRF (contre les attaques de formulaires), etc.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',              # En-têtes de sécurité HTTP
    'django.contrib.sessions.middleware.SessionMiddleware',       # Gestion des sessions
    'django.middleware.common.CommonMiddleware',                  # Redirections communes (slash final)
    'django.middleware.csrf.CsrfViewMiddleware',                  # Protection CSRF (anti-piratage de formulaires)
    'django.contrib.auth.middleware.AuthenticationMiddleware',    # Attache l'utilisateur connecté à chaque requête
    'django.contrib.messages.middleware.MessageMiddleware',       # Gestion des messages flash
    'django.middleware.clickjacking.XFrameOptionsMiddleware',     # Protection contre le clickjacking
]


# ─────────────────────────────────────────────────────────────────────────────
# URLS RACINES
# ─────────────────────────────────────────────────────────────────────────────
# Indique à Django quel fichier urls.py utiliser comme point d'entrée principal.
ROOT_URLCONF = 'config.urls'


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATES (Fichiers HTML)
# ─────────────────────────────────────────────────────────────────────────────
# Configuration du moteur de templates Django.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Django cherchera les templates HTML dans ce dossier en premier
        'DIRS': [BASE_DIR / 'templates'],
        # Puis il cherchera dans le sous-dossier templates/ de chaque app
        'APP_DIRS': True,
        'OPTIONS': {
            # context_processors : injectent automatiquement des variables
            # dans TOUS les templates sans avoir à les passer manuellement.
            'context_processors': [
                'django.template.context_processors.request',  # Donne accès à {{ request }}
                'django.contrib.auth.context_processors.auth', # Donne accès à {{ user }}
                'django.contrib.messages.context_processors.messages', # Donne accès aux messages flash
            ],
        },
    },
]

# Point d'entrée WSGI (interface entre Django et le serveur web en production)
WSGI_APPLICATION = 'config.wsgi.application'


# ─────────────────────────────────────────────────────────────────────────────
# BASE DE DONNÉES
# ─────────────────────────────────────────────────────────────────────────────
# Configuration de la base de données principale du projet.
# SQLite : base de données stockée dans un seul fichier (db.sqlite3).
# ✅ Parfait pour le développement et les installations mono-poste.
# ⚠️  À remplacer par PostgreSQL en production multi-utilisateurs (Railway).
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Moteur SQLite
        'NAME': BASE_DIR / 'db.sqlite3',          # Chemin du fichier de base de données
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION DES MOTS DE PASSE
# ─────────────────────────────────────────────────────────────────────────────
# Django vérifie automatiquement la force des mots de passe lors de la création
# d'un compte. Ces validateurs définissent les règles appliquées.
AUTH_PASSWORD_VALIDATORS = [
    # Interdit les mots de passe trop similaires au nom d'utilisateur
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    # Exige un minimum de 8 caractères
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    # Interdit les mots de passe trop communs ("password", "123456", etc.)
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    # Interdit les mots de passe entièrement numériques
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ─────────────────────────────────────────────────────────────────────────────
# INTERNATIONALISATION & FUSEAU HORAIRE
# ─────────────────────────────────────────────────────────────────────────────
# Langue de l'interface Django (messages d'erreur, validation, etc.)
# 'en-us' : anglais américain — évite les problèmes de virgule décimale en JS
# Note : l'interface de l'application elle-même est en français (templates HTML)
LANGUAGE_CODE = 'en-us'

# Fuseau horaire du serveur.
# ⚠️  CRITIQUE pour la clôture journalière : sans ce réglage, les commandes
#     du soir seraient comptabilisées sur le mauvais jour (décalage UTC).
# 'Africa/Douala' = UTC+1 (Cameroun, Afrique Centrale)
TIME_ZONE = 'Africa/Douala'

# Active les traductions (USE_I18N) et le support des fuseaux horaires (USE_TZ)
USE_I18N = True
USE_TZ = True   # Les dates sont stockées en UTC dans la DB, converties à l'affichage


# ─────────────────────────────────────────────────────────────────────────────
# FICHIERS STATIQUES (CSS, JavaScript, Images)
# ─────────────────────────────────────────────────────────────────────────────
# URL de base pour accéder aux fichiers statiques dans le navigateur
# Ex: /static/css/bootstrap.min.css
STATIC_URL = 'static/'

# Dossiers où Django cherche les fichiers statiques du projet
# (notre dossier static/ à la racine avec Bootstrap téléchargé localement)
STATICFILES_DIRS = [BASE_DIR / 'static']

# Dossier de destination quand on lance "python manage.py collectstatic"
# Django copie tous les fichiers statiques ici pour le déploiement en production
STATIC_ROOT = BASE_DIR / 'staticfiles'


# ─────────────────────────────────────────────────────────────────────────────
# AUTHENTIFICATION PERSONNALISÉE
# ─────────────────────────────────────────────────────────────────────────────
# Indique à Django d'utiliser notre modèle utilisateur personnalisé (CustomUser)
# au lieu du modèle User par défaut. Permet d'ajouter les champs 'role' et 'phone'.
AUTH_USER_MODEL = 'accounts.CustomUser'

# Après une connexion réussie, Django redirige vers cette vue nommée.
# 'redirect_by_role' analyse le rôle et redirige vers le bon dashboard.
LOGIN_REDIRECT_URL = 'redirect_by_role'

# Après une déconnexion, Django redirige vers la page de connexion.
LOGOUT_REDIRECT_URL = 'login'
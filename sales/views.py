"""
================================================================================
FICHIER     : sales/views.py
PROJET      : POS_BAKERY — Système de Point de Vente pour Boulangerie
AUTEUR      : Abdoul Aziz Atonfo
VERSION     : 1.3.0
DATE        : 15 juin 2026
================================================================================

RÔLE DE CE FICHIER :
--------------------
Contient toutes les vues liées aux ventes et à la gestion financière.
C'est le fichier le plus important du projet car il gère le cœur métier :
l'encaissement des clients.

VUES DISPONIBLES :
------------------
  cashier_interface()   → Interface de caisse tactile avec catalogue et panier
  process_sale()        → Traite une vente AJAX : crée la commande, décrémente le stock
  order_receipt()       → Affiche le ticket de caisse imprimable dans un popup
  daily_cloture()       → Bilan de clôture du jour par mode de paiement
  cloture_historique()  → Historique des 30 derniers jours avec filtre par date
  dashboard_stats()     → Statistiques globales : CA, marge, Top 5 produits

SÉCURITÉ :
----------
  - cashier_interface, process_sale, order_receipt, daily_cloture :
    accessibles aux rôles 'admin' ET 'cashier'
  - cloture_historique, dashboard_stats :
    accessibles uniquement au rôle 'admin'

FONCTIONNEMENT DE LA VENTE (process_sale) :
--------------------------------------------
  1. Le caissier compose le panier dans l'interface (JavaScript)
  2. Il clique "Valider l'encaissement"
  3. JavaScript envoie le panier en JSON via une requête AJAX (fetch POST)
  4. process_sale() reçoit le JSON, valide le stock, crée Order + OrderLines
  5. Il retourne un JSON {success: true, order_id: X}
  6. JavaScript ouvre le ticket dans un popup via order_receipt()

HISTORIQUE DES MODIFICATIONS :
-------------------------------
v1.0.0 - Création de cashier_interface, process_sale, order_receipt
v1.1.0 - Ajout de daily_cloture et dashboard_stats
v1.2.0 - Ajout de @transaction.atomic sur process_sale (intégrité des données)
         Optimisation de dashboard_stats avec annotate() ORM (plus de boucle Python)
v1.3.0 - Ajout de cloture_historique (historique 30 jours avec filtre par date)
================================================================================
"""

import json  # Pour lire le JSON envoyé par le JavaScript de la caisse

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse  # Pour retourner du JSON aux requêtes AJAX
from django.db import transaction     # Pour les transactions atomiques (tout ou rien)
from django.db.models import Sum, F   # Sum : agrégation SQL | F : référence à une colonne SQL
from django.utils import timezone     # Pour la gestion du fuseau horaire

from accounts.decorators import role_required
from inventory.models import Product
from .models import Order, OrderLine


# ─────────────────────────────────────────────────────────────────────────────
# VUE : cashier_interface
# ─────────────────────────────────────────────────────────────────────────────
@login_required
@role_required(allowed_roles=['admin', 'cashier'])
def cashier_interface(request):
    """
    Affiche l'interface de caisse tactile.

    Cette page est la vue principale du caissier. Elle affiche :
      - Les boutons de filtrage par catégorie
      - La grille de produits actifs avec prix et stock
      - Le panier (géré côté JavaScript)
      - Le sélecteur de mode de paiement
      - Le bouton de validation

    IMPORTANT : On n'affiche que les produits is_active=True.
    Les produits désactivés (is_active=False) sont invisibles en caisse
    même si leur stock est > 0.

    Paramètre :
        request : la requête HTTP

    Retourne :
        Le template 'sales/cashier_interface.html' avec produits et catégories
    """
    from inventory.models import Category

    # Récupération des produits actifs uniquement, triés par catégorie
    # select_related('category') optimise la requête en faisant un JOIN SQL
    # au lieu d'une requête supplémentaire par produit pour obtenir la catégorie
    products = Product.objects.filter(is_active=True).select_related('category').order_by('category', 'name')

    # Récupération de toutes les catégories pour les boutons de filtre
    categories = Category.objects.all().order_by('name')

    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'sales/cashier_interface.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# VUE : process_sale
# ─────────────────────────────────────────────────────────────────────────────
@login_required
@role_required(allowed_roles=['admin', 'cashier'])
@transaction.atomic  # CRITIQUE : tout ou rien — si une erreur survient, RIEN n'est sauvegardé
def process_sale(request):
    """
    Traite une vente envoyée depuis l'interface de caisse via AJAX.

    Cette vue est le CŒUR FINANCIER de l'application.
    Elle est appelée uniquement en POST par le JavaScript de la caisse.

    Format JSON attendu en entrée :
    {
        "cart": [
            {"id": 1, "name": "Croissant", "price": 1.20, "quantity": 3},
            {"id": 5, "name": "Café", "price": 2.50, "quantity": 1}
        ],
        "payment_mode": "cash"
    }

    Traitement effectué :
      1. Lecture et décodage du JSON reçu
      2. Vérification du stock pour chaque article
      3. Calcul du montant total de la commande
      4. Création de l'objet Order (ticket de caisse)
      5. Création d'un OrderLine par article du panier
      6. Décrémentation du stock pour chaque produit vendu
      7. Retour JSON {success: true, order_id: X}

    Le décorateur @transaction.atomic garantit que si une erreur survient
    à l'étape 5 par exemple, les étapes 4 et 6 sont annulées automatiquement.
    La base de données reste toujours dans un état cohérent.

    Paramètre :
        request : la requête HTTP POST avec le corps JSON

    Retourne :
        JsonResponse({'success': True, 'order_id': X}) en cas de succès
        JsonResponse({'success': False, 'message': '...'}) en cas d'erreur
    """
    # Vérification de la méthode HTTP
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'}, status=405)

    # Décodage du corps de la requête JSON
    # request.body contient les octets bruts du corps POST
    # json.loads() les convertit en dictionnaire Python
    data = json.loads(request.body)
    cart = data.get('cart', [])             # Liste des articles du panier
    payment_mode = data.get('payment_mode', 'cash')  # Mode de paiement choisi

    # Validation : panier vide
    if not cart:
        return JsonResponse({'success': False, 'message': 'Le panier est vide.'})

    # ── Phase 1 : Vérification du stock pour tous les articles ──────────────
    # On vérifie AVANT de créer quoi que ce soit en base
    # pour éviter d'avoir une commande à moitié créée
    total_amount = 0
    validated_items = []  # Liste des produits validés avec leurs objets Django

    for item in cart:
        # Récupération du produit en base (ou 404 si inexistant)
        product = get_object_or_404(Product, id=item['id'])

        # Vérification du stock disponible
        if product.stock_quantity < item['quantity']:
            return JsonResponse({
                'success': False,
                'message': f"Stock insuffisant pour {product.name}. "
                           f"Disponible : {product.stock_quantity} u."
            })

        # Calcul du prix unitaire depuis la base (pas depuis le panier JS)
        # On fait confiance au prix en base, pas au prix envoyé par le client
        # Cela protège contre toute manipulation du prix côté navigateur
        unit_price = product.selling_price
        line_total = unit_price * item['quantity']
        total_amount += line_total

        validated_items.append({
            'product': product,
            'quantity': item['quantity'],
            'unit_price': unit_price,
        })

    # ── Phase 2 : Création de la commande ───────────────────────────────────
    # Order = le ticket de caisse global
    order = Order.objects.create(
        cashier=request.user,         # L'utilisateur actuellement connecté
        total_amount=total_amount,    # Montant total calculé côté serveur
        payment_mode=payment_mode,    # 'cash', 'card' ou 'mobile'
    )

    # ── Phase 3 : Création des lignes et décrémentation du stock ────────────
    for item_data in validated_items:
        product = item_data['product']

        # Création d'une ligne de commande (OrderLine) pour cet article
        # Le prix unitaire est FIGÉ au moment de la vente :
        # si le prix du produit change demain, ce ticket restera correct
        OrderLine.objects.create(
            order=order,
            product=product,
            quantity=item_data['quantity'],
            unit_price=item_data['unit_price'],  # Prix figé
        )

        # Décrémentation du stock
        # F('stock_quantity') - item_data['quantity'] : opération SQL directe
        # Évite les race conditions (deux caissiers qui vendraient le même stock simultanément)
        Product.objects.filter(id=product.id).update(
            stock_quantity=F('stock_quantity') - item_data['quantity']
        )

    # Réponse JSON de succès avec l'identifiant de la commande créée
    # Le JavaScript utilisera order_id pour ouvrir le bon ticket dans le popup
    return JsonResponse({'success': True, 'order_id': order.id})


# ─────────────────────────────────────────────────────────────────────────────
# VUE : order_receipt
# ─────────────────────────────────────────────────────────────────────────────
@login_required
@role_required(allowed_roles=['admin', 'cashier'])
def order_receipt(request, order_id):
    """
    Affiche le ticket de caisse imprimable dans un popup navigateur.

    Cette vue est appelée automatiquement par JavaScript après une vente réussie :
        window.open('/sales/receipt/42/', 'Ticket de Caisse', 'width=400,height=800')

    Le template order_receipt.html est autonome (n'hérite pas de base.html)
    car il est conçu pour l'impression : format rouleau 75mm, CSS @media print,
    pas de navbar, pas de Bootstrap.

    Paramètre :
        request  : la requête HTTP
        order_id : l'identifiant de la commande à afficher

    Retourne :
        Le template 'sales/order_receipt.html' avec la commande et ses lignes
    """
    # Récupération de la commande (ou 404 si inexistante)
    order = get_object_or_404(Order, id=order_id)

    # Récupération de toutes les lignes de cette commande
    # select_related('product') évite une requête SQL supplémentaire par ligne
    order_lines = OrderLine.objects.filter(order=order).select_related('product')

    context = {
        'order': order,
        'order_lines': order_lines,
    }
    return render(request, 'sales/order_receipt.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# VUE : daily_cloture
# ─────────────────────────────────────────────────────────────────────────────
@login_required
@role_required(allowed_roles=['admin', 'cashier'])
def daily_cloture(request):
    """
    Affiche le bilan de clôture de la journée en cours.

    Calcule les totaux encaissés par mode de paiement pour aujourd'hui :
      - Total espèces
      - Total cartes bancaires
      - Total paiements mobiles
      - Total général

    Ces montants permettent au gérant/caissier de vérifier sa caisse physique
    en fin de journée (compter les billets, vérifier le terminal de carte, etc.)

    Paramètre :
        request : la requête HTTP

    Retourne :
        Le template 'sales/daily_cloture.html' avec les totaux du jour
    """
    # Date d'aujourd'hui dans le bon fuseau horaire (Africa/Douala)
    today = timezone.now().date()

    # Filtrage des commandes du jour uniquement
    today_orders = Order.objects.filter(created_at__date=today)

    # Calcul du total par mode de paiement
    # aggregate(Sum(...)) retourne un dictionnaire ou None si aucune commande
    # "or 0" remplace None par 0 pour éviter les erreurs dans le template
    cash_total = today_orders.filter(payment_mode='cash').aggregate(
        Sum('total_amount'))['total_amount__sum'] or 0

    card_total = today_orders.filter(payment_mode='card').aggregate(
        Sum('total_amount'))['total_amount__sum'] or 0

    mobile_total = today_orders.filter(payment_mode='mobile').aggregate(
        Sum('total_amount'))['total_amount__sum'] or 0

    # Total général : somme des trois modes de paiement
    grand_total = cash_total + card_total + mobile_total

    # Nombre de clients servis aujourd'hui
    orders_count = today_orders.count()

    context = {
        'today': today,
        'cash_total': cash_total,
        'card_total': card_total,
        'mobile_total': mobile_total,
        'grand_total': grand_total,
        'orders_count': orders_count,
    }
    return render(request, 'sales/daily_cloture.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# VUE : cloture_historique
# ─────────────────────────────────────────────────────────────────────────────
@login_required
@role_required(allowed_roles=['admin'])
def cloture_historique(request):
    """
    Affiche l'historique des clôtures journalières sur les 30 derniers jours.

    Deux fonctionnalités sur la même page :
      1. Tableau des 30 derniers jours avec CA total et nombre de tickets
      2. Détail complet d'un jour sélectionné (par mode de paiement)

    Navigation :
      - Par défaut, le jour sélectionné est aujourd'hui
      - L'utilisateur peut cliquer sur n'importe quel jour du tableau
        (génère un lien ?date=2026-06-10 dans l'URL)
      - Un sélecteur de date en bas permet d'accéder à n'importe quel jour historique

    Paramètre :
        request : la requête HTTP
                  request.GET.get('date') contient la date sélectionnée si elle est dans l'URL

    Retourne :
        Le template 'sales/cloture_historique.html' avec le tableau et le détail
    """
    from datetime import timedelta, datetime

    # ── Récupération de la date sélectionnée ────────────────────────────────
    # On lit le paramètre 'date' dans l'URL (ex: ?date=2026-06-10)
    selected_date_str = request.GET.get('date', None)

    if selected_date_str:
        try:
            # Conversion de la chaîne 'YYYY-MM-DD' en objet date Python
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            # Si le format est invalide, on utilise aujourd'hui par défaut
            selected_date = timezone.now().date()
    else:
        # Aucune date dans l'URL → on affiche aujourd'hui par défaut
        selected_date = timezone.now().date()

    # ── Calcul du détail pour le jour sélectionné ───────────────────────────
    selected_orders = Order.objects.filter(created_at__date=selected_date)

    selected_cash = selected_orders.filter(payment_mode='cash').aggregate(
        Sum('total_amount'))['total_amount__sum'] or 0

    selected_card = selected_orders.filter(payment_mode='card').aggregate(
        Sum('total_amount'))['total_amount__sum'] or 0

    selected_mobile = selected_orders.filter(payment_mode='mobile').aggregate(
        Sum('total_amount'))['total_amount__sum'] or 0

    selected_total = selected_cash + selected_card + selected_mobile
    selected_count = selected_orders.count()

    # ── Construction du tableau des 30 derniers jours ───────────────────────
    today = timezone.now().date()
    historique = []

    # On itère sur les 30 derniers jours (aujourd'hui inclus)
    for i in range(30):
        # timedelta(days=i) soustrait i jours à aujourd'hui
        # i=0 → aujourd'hui, i=1 → hier, i=2 → avant-hier, etc.
        day = today - timedelta(days=i)

        day_orders = Order.objects.filter(created_at__date=day)

        # Calcul du total et du nombre de tickets pour ce jour
        day_total = day_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        day_count = day_orders.count()

        # Chaque jour est un dictionnaire avec toutes les infos nécessaires au template
        historique.append({
            'date': day,
            'total': day_total,
            'count': day_count,
            'is_selected': day == selected_date,  # True si ce jour est actuellement sélectionné
            'is_today': day == today,              # True si c'est aujourd'hui
        })

    context = {
        'selected_date': selected_date,     # Date du détail affiché à droite
        'selected_cash': selected_cash,
        'selected_card': selected_card,
        'selected_mobile': selected_mobile,
        'selected_total': selected_total,
        'selected_count': selected_count,
        'historique': historique,           # Liste des 30 derniers jours
        'today': today,                     # Utilisé pour le max= du sélecteur de date
    }
    return render(request, 'sales/cloture_historique.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# VUE : dashboard_stats
# ─────────────────────────────────────────────────────────────────────────────
@login_required
@role_required(allowed_roles=['admin'])
def dashboard_stats(request):
    """
    Affiche le tableau de bord des statistiques commerciales globales.

    Calcule sur l'ensemble de l'historique (toutes périodes confondues) :
      - Chiffre d'affaires total
      - Nombre total de tickets
      - Marge brute totale (CA - coûts d'achat)
      - Panier moyen par client
      - Top 5 des produits les plus vendus (en quantité et en CA)

    OPTIMISATION :
    La marge brute est calculée directement en SQL via annotate() et F()
    plutôt qu'une boucle Python sur toutes les lignes de commande.
    Cela génère une seule requête SQL efficace même avec des milliers de ventes.

    Formule marge :
        marge_ligne = (prix_vente - prix_achat) * quantité
        marge_totale = SUM(marge_ligne) sur toutes les OrderLine

    Paramètre :
        request : la requête HTTP

    Retourne :
        Le template 'sales/dashboard_stats.html' avec toutes les statistiques
    """
    # ── Statistiques globales ────────────────────────────────────────────────

    # Chiffre d'affaires total (somme de tous les tickets)
    total_revenue = Order.objects.aggregate(
        Sum('total_amount'))['total_amount__sum'] or 0

    # Nombre total de tickets de caisse
    total_sales_count = Order.objects.count()

    # Panier moyen = CA total / nombre de tickets
    # On évite la division par zéro si aucune vente n'existe encore
    average_basket = (total_revenue / total_sales_count) if total_sales_count > 0 else 0

    # ── Calcul de la marge brute en SQL ─────────────────────────────────────
    # F('product__purchase_price') : référence à la colonne purchase_price
    #   du produit lié à chaque ligne de commande (JOIN automatique)
    # F('unit_price') : prix de vente figé au moment de la vente
    # (unit_price - purchase_price) * quantity = marge de la ligne
    # Sum(...) additionne toutes les marges de toutes les lignes
    margin_data = OrderLine.objects.annotate(
        line_margin=(F('unit_price') - F('product__purchase_price')) * F('quantity')
    ).aggregate(total_margin=Sum('line_margin'))

    total_margin = margin_data['total_margin'] or 0

    # ── Top 5 des produits les plus vendus ──────────────────────────────────
    # values() → GROUP BY product_id, product__name, product__category__name
    # annotate() → COUNT et SUM pour chaque groupe
    # order_by('-total_qty') → tri décroissant par quantité vendue
    top_products = OrderLine.objects.values(
        'product__name',            # Nom du produit (JOIN automatique)
        'product__category__name'   # Nom de la catégorie (double JOIN automatique)
    ).annotate(
        total_qty=Sum('quantity'),                                   # Quantité totale vendue
        total_rev=Sum(F('unit_price') * F('quantity'))               # CA généré par ce produit
    ).order_by('-total_qty')[:5]    # Top 5 seulement (LIMIT 5 en SQL)

    context = {
        'total_revenue': total_revenue,
        'total_sales_count': total_sales_count,
        'average_basket': average_basket,
        'total_margin': total_margin,
        'top_products': top_products,
    }
    return render(request, 'sales/dashboard_stats.html', context)
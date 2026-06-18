from django.db import models
from django.conf import settings
from inventory.models import Product

class Order(models.Model):
    PAYMENT_MODES = [
        ('cash', 'Espèces'),
        ('card', 'Carte Bancaire'),
        ('mobile', 'Paiement Mobile'),
    ]

    # Liaison avec l'utilisateur connecté qui réalise la vente
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders", verbose_name="Caissier")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date et Heure")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Montant Total")
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES, default='cash', verbose_name="Mode de paiement")
    
    def __str__(self):
        return f"Commande #{self.id} du {self.created_at.strftime('%d/%m/%Y %H:%M')} ({self.total_amount}€)"

class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines", verbose_name="Commande")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_lines", verbose_name="Produit")
    quantity = models.IntegerField(verbose_name="Quantité")
    # On fige le prix au moment de l'achat au cas où le gérant modifie le prix du catalogue plus tard
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire appliqué")

    @property
    def total_line_price(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Commande #{self.order.id})"
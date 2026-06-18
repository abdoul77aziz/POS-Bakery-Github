from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom de la catégorie")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Active")

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products", verbose_name="Catégorie")
    name = models.CharField(max_length=150, unique=True, verbose_name="Nom du produit")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix d'achat (marge)")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix de vente")
    stock_quantity = models.IntegerField(default=0, verbose_name="Quantité en stock")
    low_stock_threshold = models.IntegerField(default=5, verbose_name="Seuil d'alerte stock bas")
    is_active = models.BooleanField(default=True, verbose_name="Disponible à la vente (Soft Delete)")

    @property
    def is_low_stock(self):
        """Retourne True si le stock actuel est inférieur ou égal au seuil d'alerte"""
        return self.stock_quantity <= self.low_stock_threshold

    def __str__(self):
        return f"{self.name} - {self.selling_price}€"
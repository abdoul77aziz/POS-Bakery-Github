from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    # Configurer l'affichage dans le panneau de contrôle admin
    model = CustomUser
    list_display = ['username', 'email', 'role', 'phone', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Informations Métier', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations Métier', {'fields': ('role', 'phone')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
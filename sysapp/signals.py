from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Pago


@receiver(pre_save, sender=Pago)
def calcular_estrellas_pago(sender, instance, **kwargs):
    if not instance.pk:
        instance.estrellas = instance.calcular_estrellas()
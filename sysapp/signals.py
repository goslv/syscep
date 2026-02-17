from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Pago


@receiver(pre_save, sender=Pago)
def calcular_estrellas_pago(sender, instance, **kwargs):
    if not instance.pk:  # Solo para nuevos pagos
        # Cambiado de calcular_estrellas() a calcular_puntos()
        instance.puntos = instance.calcular_puntos()
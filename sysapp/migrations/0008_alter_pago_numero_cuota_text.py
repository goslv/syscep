from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sysapp', '0007_remove_pago_importe_parcial_alter_pago_numero_recibo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pago',
            name='numero_cuota',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Nº de Cuota',
                                   help_text='Ej: 1 o 3,4,5'),
        ),
    ]

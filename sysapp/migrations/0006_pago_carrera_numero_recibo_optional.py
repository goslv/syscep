from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sysapp', '0005_carrera_monto_matricula_carrera_monto_mensualidad_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pago',
            name='carrera',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name='pagos', to='sysapp.carrera', verbose_name='Carrera'),
        ),
        migrations.AlterField(
            model_name='pago',
            name='numero_recibo',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True, verbose_name='Nº de Recibo'),
        ),
    ]

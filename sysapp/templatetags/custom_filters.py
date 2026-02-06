from django import template

register = template.Library()


@register.filter(name='formato_guaranies')
def formato_guaranies(value):
    """
    Formatea números a formato paraguayo con puntos como separadores de miles
    Ejemplo: 1000000 -> 1.000.000
    """
    try:
        # Convertir a entero (eliminar decimales)
        value = int(float(value))

        # Convertir a string y formatear
        value_str = str(value)

        # Si es negativo, guardar el signo
        negative = value < 0
        if negative:
            value_str = value_str[1:]

        # Agregar puntos cada 3 dígitos desde la derecha
        result = []
        for i, digit in enumerate(reversed(value_str)):
            if i > 0 and i % 3 == 0:
                result.append('.')
            result.append(digit)

        formatted = ''.join(reversed(result))

        # Agregar signo negativo si corresponde
        if negative:
            formatted = '-' + formatted

        return formatted
    except (ValueError, TypeError):
        return value
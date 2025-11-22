import dateparser
from datetime import datetime
from django.utils import timezone

def parse_user_date(texto, default_hour=10, default_minute=0):
    """
    Convierte texto en datetime (timezone aware) y valida que no sea pasado.
    Devuelve None si no puede interpretarse o si la fecha es anterior a ahora.
    """
    if not texto or not texto.strip():
        return None

    texto = texto.lower().strip()
    now = timezone.now()

    fecha_dp = dateparser.parse(
        texto,
        languages=['es'],
        settings={
            'PREFER_DATES_FROM': 'future',
            'RELATIVE_BASE': now.replace(tzinfo=None),
            'RETURN_AS_TIMEZONE_AWARE': False
        }
    )

    if fecha_dp:
        if fecha_dp.hour == 0 and fecha_dp.minute == 0 and ":" not in texto:
            fecha_dp = fecha_dp.replace(hour=default_hour, minute=default_minute)

        fecha_dp = timezone.make_aware(fecha_dp, timezone.get_current_timezone())

        if fecha_dp < now:
            return None

        return fecha_dp

    formatos = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d/%m/%y",
        "%d-%m-%y",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M",
        "%Y-%m-%d %H:%M",
        "%d/%m/%y %H:%M",
        "%d-%m-%y %H:%M",
    ]

    for f in formatos:
        try:
            fecha_manual = datetime.strptime(texto, f)
            if 'H' not in f and '%H' not in f:
                fecha_manual = fecha_manual.replace(hour=default_hour, minute=default_minute)
            fecha_manual = timezone.make_aware(fecha_manual, timezone.get_current_timezone())
            if fecha_manual < now:
                return None
            return fecha_manual
        except Exception:
            continue

    return None

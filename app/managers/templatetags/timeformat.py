from django import template

register = template.Library()

@register.filter
def hhmm(total_minutes):
    try:
        m = int(total_minutes)
    except (TypeError, ValueError):
        return "00:00"
    sign = "-" if m < 0 else ""
    m = abs(m)
    h, mm = divmod(m, 60) # 60で割った商と余りを取得
    return f"{sign}{h:02d}:{mm:02d}"

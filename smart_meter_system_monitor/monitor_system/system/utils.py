from .models import SystemOption

def get_option(key, default=None):
    try:
        opt = SystemOption.objects.get(key=key)
        return opt.value
    except SystemOption.DoesNotExist:
        return default


def get_float_option(key, default=0.0):
    try:
        return float(get_option(key, default))
    except ValueError:
        return default
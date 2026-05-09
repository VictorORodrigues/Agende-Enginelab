from django.conf import settings
from django.core.cache import cache
from django.utils.crypto import salted_hmac


def get_client_ip(request):
    if not request:
        return ''
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _digest(ip, username):
    raw = f'{ip}|{username}'.strip().lower()
    return salted_hmac('account.login', raw).hexdigest()


def _key(prefix, ip, username):
    return f'account:{prefix}:{_digest(ip, username)}'


def limits():
    return {
        'max_per_minute': getattr(settings, 'ACCOUNT_MAX_FAILED_LOGINS_PER_MINUTE', 5),
        'lockout_threshold': getattr(settings, 'ACCOUNT_LOCKOUT_THRESHOLD', 10),
        'lockout_seconds': getattr(settings, 'ACCOUNT_LOCKOUT_SECONDS', 15 * 60),
        'captcha_after': getattr(settings, 'ACCOUNT_CAPTCHA_AFTER_FAILS', 3),
    }


def is_locked(ip, username):
    return bool(cache.get(_key('login_lock', ip, username)))


def failure_counts(ip, username):
    per_minute = cache.get(_key('login_minute', ip, username), 0) or 0
    consecutive = cache.get(_key('login_fails', ip, username), 0) or 0
    return per_minute, consecutive


def register_failure(ip, username):
    l = limits()
    minute_key = _key('login_minute', ip, username)
    fails_key = _key('login_fails', ip, username)
    lock_key = _key('login_lock', ip, username)

    try:
        minute = cache.incr(minute_key)
    except ValueError:
        cache.set(minute_key, 1, timeout=60)
        minute = 1

    try:
        fails = cache.incr(fails_key)
    except ValueError:
        cache.set(fails_key, 1, timeout=l['lockout_seconds'])
        fails = 1

    if minute >= l['max_per_minute'] or fails >= l['lockout_threshold']:
        cache.set(lock_key, 1, timeout=l['lockout_seconds'])
        cache.delete(minute_key)
        cache.delete(fails_key)


def register_success(ip, username):
    cache.delete(_key('login_minute', ip, username))
    cache.delete(_key('login_fails', ip, username))
    cache.delete(_key('login_lock', ip, username))

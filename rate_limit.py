import time

def rate_limited(context, key, seconds=1.5):
    now = time.time()
    last = context.user_data.get(key, 0)
    if now - last < seconds:
        return True
    context.user_data[key] = now
    return False

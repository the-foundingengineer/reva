import traceback
try:
    from app.cache.redis import is_already_received
    print("Success")
except Exception:
    traceback.print_exc()

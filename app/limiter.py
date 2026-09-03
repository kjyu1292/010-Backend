import os

from slowapi import Limiter
from slowapi.util import get_remote_address

import app.environment


"""----------------------------"""
limiter_enabled = True if os.getenv("LIMITER_ENABLED") == "true" else False

print(f"LIMITER_ENABLED={os.getenv('LIMITER_ENABLED')}")
print(f"limiter_enabled={limiter_enabled}")


"""----------------------------"""
limiter = Limiter(key_func = get_remote_address, enabled = limiter_enabled)

print(f"limiter.enabled     = {limiter.enabled}")

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

import app.environment


"""----------------------------"""
limiter_enabled = True if os.getenv("LIMITER_ENABLED") == "true" else False


"""----------------------------"""
limiter = Limiter(key_func = get_remote_address, enabled = limiter_enabled)



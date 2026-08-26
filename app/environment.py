import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
env_local = ROOT_DIR / ".env.local"
env_files = list(ROOT_DIR.glob(".env*"))

if env_local.exists():
    env_file = env_local
elif len(env_files) == 1:
    env_file = env_files[0]
else:
    raise RuntimeError(
            f"Could not determine which environment file to load."
            f"Found: {[file.name for file in env_files]}"
    )   

load_dotenv(env_file)

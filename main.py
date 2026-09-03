import os
import uvicorn

if __name__ == "__main__":
    PORT = int(os.getenv("APP_PORT", "8000"))
    UVICORN_WORKERS = int(os.getenv("UVICORN_WORKERS", "4"))
    
    uvicorn.run(
        "app.app:app"
        , host = "0.0.0.0"
        , port = PORT
        , workers = UVICORN_WORKERS
        , proxy_headers = True
        , forwarded_allow_ips = "*"
    )

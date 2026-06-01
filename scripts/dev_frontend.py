#!/usr/bin/env python3
"""Servidor estático de DESARROLLO para el frontend, SIN caché.

Sirve la carpeta `frontend/` con cabeceras `Cache-Control: no-store`, de modo que
el navegador siempre cargue la última versión de los módulos JS/CSS (evita el típico
problema de "módulo viejo cacheado" al iterar la SPA).

Uso:
    python3 scripts/dev_frontend.py            # puerto 8080
    PORT=9000 python3 scripts/dev_frontend.py  # otro puerto
"""
import http.server
import os
import socketserver

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRECTORY = os.path.join(ROOT, "frontend")
PORT = int(os.environ.get("PORT", "8080"))


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def main() -> None:
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), NoCacheHandler) as httpd:
        print(f"Frontend (no-cache) sirviendo {DIRECTORY} en http://localhost:{PORT}", flush=True)
        httpd.serve_forever()


if __name__ == "__main__":
    main()

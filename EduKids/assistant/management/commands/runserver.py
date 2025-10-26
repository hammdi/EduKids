"""
Custom runserver command that launches Daphne (ASGI) with auto-reload.
This enables WebSocket support while keeping the developer-friendly auto-reload feature.
"""
import os
import sys
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = (
        "Lance Daphne (serveur ASGI) avec auto-reload pour WebSockets.\n"
        "Usage: python manage.py runserver [addrport]\n"
        "Exemple: python manage.py runserver 0.0.0.0:8000"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "addrport",
            nargs="?",
            default="127.0.0.1:8000",
            help="Adresse et port (défaut: 127.0.0.1:8000)",
        )
        parser.add_argument(
            "--noreload",
            action="store_true",
            help="Désactiver l'auto-reload",
        )

    def handle(self, *args, **options):
        # Parse l'adresse et le port
        addrport = options["addrport"]
        if ":" in addrport:
            addr, port = addrport.rsplit(":", 1)
        else:
            addr = "127.0.0.1"
            port = addrport

        # Récupère l'application ASGI depuis settings
        asgi_app = getattr(settings, "ASGI_APPLICATION", None)
        if not asgi_app:
            self.stderr.write(
                self.style.ERROR(
                    "ASGI_APPLICATION n'est pas définie dans settings.py"
                )
            )
            sys.exit(1)

        # Convertit 'EduKids.asgi.application' en 'EduKids.asgi:application' pour Daphne
        # On sépare le module du callable (dernier élément après le dernier point)
        if ":" not in asgi_app:
            parts = asgi_app.rsplit(".", 1)
            if len(parts) == 2:
                asgi_module = f"{parts[0]}:{parts[1]}"
            else:
                asgi_module = asgi_app
        else:
            asgi_module = asgi_app

        # Commande Daphne
        cmd = [
            sys.executable,
            "-m",
            "daphne",
            "-b", addr,
            "-p", port,
            asgi_module,
        ]

        def run_daphne():
            self.stdout.write(
                self.style.SUCCESS(
                    f"🚀 Démarrage de Daphne (ASGI + WebSockets) sur http://{addr}:{port}"
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    "⚡ Auto-reload activé - le serveur redémarrera à chaque modification"
                )
            )
            try:
                subprocess.call(cmd)
            except KeyboardInterrupt:
                self.stdout.write("\n👋 Serveur arrêté")
            except FileNotFoundError:
                self.stderr.write(
                    self.style.ERROR(
                        "❌ Daphne n'est pas installé. Lancez: pip install daphne"
                    )
                )
                sys.exit(1)

        # Lance avec ou sans auto-reload
        if options["noreload"]:
            run_daphne()
        else:
            # Utilise l'autoreloader de Django
            from django.utils import autoreload
            autoreload.run_with_reloader(run_daphne)

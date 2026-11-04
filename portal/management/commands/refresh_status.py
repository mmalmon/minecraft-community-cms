import time
from concurrent.futures import ThreadPoolExecutor
from django.core.management.base import BaseCommand
from django.utils import timezone
from portal.models import Server
from portal.status import query

class Command(BaseCommand):
    help = "Odśwież zapisany status serwerów Java (bez dostępu do Docker API)."
    def add_arguments(self, parser):
        parser.add_argument("--loop", action="store_true")
        parser.add_argument("--interval", type=int, default=30)
    def handle(self, *args, **options):
        while True:
            targets = list(Server.objects.filter(is_published=True, status_enabled=True).values_list("pk", "status_host", "status_port"))
            def check(target):
                pk, host, port = target
                try:
                    online, maximum, version = query(host, port)
                    return pk, True, online, maximum, version
                except (OSError, ValueError, TypeError, KeyError, RecursionError, OverflowError):
                    return pk, False, 0, 0, ""
            with ThreadPoolExecutor(max_workers=4) as pool:
                for pk, state, online, maximum, version in pool.map(check, targets):
                    Server.objects.filter(pk=pk).update(status_online=state, players_online=online, players_max=maximum, reported_version=version, status_checked_at=timezone.now())
            if not options["loop"]:
                return
            time.sleep(max(15, options["interval"]))

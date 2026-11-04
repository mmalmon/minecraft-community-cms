from datetime import timedelta
from io import BytesIO
from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, SimpleTestCase
from django.utils import timezone
from .models import Entry, Server, SiteSettings
from .status import varint, read_varint, read_exact
import json, struct

class PortalTests(TestCase):
    def make_server(self, **kwargs):
        return Server.objects.create(name="Mój świat", slug="moj-swiat", address="mc.example.org", description="Opis", **kwargs)

    def test_admin_requires_login(self):
        self.assertRedirects(self.client.get("/admin/"), "/admin/login/?next=/admin/", fetch_redirect_response=False)

    def test_no_network_calls_on_public_requests(self):
        self.make_server(is_published=True, status_enabled=True, status_host="private-service")
        with patch("socket.create_connection", side_effect=AssertionError("network")):
            self.assertEqual(self.client.get("/").status_code, 200)
            result = self.client.get("/status/").json()
        self.assertNotIn("private-service", json.dumps(result))
        self.assertIsNone(result["servers"][0]["online"])

    def test_drafts_and_future_entries_are_not_public(self):
        for slug, published, date in [("draft", False, timezone.now()), ("future", True, timezone.now()+timedelta(days=1))]:
            Entry.objects.create(title=slug, slug=slug, kind="news", intro="opis", body="prywatne", is_published=published, published_at=date)
            self.assertEqual(self.client.get("/wpis/"+slug+"/").status_code, 404)
        self.assertNotContains(self.client.get("/aktualnosci/"), "prywatne")

    def test_hidden_servers_are_not_public(self):
        self.make_server(is_published=False)
        self.assertNotContains(self.client.get("/"), "Mój świat")
        self.assertEqual(self.client.get("/serwery/moj-swiat/").status_code, 404)
        self.assertEqual(self.client.get("/status/").json()["servers"], [])

    def test_text_is_escaped(self):
        self.make_server(is_published=True, join_instructions="<script>alert(1)</script>")
        response = self.client.get("/serwery/moj-swiat/")
        self.assertNotContains(response, "<script>")
        self.assertContains(response, "&lt;script&gt;")

    def test_admin_can_configure_brand_and_more_than_two_servers(self):
        SiteSettings.objects.create(name="Nasza społeczność", tagline="Witaj w grze")
        for i in range(3):
            Server.objects.create(name="Świat "+str(i), slug="world-"+str(i), address="mc.example.org", description="Opis", is_published=True)
        response = self.client.get("/")
        self.assertContains(response, "Nasza społeczność")
        self.assertContains(response, "Witaj w grze")
        self.assertContains(response, "Świat 2")

    def test_status_requires_host_and_valid_port(self):
        s = self.make_server(status_enabled=True)
        with self.assertRaises(ValidationError): s.full_clean()
        s.status_host = "http://127.0.0.1/path"
        with self.assertRaises(ValidationError): s.full_clean()
        s.status_host = "paper"
        s.status_port = 0
        with self.assertRaises(ValidationError): s.full_clean()

    def test_worker_stores_status_and_stale_status_becomes_unknown(self):
        s = self.make_server(is_published=True, status_enabled=True, status_host="paper")
        with patch("portal.management.commands.refresh_status.query", return_value=(2,10,"Paper")):
            call_command("refresh_status")
        self.assertTrue(self.client.get("/status/").json()["servers"][0]["online"])
        Server.objects.filter(pk=s.pk).update(status_checked_at=timezone.now()-timedelta(minutes=3))
        self.assertIsNone(self.client.get("/status/").json()["servers"][0]["online"])

    def test_worker_handles_connection_failure(self):
        self.make_server(is_published=True, status_enabled=True, status_host="paper")
        with patch("portal.management.commands.refresh_status.query", side_effect=TimeoutError):
            call_command("refresh_status")
        self.assertFalse(self.client.get("/status/").json()["servers"][0]["online"])

    def test_health(self):
        self.assertEqual(self.client.get("/health/").content, b"ok\n")


class OloCraftImportTests(TestCase):
    def metadata(self):
        from types import SimpleNamespace
        return SimpleNamespace(read_text=lambda **_: json.dumps({
            "status_host": "192.0.2.10",
            "servers": [{"slug": "mc1", "name": "MC1", "edition": "Paper", "host": "mc.example.org", "port": 25565, "description": "Własny świat"}],
            "dragonlife_html": '{% block content %}<h1>DragonLife</h1><p>10 serc, zakres 1–30.</p><code>/dragonlife sethearts &lt;gracz&gt;</code>{% endblock %}'
        }))

    def test_import_keeps_accounts_is_repeatable_and_maps_editor_permissions(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        from .management.commands.import_olocraft import Command
        user = get_user_model().objects.create_user("existing-editor", password="ExistingPassword123!", is_staff=True)
        original_hash = user.password
        legacy_type = ContentType.objects.create(app_label="content", model="post")
        permission = Permission.objects.create(content_type=legacy_type, codename="change_post", name="Change post")
        group = Group.objects.create(name="Redakcja OloCraft")
        group.permissions.add(permission)
        user.groups.add(group)
        command = Command()
        command.handle(metadata=self.metadata())
        command.handle(metadata=self.metadata())
        self.assertEqual(Server.objects.count(), 1)
        self.assertEqual(Entry.objects.filter(slug="dragonlife").count(), 1)
        user.refresh_from_db()
        self.assertEqual(user.password, original_hash)
        self.assertTrue(user.has_perm("portal.change_entry"))
        self.assertFalse(user.has_perm("auth.change_user"))
        self.assertFalse(user.has_perm("portal.delete_entry"))
        self.assertFalse(user.has_perm("portal.change_server"))
        command.handle(metadata=self.metadata(), community_editors=True)
        user = get_user_model().objects.get(pk=user.pk)
        self.assertTrue(user.has_perm("portal.change_server"))
        self.assertTrue(user.has_perm("portal.change_sitesettings"))
        self.assertFalse(user.has_perm("portal.delete_server"))
        self.assertFalse(user.has_perm("auth.change_user"))
        page = self.client.get("/wpis/dragonlife/")
        self.assertContains(page, "/dragonlife sethearts &lt;gracz&gt;")
        self.assertRedirects(self.client.get("/dragonlife/"), "/wpis/dragonlife/", status_code=301, fetch_redirect_response=False)
        Entry.objects.filter(slug="dragonlife").update(is_published=False)
        self.assertEqual(self.client.get("/dragonlife/").status_code, 404)

    def test_original_news_and_tutorial_slugs_can_collide_without_losing_text(self):
        from django.db import connection
        from .management.commands.import_olocraft import Command
        with connection.cursor() as cursor:
            for table in ("content_post", "content_tutorial"):
                cursor.execute("CREATE TABLE "+table+" (title text, slug text, intro text, body text, is_published bool, published_at text)")
                cursor.execute("INSERT INTO "+table+" VALUES (%s,%s,%s,%s,%s,%s)", ["Tytuł", "ten-sam", "Opis", table, True, timezone.now().isoformat()])
        Command().handle(metadata=self.metadata())
        self.assertEqual(Entry.objects.count(), 3)
        self.assertContains(self.client.get("/wpis/ten-sam/"), "content_post")
        self.assertContains(self.client.get("/wpis/tutorial-ten-sam/"), "content_tutorial")
        self.assertRedirects(self.client.get("/poradniki/ten-sam/"), "/wpis/tutorial-ten-sam/", status_code=301, fetch_redirect_response=False)
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM content_post")
            self.assertEqual(cursor.fetchone()[0], 1)


class ProtocolTests(SimpleTestCase):
    def reader(self, data):
        buffer=BytesIO(data)
        class Reader:
            def recv(self, count): return buffer.read(count)
            def settimeout(self, timeout): pass
        return Reader()
    def test_invalid_varint_and_oversized_packets_are_rejected(self):
        import time
        with self.assertRaises(ValueError): read_varint(self.reader(b"\xff"*6), time.monotonic()+2)
        with self.assertRaises(ValueError): read_exact(self.reader(b""), 65537, time.monotonic()+2)
    def test_parse_fragmented_response(self):
        from .status import query
        payload=json.dumps({"players":{"online":3,"max":12},"version":{"name":"Paper"}}).encode()
        data=varint(1+len(varint(len(payload)))+len(payload))+b"\x00"+varint(len(payload))+payload
        buffer=BytesIO(data)
        class Conn:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def settimeout(self,value): pass
            def sendall(self,data): pass
            def recv(self,count): return buffer.read(min(count,2))
        with patch("socket.create_connection",return_value=Conn()):
            self.assertEqual(query("paper",25565),(3,12,"Paper"))

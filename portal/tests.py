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

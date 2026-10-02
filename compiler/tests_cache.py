"""Кеш (Redis в проде): что кешируется, что сбрасывается, и что сайт живёт без Redis."""
import json
import os
from unittest import mock, skipUnless

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings

from . import cache as oc_cache
from .models import Snippet

PASSWORD = "Krepkiy-parol-42"
DEAD_REDIS = {"default": {
    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    "LOCATION": "redis://127.0.0.1:1/0",  # порт, где точно никого нет
    "OPTIONS": {"socket_connect_timeout": 0.2, "socket_timeout": 0.2},
}}


def call(client, url, data=None, method="post"):
    return getattr(client, method)(url, json.dumps(data or {}), content_type="application/json")


class CachedReadsTests(TestCase):
    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.leha = User.objects.create_user("leha", password=PASSWORD)
        self.owner = Client()
        self.owner.force_login(self.leha)
        self.anon = Client()

    def test_language_catalog_is_cached(self):
        with mock.patch("compiler.engine.language_catalog", return_value=[{"slug": "x"}]) as catalog:
            for _ in range(3):
                self.assertEqual(self.anon.get("/api/languages/").json()["languages"], [{"slug": "x"}])
        self.assertEqual(catalog.call_count, 1)

    def test_snippet_read_from_cache_and_invalidated_on_save(self):
        snippet = Snippet.objects.create(language="python", code="print(1)\n", owner=self.leha)
        url = f"/api/snippets/{snippet.pk}/"
        self.assertEqual(self.anon.get(url).json()["code"], "print(1)\n")
        with self.assertNumQueries(0):  # аноним, кеш тёплый — в базу не ходим вообще
            self.assertEqual(self.anon.get(url).status_code, 200)
        call(self.owner, url, {"code": "print(2)\n"}, "patch")
        self.assertEqual(self.anon.get(url).json()["code"], "print(2)\n")
        self.assertTrue(self.owner.get(url).json()["is_owner"])  # is_owner считается не из кеша
        self.assertFalse(self.anon.get(url).json()["is_owner"])

    def test_private_is_not_leaked_by_cache(self):
        snippet = Snippet.objects.create(language="python", code="secret", owner=self.leha, visibility="private")
        url = f"/api/snippets/{snippet.pk}/"
        self.assertEqual(self.owner.get(url).status_code, 200)  # прогрели кеш владельцем
        self.assertEqual(self.anon.get(url).status_code, 404)
        self.assertEqual(self.anon.get(f"/s/{snippet.pk}/").status_code, 404)

    def test_fork_and_delete_update_cached_projects(self):
        source = Snippet.objects.create(language="python", code="x", owner=self.leha, title="Исходник")
        other = Client()
        other.force_login(get_user_model().objects.create_user("brat", password=PASSWORD))
        self.assertEqual(self.anon.get(f"/api/snippets/{source.pk}/").json()["forks"], 0)
        fork = call(other, f"/api/snippets/{source.pk}/fork/").json()
        self.assertEqual(self.anon.get(f"/api/snippets/{source.pk}/").json()["forks"], 1)
        self.assertEqual(self.anon.get(f"/api/snippets/{fork['id']}/").json()["forked_from"]["id"], source.pk)
        self.owner.delete(f"/api/snippets/{source.pk}/")
        self.assertIsNone(self.anon.get(f"/api/snippets/{fork['id']}/").json()["forked_from"])
        self.assertEqual(self.anon.get(f"/api/snippets/{source.pk}/").status_code, 404)

    def test_page_view_counter_does_not_break_cache(self):
        snippet = Snippet.objects.create(language="python", code="print(1)\n")
        for _ in range(3):
            self.assertEqual(self.anon.get(f"/s/{snippet.pk}/").status_code, 200)
        snippet.refresh_from_db()
        self.assertEqual(snippet.views, 3)

    def test_profile_cache_follows_visibility(self):
        snippet = Snippet.objects.create(language="python", code="x", owner=self.leha, title="Мой")
        self.assertEqual(self.anon.get("/api/users/leha/").json()["projects"], [])
        call(self.owner, f"/api/snippets/{snippet.pk}/", {"visibility": "public"}, "patch")
        self.assertEqual([p["title"] for p in self.anon.get("/api/users/leha/").json()["projects"]], ["Мой"])

    def test_library_is_cached(self):
        first = self.anon.get("/api/library/?language=python").json()
        with mock.patch("compiler.library.catalog", side_effect=AssertionError("должно прийти из кеша")):
            self.assertEqual(self.anon.get("/api/library/?language=python").json(), first)


@override_settings(CACHES=DEAD_REDIS)
class RedisDownTests(TestCase):
    """Redis лёг — сайт работает: кеш просто не используется, rate limit не применяется."""

    def test_site_works_without_cache(self):
        with self.assertLogs("compiler.cache", level="WARNING"):
            self.assertEqual(self.client.get("/api/languages/").status_code, 200)
        snippet = Snippet.objects.create(language="python", code="print(1)\n")
        self.assertEqual(self.client.get(f"/api/snippets/{snippet.pk}/").json()["code"], "print(1)\n")
        self.assertFalse(oc_cache.rate_hit("rl:test", limit=1))
        self.assertEqual(oc_cache.cached("k", 10, lambda: 42), 42)


@skipUnless(os.environ.get("REDIS_TEST_URL"), "нужен настоящий Redis (REDIS_TEST_URL) — в CI он есть")
class RealRedisTests(TestCase):
    def test_redis_backend_roundtrip_and_rate_limit(self):
        from django.conf import settings
        self.assertIn("RedisCache", settings.CACHES["default"]["BACKEND"])
        cache.clear()
        self.assertEqual(oc_cache.cached("roundtrip", 10, lambda: {"a": [1, 2]}), {"a": [1, 2]})
        self.assertEqual(cache.get("roundtrip"), {"a": [1, 2]})
        hits = [oc_cache.rate_hit("rl:real", limit=2) for _ in range(4)]
        self.assertEqual(hits, [False, False, True, True])

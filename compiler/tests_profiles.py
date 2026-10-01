"""Этап C: почта и сброс пароля, смена пароля, видимость проектов, профиль, вход через GitHub / Google."""
import json
import re
from unittest import mock
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings

from . import oauth
from .models import Snippet, SocialAccount

PASSWORD = "Krepkiy-parol-42"
OAUTH = {
    "github": {"client_id": "gh-id", "client_secret": "gh-secret"},
    "google": {"client_id": "gg-id", "client_secret": "gg-secret"},
}


def post(client, url, data=None, method="post"):
    return getattr(client, method)(url, json.dumps(data or {}), content_type="application/json")


class EmailAndPasswordTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_register_with_email(self):
        res = post(self.client, "/api/auth/register/", {"username": "leha", "password": PASSWORD,
                                                        "email": "Leha@Example.com"})
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(res.json()["user"]["email"], "Leha@example.com")  # Django приводит домен к нижнему регистру
        self.assertTrue(res.json()["user"]["has_password"])
        other = Client()
        res = post(other, "/api/auth/register/",
                   {"username": "brat", "password": PASSWORD, "email": "leha@example.COM"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("уже привязана", res.json()["error"])
        res = post(other, "/api/auth/register/", {"username": "brat", "password": PASSWORD, "email": "не почта"})
        self.assertIn("не похоже", res.json()["error"])

    def test_password_reset_flow(self):
        get_user_model().objects.create_user("leha", password="old-Parol-123", email="leha@example.com")
        res = post(self.client, "/api/auth/password-reset/", {"email": "LEHA@example.com"})
        self.assertEqual(res.json(), {"ok": True})
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["leha@example.com"])
        link = re.search(r"http://testserver/reset/(\S+)/(\S+)/", mail.outbox[0].body)
        self.assertIsNotNone(link, mail.outbox[0].body)
        uid, token = link.groups()

        page = self.client.get(f"/reset/{uid}/{token}/")
        self.assertContains(page, f'"token": "{token}"')

        bad = post(self.client, "/api/auth/password-reset/confirm/", {"uid": uid, "token": token, "password": "123"})
        self.assertEqual(bad.status_code, 400)  # слабый пароль отклоняют валидаторы, токен ещё жив
        res = post(self.client, "/api/auth/password-reset/confirm/", {"uid": uid, "token": token, "password": PASSWORD})
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(res.json()["user"]["username"], "leha")  # сразу вошёл
        again = post(Client(), "/api/auth/password-reset/confirm/",
                     {"uid": uid, "token": token, "password": "Drugoy-parol-77"})
        self.assertEqual(again.status_code, 400)  # одноразовая ссылка
        self.assertTrue(get_user_model().objects.get(username="leha").check_password(PASSWORD))

    def test_reset_does_not_reveal_unknown_email(self):
        res = post(self.client, "/api/auth/password-reset/", {"email": "nobody@example.com"})
        self.assertEqual(res.json(), {"ok": True})
        self.assertEqual(mail.outbox, [])

    def test_change_password_and_email(self):
        get_user_model().objects.create_user("leha", password=PASSWORD)
        self.client.login(username="leha", password=PASSWORD)
        res = post(self.client, "/api/auth/password/", {"old_password": "wrong", "new_password": "Novyi-parol-55"})
        self.assertEqual(res.status_code, 400)
        res = post(self.client, "/api/auth/password/", {"old_password": PASSWORD, "new_password": "Novyi-parol-55"})
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(self.client.get("/api/auth/me/").json()["user"]["username"], "leha")  # сессия жива
        res = post(self.client, "/api/auth/me/", {"email": "new@example.com", "password": "wrong"}, "patch")
        self.assertEqual(res.status_code, 400)
        res = post(self.client, "/api/auth/me/", {"email": "new@example.com", "password": "Novyi-parol-55"}, "patch")
        self.assertEqual(res.json()["user"]["email"], "new@example.com")


class VisibilityAndProfileTests(TestCase):
    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.leha = User.objects.create_user("leha", password=PASSWORD)
        self.owner = Client()
        self.owner.force_login(self.leha)
        self.other = Client()
        self.other.force_login(User.objects.create_user("brat", password=PASSWORD))
        self.anon = Client()

    def make(self, title, visibility):
        snippet = Snippet.objects.create(language="python", code="print(1)\n", title=title, owner=self.leha)
        res = post(self.owner, f"/api/snippets/{snippet.pk}/", {"visibility": visibility}, "patch")
        self.assertEqual(res.status_code, 200, res.content)
        return snippet

    def test_private_is_hidden_from_everyone_but_owner(self):
        secret = self.make("Секрет", "private")
        for client in (self.other, self.anon):
            self.assertEqual(client.get(f"/s/{secret.pk}/").status_code, 404)
            self.assertEqual(client.get(f"/api/snippets/{secret.pk}/").status_code, 404)
            self.assertEqual(client.get(f"/s/{secret.pk}/raw/").status_code, 404)
            self.assertEqual(client.get(f"/s/{secret.pk}/zip/").status_code, 404)
        self.assertEqual(post(self.other, f"/api/snippets/{secret.pk}/fork/").status_code, 404)
        self.assertEqual(self.owner.get(f"/s/{secret.pk}/").status_code, 200)
        self.assertEqual(self.owner.get(f"/api/snippets/{secret.pk}/").json()["visibility"], "private")

    def test_visibility_validation_and_ownership(self):
        snippet = self.make("Проект", "unlisted")
        res = post(self.owner, f"/api/snippets/{snippet.pk}/", {"visibility": "everyone"}, "patch")
        self.assertEqual(res.status_code, 400)
        res = post(self.other, f"/api/snippets/{snippet.pk}/", {"visibility": "private"}, "patch")
        self.assertEqual(res.status_code, 403)

    def test_profile_lists_only_public(self):
        self.make("Публичный", "public")
        self.make("По ссылке", "unlisted")
        self.make("Секрет", "private")
        data = self.anon.get("/api/users/LEHA/").json()  # регистр логина не важен
        self.assertEqual(data["username"], "leha")
        self.assertEqual([p["title"] for p in data["projects"]], ["Публичный"])
        page = self.anon.get("/u/leha/")
        self.assertContains(page, "Публичный")
        self.assertNotContains(page, "Секрет")
        self.assertNotContains(page, "По ссылке")
        self.assertEqual(self.anon.get("/u/nobody/").status_code, 404)
        self.assertContains(self.owner.get("/api/projects/"), '"visibility": "private"')


@override_settings(OAUTH_PROVIDERS=OAUTH)
class OAuthTests(TestCase):
    def fake_github(self, uid=42, login="octocat", email="octo@example.com", verified=True):
        def http_json(url, data=None, token=None):
            if url.endswith("/access_token"):
                self.assertEqual(data["code"], "the-code")
                return {"access_token": "tok"}
            if url.endswith("/user"):
                self.assertEqual(token, "tok")
                return {"id": uid, "login": login}
            if url.endswith("/user/emails"):
                return [{"email": email, "primary": True, "verified": verified}]
            raise AssertionError(url)
        return mock.patch.object(oauth, "http_json", side_effect=http_json)

    def start(self, client, provider="github", next_url="/s/abc/"):
        res = client.get(f"/auth/{provider}/login/?next={next_url}")
        self.assertEqual(res.status_code, 302)
        query = parse_qs(urlparse(res["Location"]).query)
        return query

    def test_redirect_to_provider(self):
        query = self.start(self.client)
        self.assertEqual(query["client_id"], ["gh-id"])
        self.assertEqual(query["redirect_uri"], ["http://testserver/auth/github/callback/"])
        self.assertTrue(query["state"][0])
        google = self.start(Client(), "google")
        self.assertEqual(google["response_type"], ["code"])

    def test_login_creates_user_once(self):
        state = self.start(self.client)["state"][0]
        with self.fake_github():
            res = self.client.get(f"/auth/github/callback/?code=the-code&state={state}")
        self.assertEqual(res["Location"], "/s/abc/")
        user = get_user_model().objects.get(username="octocat")
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.email, "octo@example.com")
        self.assertEqual(self.client.get("/api/auth/me/").json()["user"]["providers"], ["github"])

        again = Client()
        state = self.start(again)["state"][0]
        with self.fake_github():
            again.get(f"/auth/github/callback/?code=the-code&state={state}")
        self.assertEqual(again.get("/api/auth/me/").json()["user"]["username"], "octocat")
        self.assertEqual(SocialAccount.objects.count(), 1)

    def test_verified_email_links_existing_account(self):
        get_user_model().objects.create_user("leha", password=PASSWORD, email="octo@example.com")
        state = self.start(self.client)["state"][0]
        with self.fake_github():
            self.client.get(f"/auth/github/callback/?code=the-code&state={state}")
        self.assertEqual(self.client.get("/api/auth/me/").json()["user"]["username"], "leha")

    def test_unverified_email_does_not_link(self):
        get_user_model().objects.create_user("leha", password=PASSWORD, email="octo@example.com")
        state = self.start(self.client)["state"][0]
        with self.fake_github(verified=False):
            self.client.get(f"/auth/github/callback/?code=the-code&state={state}")
        me = self.client.get("/api/auth/me/").json()["user"]
        self.assertEqual(me["username"], "octocat")
        self.assertEqual(me["email"], "")

    def test_username_collision_gets_suffix(self):
        get_user_model().objects.create_user("octocat", password=PASSWORD)
        state = self.start(self.client)["state"][0]
        with self.fake_github(email="other@example.com"):
            self.client.get(f"/auth/github/callback/?code=the-code&state={state}")
        self.assertEqual(self.client.get("/api/auth/me/").json()["user"]["username"], "octocat2")

    def test_bad_state_and_denied(self):
        self.start(self.client)
        res = self.client.get("/auth/github/callback/?code=x&state=forged")
        self.assertIn("auth_error=", res["Location"])
        self.assertIsNone(self.client.get("/api/auth/me/").json()["user"])
        state = self.start(self.client)["state"][0]
        res = self.client.get(f"/auth/github/callback/?error=access_denied&state={state}")
        self.assertIn("auth_error=", res["Location"])

    def test_open_redirect_blocked(self):
        state = self.start(self.client, next_url="https://evil.example/")["state"][0]
        with self.fake_github():
            res = self.client.get(f"/auth/github/callback/?code=the-code&state={state}")
        self.assertEqual(res["Location"], "/")

    @override_settings(OAUTH_PROVIDERS={"github": {"client_id": "", "client_secret": ""}})
    def test_disabled_provider(self):
        self.assertEqual(self.client.get("/auth/github/login/").status_code, 404)
        self.assertContains(self.client.get("/"), '"providers": []')

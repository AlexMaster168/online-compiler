"""Scratch 3: хранение .sb3 в проектах, права, форки, страница редактора."""
import base64
import io
import json
import zipfile

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings

from . import scratch

PASSWORD = "Krepkiy-parol-42"


def sb3(title="cat") -> str:
    """Минимальный .sb3: zip с project.json."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("project.json", json.dumps({"targets": [], "meta": {"semver": "3.0.0", "title": title}}))
    return base64.b64encode(buf.getvalue()).decode()


def call(client, url, data=None, method="post"):
    return getattr(client, method)(url, json.dumps(data or {}), content_type="application/json")


class ScratchApiTests(TestCase):
    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.owner = Client()
        self.owner.force_login(User.objects.create_user("leha", password=PASSWORD))
        self.other = Client()
        self.other.force_login(User.objects.create_user("brat", password=PASSWORD))

    def create(self, client, **extra):
        res = call(client, "/api/scratch/", {"sb3": sb3(), "title": "Кот бегает", **extra})
        self.assertEqual(res.status_code, 201, res.content)
        return res.json()

    def test_create_and_read(self):
        project = self.create(self.owner)
        self.assertEqual(project["url"], f"/scratch/{project['id']}/")
        self.assertTrue(project["is_owner"])
        self.assertNotIn("code", project)
        data = Client().get(f"/api/scratch/{project['id']}/").json()
        self.assertEqual(data["sb3"], sb3())
        self.assertFalse(data["is_owner"])
        # в «Моих проектах» scratch-проект ведёт на свою страницу
        items = self.owner.get("/api/projects/").json()["items"]
        self.assertEqual((items[0]["language"], items[0]["url"]), ("scratch", project["url"]))

    def test_validation(self):
        bad = [{"sb3": "не base64!!"}, {"sb3": base64.b64encode(b"just text").decode()}, {}]
        for data in bad:
            self.assertEqual(call(self.owner, "/api/scratch/", data).status_code, 400, data)

    @override_settings()
    def test_size_limit(self):
        old = scratch.MAX_SB3_BYTES
        scratch.MAX_SB3_BYTES = 100
        try:
            res = call(self.owner, "/api/scratch/", {"sb3": base64.b64encode(b"PK" + b"0" * 500).decode()})
            self.assertEqual(res.status_code, 400)
            self.assertIn("МБ", res.json()["error"])
        finally:
            scratch.MAX_SB3_BYTES = old

    def test_owner_saves_others_fork(self):
        project = self.create(self.owner)
        url = f"/api/scratch/{project['id']}/"
        self.assertEqual(call(self.owner, url, {"sb3": sb3("v2"), "title": "Кот v2"}, "patch").status_code, 200)
        self.assertEqual(Client().get(url).json()["title"], "Кот v2")
        self.assertEqual(call(self.other, url, {"sb3": sb3("hack")}, "patch").status_code, 403)
        self.assertEqual(call(Client(), url, {"sb3": sb3("hack")}, "patch").status_code, 401)

        copy = call(self.other, f"/api/snippets/{project['id']}/fork/").json()
        self.assertEqual(copy["url"], f"/scratch/{copy['id']}/")
        self.assertEqual(call(self.other, f"/api/scratch/{copy['id']}/", {"sb3": sb3("mine")}, "patch").status_code,
                         200)
        self.assertEqual(Client().get(url).json()["sb3"], sb3("v2"))  # оригинал не тронут

    def test_private_and_redirects(self):
        project = self.create(self.owner)
        call(self.owner, f"/api/scratch/{project['id']}/", {"visibility": "private"}, "patch")
        self.assertEqual(self.other.get(f"/api/scratch/{project['id']}/").status_code, 404)
        self.assertEqual(self.other.get(f"/scratch/{project['id']}/").status_code, 404)
        self.assertEqual(self.owner.get(f"/scratch/{project['id']}/").status_code, 200)
        # старая ссылка /s/<id>/ на scratch-проект ведёт в редактор Scratch
        res = self.owner.get(f"/s/{project['id']}/")
        self.assertRedirects(res, f"/scratch/{project['id']}/", fetch_redirect_response=False)

    def test_code_snippet_is_not_scratch(self):
        res = call(self.owner, "/api/snippets/", {"language": "python", "code": "print(1)"})
        sid = res.json()["id"]
        self.assertEqual(self.owner.get(f"/api/scratch/{sid}/").status_code, 400)
        self.assertRedirects(self.owner.get(f"/scratch/{sid}/"), f"/s/{sid}/", fetch_redirect_response=False)

    def test_page_renders(self):
        page = self.client.get("/scratch/")
        self.assertContains(page, "Scratch")
        if scratch.editor_available():
            self.assertContains(page, "scratchFrame")
        else:
            self.assertContains(page, "build_scratch")

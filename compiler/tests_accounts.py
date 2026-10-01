"""Этап 4: аккаунты, «Мои проекты», сохранение на месте, форки, привязка истории."""
import json
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, TransactionTestCase, override_settings

from .models import Execution, Snippet
from .tests import LOCAL, python_available

PASSWORD = "Krepkiy-parol-42"


def post(client, url, data=None, method="post"):
    return getattr(client, method)(url, json.dumps(data or {}), content_type="application/json")


class AuthTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_register_login_logout(self):
        res = post(self.client, "/api/auth/register/", {"username": "Лёха", "password": PASSWORD})
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(res.json()["user"], {"username": "Лёха"})
        self.assertEqual(self.client.get("/api/auth/me/").json()["user"], {"username": "Лёха"})

        post(self.client, "/api/auth/logout/")
        self.assertIsNone(self.client.get("/api/auth/me/").json()["user"])

        res = post(self.client, "/api/auth/login/", {"username": "лёха", "password": PASSWORD})  # регистр не важен
        self.assertEqual(res.status_code, 200, res.content)
        res = post(self.client, "/api/auth/login/", {"username": "Лёха", "password": "wrong"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("Неверный", res.json()["error"])

    def test_register_validation(self):
        get_user_model().objects.create_user("taken", password=PASSWORD)
        cases = [
            ({"username": "TAKEN", "password": PASSWORD}, "занят"),
            ({"username": "a", "password": PASSWORD}, "3–30"),
            ({"username": "bad name", "password": PASSWORD}, "3–30"),
            ({"username": "newbie", "password": "12345678"}, ""),  # валидаторы Django: слишком простой
        ]
        for data, message in cases:
            res = post(self.client, "/api/auth/register/", data)
            self.assertEqual(res.status_code, 400, data)
            self.assertIn(message, res.json()["error"])
        self.assertFalse(get_user_model().objects.filter(username="newbie").exists())

    @override_settings(AUTH_RATE_LIMIT_PER_MINUTE=3)
    def test_bruteforce_throttled(self):
        get_user_model().objects.create_user("victim", password=PASSWORD)
        codes = [post(self.client, "/api/auth/login/", {"username": "victim", "password": f"x{i}"}).status_code
                 for i in range(5)]
        self.assertEqual(codes, [400, 400, 400, 429, 429])
        res = post(self.client, "/api/auth/login/", {"username": "victim", "password": PASSWORD})
        self.assertEqual(res.status_code, 429)  # даже верный пароль — пока окно не истекло

    def test_csrf_enforced_on_login(self):
        client = Client(enforce_csrf_checks=True)
        res = post(client, "/api/auth/login/", {"username": "x", "password": "y"})
        self.assertEqual(res.status_code, 403)

    def test_index_exposes_user(self):
        get_user_model().objects.create_user("leha", password=PASSWORD)
        self.client.login(username="leha", password=PASSWORD)
        self.assertContains(self.client.get("/"), '"username": "leha"')


class ProjectTests(TestCase):
    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.owner = Client()
        self.owner.force_login(User.objects.create_user("owner", password=PASSWORD))
        self.other = Client()
        self.other.force_login(User.objects.create_user("other", password=PASSWORD))
        self.anon = Client()

    def create(self, client, **extra):
        data = {"language": "python", "code": "print(1)\n", "title": "Проект", **extra}
        res = post(client, "/api/snippets/", data)
        self.assertEqual(res.status_code, 201, res.content)
        return res.json()

    def test_owned_snippet_saves_in_place(self):
        project = self.create(self.owner)
        self.assertEqual((project["owner"], project["is_owner"]), ("owner", True))
        res = post(self.owner, f"/api/snippets/{project['id']}/", {
            "language": "python", "code": "print(2)\n", "files": [{"name": "lib.py", "content": "X = 1\n"}],
            "stdin": "in", "args": "-v",
        }, method="patch")
        self.assertEqual(res.status_code, 200, res.content)
        snippet = Snippet.objects.get(pk=project["id"])
        self.assertEqual((snippet.code, snippet.files[0]["name"], snippet.stdin, snippet.args),
                         ("print(2)\n", "lib.py", "in", "-v"))
        self.assertEqual(snippet.title, "Проект")  # не трогали — не изменилось

        post(self.owner, f"/api/snippets/{project['id']}/", {"title": "  Новое имя  "}, method="patch")
        self.assertEqual(Snippet.objects.get(pk=project["id"]).title, "Новое имя")

    def test_only_owner_can_change_or_delete(self):
        project = self.create(self.owner)
        url = f"/api/snippets/{project['id']}/"
        self.assertEqual(post(self.other, url, {"code": "hack"}, "patch").status_code, 403)
        self.assertEqual(post(self.anon, url, {"code": "hack"}, "patch").status_code, 401)
        self.assertEqual(self.other.delete(url).status_code, 403)
        self.assertEqual(Snippet.objects.get(pk=project["id"]).code, "print(1)\n")
        # Анонимный снимок не меняет никто
        anon_project = self.create(self.anon)
        self.assertIsNone(anon_project["owner"])
        self.assertEqual(post(self.owner, f"/api/snippets/{anon_project['id']}/", {"code": "x"}, "patch").status_code,
                         403)
        # Чужой видит проект, но is_owner = false
        view = self.other.get(url).json()
        self.assertEqual((view["owner"], view["is_owner"]), ("owner", False))

        self.assertEqual(self.owner.delete(url).status_code, 200)
        self.assertFalse(Snippet.objects.filter(pk=project["id"]).exists())

    def test_patch_validates_payload(self):
        project = self.create(self.owner)
        url = f"/api/snippets/{project['id']}/"
        self.assertEqual(post(self.owner, url, {"code": "x", "files": [{"name": "../x", "content": ""}]},
                              "patch").status_code, 400)
        self.assertEqual(post(self.owner, url, {}, "patch").status_code, 400)
        self.assertEqual(post(self.owner, url, {"code": "x", "language": "nope"}, "patch").status_code, 400)

    def test_fork(self):
        project = self.create(self.owner, args="a b", stdin="5", files=[{"name": "u.py", "content": "U=1\n"}])
        res = post(self.other, f"/api/snippets/{project['id']}/fork/")
        self.assertEqual(res.status_code, 201, res.content)
        fork = res.json()
        self.assertNotEqual(fork["id"], project["id"])
        self.assertEqual((fork["owner"], fork["is_owner"], fork["args"], fork["stdin"]), ("other", True, "a b", "5"))
        self.assertEqual(fork["files"], [{"name": "u.py", "content": "U=1\n"}])
        self.assertEqual(fork["forked_from"], {"id": project["id"], "title": "Проект", "url": project["url"],
                                               "owner": "owner"})
        self.assertEqual(self.anon.get(f"/api/snippets/{project['id']}/").json()["forks"], 1)
        self.assertEqual(post(self.anon, f"/api/snippets/{project['id']}/fork/").status_code, 401)
        # Оригинал удалили — форк живёт, ссылка на источник обнуляется
        self.owner.delete(f"/api/snippets/{project['id']}/")
        self.assertIsNone(self.other.get(f"/api/snippets/{fork['id']}/").json()["forked_from"])

    def test_my_projects(self):
        a = self.create(self.owner, title="Сортировки")
        self.create(self.owner, title="Графы", language="cpp", code="int main(){}")
        self.create(self.other, title="Чужой")
        post(self.owner, f"/api/snippets/{a['id']}/", {"code": "print(3)\n"}, "patch")  # поднимется наверх
        post(self.other, f"/api/snippets/{a['id']}/fork/")
        items = self.owner.get("/api/projects/").json()["items"]
        self.assertEqual([i["title"] for i in items], ["Сортировки", "Графы"])
        self.assertEqual(items[0]["forks"], 1)
        self.assertNotIn("code", items[0])
        self.assertEqual([i["title"] for i in self.owner.get("/api/projects/?q=граф").json()["items"]], ["Графы"])
        self.assertEqual([i["title"] for i in self.owner.get("/api/projects/?q=cpp").json()["items"]], ["Графы"])
        self.assertEqual(self.anon.get("/api/projects/").status_code, 401)

    def test_shared_page_marks_owner(self):
        project = self.create(self.owner)
        self.assertContains(self.owner.get(project["url"]), '"is_owner": true')
        self.assertContains(self.other.get(project["url"]), '"is_owner": false')


@override_settings(EXECUTOR=LOCAL)
@skipUnless(python_available, "нужен локальный python")
class HistoryOwnershipTests(TestCase):
    def setUp(self):
        cache.clear()

    def run_code(self, client, code):
        res = post(client, "/api/run/", {"language": "python", "code": code})
        self.assertEqual(res.status_code, 200)
        return res.json()["id"]

    def test_anonymous_history_moves_to_account_on_login(self):
        get_user_model().objects.create_user("leha", password=PASSWORD)
        client = Client()
        client.get("/")
        anon_run = self.run_code(client, "print('аноним')")
        post(client, "/api/auth/login/", {"username": "leha", "password": PASSWORD})
        self.assertEqual(Execution.objects.get(pk=anon_run).user.username, "leha")
        user_run = self.run_code(client, "print('я')")
        self.assertEqual([i["id"] for i in client.get("/api/history/").json()["items"]], [user_run, anon_run])

        # С другого устройства — та же история
        laptop = Client()
        post(laptop, "/api/auth/login/", {"username": "leha", "password": PASSWORD})
        self.assertEqual(len(laptop.get("/api/history/").json()["items"]), 2)
        self.assertEqual(laptop.get(f"/api/executions/{anon_run}/").status_code, 200)

        # После выхода и для чужих — пусто
        post(client, "/api/auth/logout/")
        self.assertEqual(client.get("/api/history/").json()["items"], [])
        self.assertEqual(Client().get(f"/api/executions/{anon_run}/").status_code, 404)


class ConsoleOwnershipTests(TransactionTestCase):
    @override_settings(EXECUTOR=LOCAL)
    @skipUnless(python_available, "нужен локальный python")
    async def test_console_run_belongs_to_user(self):
        from asgiref.sync import sync_to_async
        from channels.testing import WebsocketCommunicator

        from config.asgi import application

        @sync_to_async
        def login_cookie():
            cache.clear()
            client = Client()
            client.force_login(get_user_model().objects.create_user("ws-user", password=PASSWORD))
            return client.cookies["sessionid"].value

        session_id = await login_cookie()
        comm = WebsocketCommunicator(application, "/ws/run/", headers=[
            (b"origin", b"http://localhost:8000"), (b"host", b"localhost"),
            (b"cookie", f"sessionid={session_id}".encode()),
        ])
        connected, _ = await comm.connect()
        self.assertTrue(connected)
        await comm.send_json_to({"type": "start", "language": "python", "code": "print('ws')"})
        while True:
            ev = await comm.receive_json_from(timeout=60)
            if ev["type"] == "exit":
                break
        execution = await Execution.objects.select_related("user").aget(pk=ev["id"])
        self.assertEqual(execution.user.username, "ws-user")
        await comm.disconnect()

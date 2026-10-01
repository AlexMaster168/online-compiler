"""Ручная проверка OcJdiAdapter без Docker: python e2e/jdi_probe.py
Компилирует адаптер и тестовую программу локальным JDK, гоняет DAP и печатает всё, включая stderr адаптера."""
import json, os, subprocess, sys, tempfile, threading, time, socket
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from compiler.engine.dap import DapClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JDI = os.path.join(ROOT, "compiler", "engine", "sandbox", "jdi")
subprocess.run(["javac", "-encoding", "UTF-8", "-d", os.path.join(JDI, "classes"), os.path.join(JDI, "OcJdiAdapter.java")], check=True)

work = tempfile.mkdtemp()
src = os.path.join(work, "Main.java")
open(src, "w", encoding="utf-8").write(
    'import java.util.*;\npublic class Main {\n    int count = 7;\n'
    '    public static void main(String[] args) {\n        int[] arr = {10, 20, 30};\n'
    '        List<String> list = new ArrayList<>(List.of("a", "b"));\n        Main m = new Main();\n'
    '        System.out.println(arr.length + list.size() + m.count);\n'
    '        Object boom = null;\n        boom.toString();\n    }\n}\n')
subprocess.run(["javac", "-g", "-encoding", "UTF-8", "-d", work, src], check=True)
with socket.socket() as s:
    s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
prog = subprocess.Popen(["java", f"-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=127.0.0.1:{port}", "-cp", work, "Main"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
adapter = subprocess.Popen(["java", "-cp", os.path.join(JDI, "classes"), "OcJdiAdapter", str(port), work.replace("\\", "/")],
                           stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
threading.Thread(target=lambda: [print("ADAPTER-ERR:", l.decode(errors="replace").rstrip()) for l in adapter.stderr], daemon=True).start()
events = []
def on_event(e):
    events.append(e); print("EVENT:", json.dumps(e, ensure_ascii=False)[:300])
def write(b):
    adapter.stdin.write(b); adapter.stdin.flush()
dap = DapClient(write, on_event)
threading.Thread(target=lambda: [dap.feed(c) for c in iter(lambda: adapter.stdout.read1(65536), b"")], daemon=True).start()

print(dap.request("initialize", {}))
att = dap.request_async("attach", {"port": port})
time.sleep(0.5)
print(dap.request("setBreakpoints", {"source": {"path": work + "/Main.java"}, "breakpoints": [{"line": 8}]}))
dap.request("configurationDone", {})
att.wait(30)
for _ in range(100):
    if any(e.get("event") == "stopped" for e in events): break
    time.sleep(0.1)
tid = [e for e in events if e.get("event") == "stopped"][0]["body"]["threadId"]
st = dap.request("stackTrace", {"threadId": tid})
print("FRAMES:", st)
fid = st["stackFrames"][0]["id"]
sc = dap.request("scopes", {"frameId": fid}); print("SCOPES:", sc)
print("VARS:", dap.request("variables", {"variablesReference": sc["scopes"][0]["variablesReference"]}))
print("SCOPES AGAIN:", dap.request("scopes", {"frameId": fid}))
dap.request_async("disconnect", {"terminateDebuggee": True})
time.sleep(1); prog.kill(); adapter.kill()

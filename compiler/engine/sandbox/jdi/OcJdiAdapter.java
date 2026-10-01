import com.sun.jdi.*;
import com.sun.jdi.connect.AttachingConnector;
import com.sun.jdi.connect.Connector;
import com.sun.jdi.event.*;
import com.sun.jdi.request.*;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Минимальный DAP-адаптер для JVM (Java, Kotlin) поверх JDI.
 *
 * Запуск: java -cp <dir> OcJdiAdapter PORT — подключается к JVM, запущенной с
 * -agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=127.0.0.1:PORT,
 * и говорит на Debug Adapter Protocol через stdin/stdout.
 *
 * Поддержано: breakpoints (в т.ч. в ещё не загруженных классах), continue/next/stepIn/stepOut/pause,
 * threads/stackTrace/scopes/variables, evaluate (пути obj.field, a[i], arr.length и арифметика),
 * остановка на непойманном исключении.
 */
public final class OcJdiAdapter {
    private static final String[] STEP_EXCLUDES = {"java.*", "javax.*", "jdk.*", "sun.*", "com.sun.*", "kotlin.*"};
    private static final int MAX_CHILDREN = 200;

    private final OutputStream out = new BufferedOutputStream(System.out);
    private int seq = 0;
    private VirtualMachine vm;
    private final String codeDir;

    /** файл (sourceName) -> строки */
    private final Map<String, List<Integer>> breakpoints = new ConcurrentHashMap<>();
    /** файл -> активные запросы JDI */
    private final Map<String, List<BreakpointRequest>> bpRequests = new ConcurrentHashMap<>();
    private final Map<String, ClassPrepareRequest> prepareRequests = new ConcurrentHashMap<>();

    /** variablesReference / frameId -> объект. Сбрасываются при каждом продолжении выполнения. */
    private final Map<Integer, Object> handles = new ConcurrentHashMap<>();
    private int nextHandle = 1000;

    private OcJdiAdapter(String codeDir) {
        this.codeDir = codeDir;
    }

    public static void main(String[] args) throws Exception {
        int port = Integer.parseInt(args[0]);
        String codeDir = args.length > 1 ? args[1] : "/code";
        OcJdiAdapter adapter = new OcJdiAdapter(codeDir);
        adapter.serve(port);
    }

    // ------------------------------------------------------------------ протокол

    private void serve(int port) throws IOException {
        InputStream in = new BufferedInputStream(System.in);
        while (true) {
            Map<String, Object> message = readMessage(in);
            if (message == null) break;
            if ("request".equals(message.get("type"))) {
                handleRequest(message, port);
            }
        }
        if (vm != null) {
            try { vm.dispose(); } catch (Exception ignored) { }
        }
        System.exit(0);
    }

    private static Map<String, Object> readMessage(InputStream in) throws IOException {
        int length = -1;
        StringBuilder line = new StringBuilder();
        while (true) {
            int c = in.read();
            if (c < 0) return null;
            if (c == '\n') {
                String header = line.toString().trim();
                line.setLength(0);
                if (header.isEmpty()) {
                    if (length >= 0) break;
                    continue;
                }
                int colon = header.indexOf(':');
                if (colon > 0 && header.substring(0, colon).trim().equalsIgnoreCase("Content-Length")) {
                    length = Integer.parseInt(header.substring(colon + 1).trim());
                }
            } else if (c != '\r') {
                line.append((char) c);
            }
        }
        byte[] body = in.readNBytes(length);
        @SuppressWarnings("unchecked")
        Map<String, Object> parsed = (Map<String, Object>) Json.parse(new String(body, StandardCharsets.UTF_8));
        return parsed;
    }

    private synchronized void send(Map<String, Object> message) {
        message.put("seq", ++seq);
        byte[] data = Json.write(message).getBytes(StandardCharsets.UTF_8);
        try {
            out.write(("Content-Length: " + data.length + "\r\n\r\n").getBytes(StandardCharsets.US_ASCII));
            out.write(data);
            out.flush();
        } catch (IOException e) {
            System.exit(1);
        }
    }

    private void respond(Map<String, Object> request, Object body) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("type", "response");
        m.put("request_seq", request.get("seq"));
        m.put("command", request.get("command"));
        m.put("success", true);
        if (body != null) m.put("body", body);
        send(m);
    }

    private void fail(Map<String, Object> request, String message) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("type", "response");
        m.put("request_seq", request.get("seq"));
        m.put("command", request.get("command"));
        m.put("success", false);
        m.put("message", message);
        send(m);
    }

    private void event(String name, Map<String, Object> body) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("type", "event");
        m.put("event", name);
        if (body != null) m.put("body", body);
        send(m);
    }

    @SuppressWarnings("unchecked")
    private void handleRequest(Map<String, Object> req, int port) {
        String command = (String) req.get("command");
        Map<String, Object> args = req.get("arguments") instanceof Map
                ? (Map<String, Object>) req.get("arguments") : new HashMap<>();
        try {
            switch (command) {
                case "initialize" -> {
                    respond(req, Json.obj("supportsConfigurationDoneRequest", true,
                            "supportsEvaluateForHovers", true));
                    event("initialized", null);
                }
                case "attach" -> {
                    attach(args.containsKey("port") ? ((Number) args.get("port")).intValue() : port);
                    respond(req, null);
                }
                case "setBreakpoints" -> respond(req, setBreakpoints(args));
                case "configurationDone" -> {
                    respond(req, null);
                    if (vm != null) vm.resume();
                }
                case "threads" -> respond(req, Json.obj("threads", threads()));
                case "stackTrace" -> respond(req, stackTrace(args));
                case "scopes" -> respond(req, scopes(args));
                case "variables" -> respond(req, Json.obj("variables", variables(args)));
                case "evaluate" -> respond(req, evaluate(args));
                case "continue" -> {
                    resume();
                    respond(req, Json.obj("allThreadsContinued", true));
                }
                case "next" -> step(req, args, StepRequest.STEP_OVER);
                case "stepIn" -> step(req, args, StepRequest.STEP_INTO);
                case "stepOut" -> step(req, args, StepRequest.STEP_OUT);
                case "pause" -> {
                    vm.suspend();
                    respond(req, null);
                    event("stopped", Json.obj("reason", "pause", "threadId", mainThreadId(), "allThreadsStopped", true));
                }
                case "disconnect" -> {
                    respond(req, null);
                    if (vm != null) {
                        try {
                            if (Boolean.TRUE.equals(args.get("terminateDebuggee"))) vm.exit(0);
                            else vm.dispose();
                        } catch (Exception ignored) { }
                    }
                    System.exit(0);
                }
                default -> fail(req, "Команда не поддерживается: " + command);
            }
        } catch (IllegalArgumentException | IllegalStateException e) {
            fail(req, e.getMessage());  // наши ожидаемые ошибки — понятный текст без имени класса
        } catch (Exception e) {
            fail(req, e.getClass().getSimpleName() + (e.getMessage() != null ? ": " + e.getMessage() : ""));
        }
    }

    // ------------------------------------------------------------------ подключение и события

    private void attach(int port) throws Exception {
        AttachingConnector connector = Bootstrap.virtualMachineManager().attachingConnectors().stream()
                .filter(c -> c.transport().name().equals("dt_socket")).findFirst()
                .orElseThrow(() -> new IllegalStateException("нет dt_socket коннектора"));
        Map<String, Connector.Argument> cargs = connector.defaultArguments();
        cargs.get("hostname").setValue("127.0.0.1");
        cargs.get("port").setValue(String.valueOf(port));
        cargs.get("timeout").setValue("5000");
        Exception last = null;
        for (int attempt = 0; attempt < 200 && vm == null; attempt++) {  // JVM может ещё стартовать
            try {
                vm = connector.attach(cargs);
            } catch (IOException e) {
                last = e;
                Thread.sleep(100);
            }
        }
        if (vm == null) throw last != null ? last : new IllegalStateException("не удалось подключиться");

        EventRequestManager erm = vm.eventRequestManager();
        ExceptionRequest exceptions = erm.createExceptionRequest(null, false, true);  // только непойманные
        for (String ex : STEP_EXCLUDES) exceptions.addClassExclusionFilter(ex);
        exceptions.setSuspendPolicy(EventRequest.SUSPEND_ALL);
        exceptions.enable();
        // Брейкпоинты, поставленные до attach, применяем к уже загруженным классам
        for (String file : breakpoints.keySet()) applyBreakpoints(file);

        Thread loop = new Thread(this::eventLoop, "jdi-events");
        loop.setDaemon(true);
        loop.start();
    }

    private void eventLoop() {
        EventQueue queue = vm.eventQueue();
        try {
            while (true) {
                EventSet set = queue.remove();
                boolean resume = true;
                // В одном наборе может прийти несколько событий на одну остановку (шаг + брейкпоинт на той же
                // строке) — клиенту сообщаем о ней один раз, иначе вторая остановка сбросит кадры первой
                boolean reported = false;
                for (Event e : set) {
                    if (e instanceof VMStartEvent) {
                        // JVM стартовала с suspend=y и ждёт: отпустим её только на configurationDone,
                        // когда брейкпоинты уже расставлены — иначе программа убежит вперёд
                        resume = false;
                    } else if (e instanceof ClassPrepareEvent cpe) {
                        applyToType(cpe.referenceType());
                    } else if (e instanceof BreakpointEvent be) {
                        resume = false;
                        if (!reported) stopped("breakpoint", be.thread(), null);
                        reported = true;
                    } else if (e instanceof StepEvent se) {
                        vm.eventRequestManager().deleteEventRequest(se.request());
                        resume = false;
                        if (!reported) stopped("step", se.thread(), null);
                        reported = true;
                    } else if (e instanceof ExceptionEvent ee) {
                        resume = false;
                        String type = ee.exception().referenceType().name();
                        if (!reported) stopped("exception", ee.thread(), "Непойманное исключение: " + type);
                        reported = true;
                    } else if (e instanceof VMDeathEvent || e instanceof VMDisconnectEvent) {
                        event("terminated", null);
                        return;
                    }
                }
                if (resume) set.resume();
            }
        } catch (InterruptedException | VMDisconnectedException e) {
            event("terminated", null);
        }
    }

    private void stopped(String reason, ThreadReference thread, String description) {
        handles.clear();
        Map<String, Object> body = Json.obj("reason", reason, "threadId", thread.uniqueID(), "allThreadsStopped", true);
        if (description != null) {
            body.put("description", description);
            body.put("text", description);
        }
        event("stopped", body);
    }

    private void resume() {
        handles.clear();
        vm.resume();
    }

    private long mainThreadId() {
        for (ThreadReference t : vm.allThreads()) if (t.name().equals("main")) return t.uniqueID();
        return vm.allThreads().isEmpty() ? 1 : vm.allThreads().get(0).uniqueID();
    }

    private ThreadReference thread(Map<String, Object> args) {
        long id = args.get("threadId") instanceof Number n ? n.longValue() : mainThreadId();
        for (ThreadReference t : vm.allThreads()) if (t.uniqueID() == id) return t;
        throw new IllegalArgumentException("нет потока " + id);
    }

    private void step(Map<String, Object> req, Map<String, Object> args, int depth) {
        ThreadReference t = thread(args);
        EventRequestManager erm = vm.eventRequestManager();
        for (StepRequest old : new ArrayList<>(erm.stepRequests())) erm.deleteEventRequest(old);
        StepRequest step = erm.createStepRequest(t, StepRequest.STEP_LINE, depth);
        for (String ex : STEP_EXCLUDES) step.addClassExclusionFilter(ex);
        step.addCountFilter(1);
        step.setSuspendPolicy(EventRequest.SUSPEND_ALL);
        step.enable();
        respond(req, null);
        resume();
    }

    // ------------------------------------------------------------------ брейкпоинты

    @SuppressWarnings("unchecked")
    private Map<String, Object> setBreakpoints(Map<String, Object> args) {
        Map<String, Object> source = (Map<String, Object>) args.get("source");
        String path = String.valueOf(source.get("path"));
        String file = path.substring(Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\')) + 1);
        List<Integer> lines = new ArrayList<>();
        for (Object bp : (List<Object>) args.getOrDefault("breakpoints", List.of())) {
            lines.add(((Number) ((Map<String, Object>) bp).get("line")).intValue());
        }
        breakpoints.put(file, lines);
        List<Object> result = new ArrayList<>();
        Set<Integer> verified = vm != null ? applyBreakpoints(file) : Set.of();
        for (int line : lines) {
            result.add(Json.obj("line", line, "verified", verified.contains(line) || vm == null));
        }
        return Json.obj("breakpoints", result);
    }

    /** Ставит точки файла в уже загруженных классах и подписывается на загрузку остальных. */
    private Set<Integer> applyBreakpoints(String file) {
        EventRequestManager erm = vm.eventRequestManager();
        for (BreakpointRequest r : bpRequests.getOrDefault(file, List.of())) erm.deleteEventRequest(r);
        bpRequests.put(file, new ArrayList<>());
        if (!prepareRequests.containsKey(file)) {
            ClassPrepareRequest cpr = erm.createClassPrepareRequest();
            cpr.addSourceNameFilter(file);
            cpr.setSuspendPolicy(EventRequest.SUSPEND_ALL);
            cpr.enable();
            prepareRequests.put(file, cpr);
        }
        Set<Integer> verified = new HashSet<>();
        for (ReferenceType type : vm.allClasses()) {
            verified.addAll(applyToType(type, file));
        }
        return verified;
    }

    private void applyToType(ReferenceType type) {
        try {
            applyToType(type, type.sourceName());
        } catch (AbsentInformationException ignored) { }
    }

    private Set<Integer> applyToType(ReferenceType type, String file) {
        Set<Integer> verified = new HashSet<>();
        try {
            if (!type.sourceName().equals(file)) return verified;
        } catch (AbsentInformationException e) {
            return verified;
        }
        EventRequestManager erm = vm.eventRequestManager();
        List<BreakpointRequest> existing = bpRequests.computeIfAbsent(file, k -> new ArrayList<>());
        for (int line : breakpoints.getOrDefault(file, List.of())) {
            try {
                for (Location loc : type.locationsOfLine(line)) {
                    if (existing.stream().anyMatch(r -> r.location().equals(loc))) {  // уже стоит
                        verified.add(line);
                        continue;
                    }
                    BreakpointRequest r = erm.createBreakpointRequest(loc);
                    r.setSuspendPolicy(EventRequest.SUSPEND_ALL);
                    r.enable();
                    bpRequests.computeIfAbsent(file, k -> new ArrayList<>()).add(r);
                    verified.add(line);
                }
            } catch (AbsentInformationException ignored) { }
        }
        return verified;
    }

    // ------------------------------------------------------------------ стек и переменные

    private List<Object> threads() {
        List<Object> list = new ArrayList<>();
        for (ThreadReference t : vm.allThreads()) {
            ThreadGroupReference group = t.threadGroup();
            if (group != null && group.name().equals("system")) continue;
            list.add(Json.obj("id", t.uniqueID(), "name", t.name()));
        }
        return list;
    }

    private int handle(Object value) {
        int id = nextHandle++;
        handles.put(id, value);
        return id;
    }

    private record FrameRef(ThreadReference thread, int index) {
        StackFrame frame() throws IncompatibleThreadStateException {
            return thread.frame(index);
        }
    }

    private Map<String, Object> stackTrace(Map<String, Object> args) throws Exception {
        ThreadReference t = thread(args);
        List<Object> frames = new ArrayList<>();
        List<StackFrame> stack = t.frames();
        int levels = args.get("levels") instanceof Number n && n.intValue() > 0 ? n.intValue() : stack.size();
        for (int i = 0; i < Math.min(stack.size(), levels); i++) {
            Location loc = stack.get(i).location();
            Map<String, Object> frame = Json.obj(
                    "id", handle(new FrameRef(t, i)),
                    "name", loc.declaringType().name() + "." + loc.method().name(),
                    "line", Math.max(loc.lineNumber(), 0), "column", 1);
            try {
                frame.put("source", Json.obj("name", loc.sourceName(), "path", codeDir + "/" + loc.sourcePath()));
            } catch (AbsentInformationException ignored) { }
            frames.add(frame);
        }
        return Json.obj("stackFrames", frames, "totalFrames", stack.size());
    }

    private Map<String, Object> scopes(Map<String, Object> args) {
        Object ref = handles.get(((Number) args.get("frameId")).intValue());
        if (!(ref instanceof FrameRef fr)) throw new IllegalArgumentException("кадр устарел");
        return Json.obj("scopes", List.of(Json.obj("name", "Locals", "variablesReference", handle(new LocalsRef(fr)),
                "expensive", false)));
    }

    private record LocalsRef(FrameRef frame) { }

    private List<Object> variables(Map<String, Object> args) throws Exception {
        Object ref = handles.get(((Number) args.get("variablesReference")).intValue());
        List<Object> result = new ArrayList<>();
        if (ref instanceof LocalsRef lr) {
            StackFrame frame = lr.frame().frame();
            ObjectReference self = frame.thisObject();
            if (self != null) result.add(variable("this", self));
            try {
                for (LocalVariable lv : frame.visibleVariables()) {
                    result.add(variable(lv.name(), frame.getValue(lv)));
                }
            } catch (AbsentInformationException e) {
                result.add(Json.obj("name", "(нет отладочной информации)", "value", "скомпилируй с -g",
                        "variablesReference", 0));
            }
        } else if (ref instanceof ArrayReference array) {
            int n = Math.min(array.length(), MAX_CHILDREN);
            for (int i = 0; i < n; i++) result.add(variable("[" + i + "]", array.getValue(i)));
        } else if (ref instanceof ObjectReference obj) {
            for (Field f : obj.referenceType().allFields()) {
                if (f.isStatic() || result.size() >= MAX_CHILDREN) continue;
                result.add(variable(f.name(), obj.getValue(f)));
            }
        }
        return result;
    }

    private Map<String, Object> variable(String name, Value value) {
        return Json.obj("name", name, "value", format(value), "type", value == null ? "null" : value.type().name(),
                "variablesReference", expandable(value) ? handle(value) : 0);
    }

    private static boolean expandable(Value v) {
        return v instanceof ObjectReference && !(v instanceof StringReference);
    }

    private static String format(Value v) {
        if (v == null) return "null";
        if (v instanceof StringReference s) return quote(s.value());
        if (v instanceof CharValue c) return "'" + c.value() + "'";
        if (v instanceof PrimitiveValue) return v.toString();
        if (v instanceof ArrayReference a) {
            String type = a.type().name();
            return type.replaceFirst("\\[]", "[" + a.length() + "]");
        }
        if (v instanceof ObjectReference o) {
            String type = o.referenceType().name();
            String simple = type.substring(type.lastIndexOf('.') + 1);
            Value boxed = field(o, "value");  // Integer, Long, Boolean и т.п.
            if (type.startsWith("java.lang.") && boxed instanceof PrimitiveValue) return boxed.toString();
            Value size = field(o, "size");    // ArrayList, HashMap, ...
            if (size instanceof IntegerValue n) return simple + " size=" + n.value();
            return simple + "@" + o.uniqueID();
        }
        return v.toString();
    }

    private static Value field(ObjectReference o, String name) {
        Field f = o.referenceType().fieldByName(name);
        return f == null || f.isStatic() ? null : o.getValue(f);
    }

    private static String quote(String s) {
        StringBuilder sb = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            switch (c) {
                case '"' -> sb.append("\\\"");
                case '\\' -> sb.append("\\\\");
                case '\n' -> sb.append("\\n");
                case '\t' -> sb.append("\\t");
                case '\r' -> sb.append("\\r");
                default -> sb.append(c);
            }
        }
        return sb.append('"').toString();
    }

    // ------------------------------------------------------------------ evaluate

    private Map<String, Object> evaluate(Map<String, Object> args) throws Exception {
        String expression = String.valueOf(args.get("expression")).trim();
        Object ref = args.get("frameId") instanceof Number n ? handles.get(n.intValue()) : null;
        if (!(ref instanceof FrameRef fr)) throw new IllegalArgumentException("программа не на паузе");
        Object value = new Evaluator(expression, fr.frame()).parse();
        if (value instanceof Value v || value == null) {
            Value jv = (Value) value;
            return Json.obj("result", format(jv), "type", jv == null ? "null" : jv.type().name(),
                    "variablesReference", expandable(jv) ? handle(jv) : 0);
        }
        return Json.obj("result", Evaluator.show(value), "type", value.getClass().getSimpleName(),
                "variablesReference", 0);
    }

    /** Мини-вычислитель: пути (a.b, a[i], arr.length), числа, строки и + - * / % с приоритетами. */
    private static final class Evaluator {
        private final String src;
        private final StackFrame frame;
        private int pos = 0;

        Evaluator(String src, StackFrame frame) {
            this.src = src;
            this.frame = frame;
        }

        Object parse() throws Exception {
            Object v = sum();
            skip();
            if (pos != src.length()) throw new IllegalArgumentException("не понял выражение у: " + src.substring(pos));
            return v;
        }

        private void skip() {
            while (pos < src.length() && Character.isWhitespace(src.charAt(pos))) pos++;
        }

        private Object sum() throws Exception {
            Object left = product();
            while (true) {
                skip();
                if (pos >= src.length() || (src.charAt(pos) != '+' && src.charAt(pos) != '-')) return left;
                char op = src.charAt(pos++);
                left = arith(op, left, product());
            }
        }

        private Object product() throws Exception {
            Object left = unary();
            while (true) {
                skip();
                if (pos >= src.length() || "*/%".indexOf(src.charAt(pos)) < 0) return left;
                char op = src.charAt(pos++);
                left = arith(op, left, unary());
            }
        }

        private Object unary() throws Exception {
            skip();
            if (pos < src.length() && src.charAt(pos) == '-') {
                pos++;
                return arith('*', -1L, unary());
            }
            return primary();
        }

        private Object primary() throws Exception {
            skip();
            if (pos >= src.length()) throw new IllegalArgumentException("выражение оборвалось");
            char c = src.charAt(pos);
            if (c == '(') {
                pos++;
                Object v = sum();
                skip();
                expect(')');
                return v;
            }
            if (Character.isDigit(c)) {
                int start = pos;
                while (pos < src.length() && (Character.isDigit(src.charAt(pos)) || src.charAt(pos) == '.')) pos++;
                String num = src.substring(start, pos);
                return num.contains(".") ? (Object) Double.parseDouble(num) : (Object) Long.parseLong(num);
            }
            if (c == '"') {
                int end = src.indexOf('"', pos + 1);
                if (end < 0) throw new IllegalArgumentException("незакрытая строка");
                String s = src.substring(pos + 1, end);
                pos = end + 1;
                return s;
            }
            return path();
        }

        private Object path() throws Exception {
            String name = ident();
            Value current = lookup(name);
            while (true) {
                skip();
                if (pos < src.length() && src.charAt(pos) == '.') {
                    pos++;
                    String member = ident();
                    if (member.equals("length") && current instanceof ArrayReference a) {
                        return (long) a.length();
                    }
                    if (!(current instanceof ObjectReference o)) throw new IllegalArgumentException(member + ": не объект");
                    Field f = o.referenceType().fieldByName(member);
                    if (f == null) throw new IllegalArgumentException("нет поля " + member);
                    current = f.isStatic() ? o.referenceType().getValue(f) : o.getValue(f);
                } else if (pos < src.length() && src.charAt(pos) == '[') {
                    pos++;
                    Object index = sum();
                    skip();
                    expect(']');
                    if (!(current instanceof ArrayReference a)) throw new IllegalArgumentException("индекс не у массива");
                    current = a.getValue((int) toLong(index));
                } else {
                    return current;
                }
            }
        }

        private Value lookup(String name) throws Exception {
            if (name.equals("this")) return frame.thisObject();
            if (name.equals("null")) return null;
            try {
                LocalVariable lv = frame.visibleVariableByName(name);
                if (lv != null) return frame.getValue(lv);
            } catch (AbsentInformationException ignored) { }
            ObjectReference self = frame.thisObject();
            ReferenceType type = self != null ? self.referenceType() : frame.location().declaringType();
            Field f = type.fieldByName(name);
            if (f != null) return f.isStatic() ? type.getValue(f) : self.getValue(f);
            throw new IllegalArgumentException("нет переменной " + name);
        }

        private String ident() {
            skip();
            int start = pos;
            while (pos < src.length() && (Character.isLetterOrDigit(src.charAt(pos)) || src.charAt(pos) == '_'
                    || src.charAt(pos) == '$')) pos++;
            if (start == pos) throw new IllegalArgumentException("ожидалось имя у: " + src.substring(start));
            return src.substring(start, pos);
        }

        private void expect(char c) {
            if (pos >= src.length() || src.charAt(pos) != c) throw new IllegalArgumentException("ожидалось " + c);
            pos++;
        }

        private static Object unwrap(Object v) {
            if (v instanceof StringReference s) return s.value();
            if (v instanceof BooleanValue b) return b.value();
            if (v instanceof CharValue c) return (long) c.value();
            if (v instanceof FloatValue f) return (double) f.value();
            if (v instanceof DoubleValue d) return d.value();
            if (v instanceof PrimitiveValue p) return p.longValue();
            return v;
        }

        private static double toDouble(Object v) {
            Object u = unwrap(v);
            if (u instanceof Number n) return n.doubleValue();
            throw new IllegalArgumentException("не число: " + show(v));
        }

        private static long toLong(Object v) {
            Object u = unwrap(v);
            if (u instanceof Number n) return n.longValue();
            throw new IllegalArgumentException("не число: " + show(v));
        }

        private static Object arith(char op, Object a, Object b) {
            Object ua = unwrap(a), ub = unwrap(b);
            if (op == '+' && (ua instanceof String || ub instanceof String)) return show(a) + show(b);
            if (ua instanceof Double || ub instanceof Double) {
                double x = toDouble(a), y = toDouble(b);
                return switch (op) {
                    case '+' -> x + y; case '-' -> x - y; case '*' -> x * y; case '/' -> x / y; default -> x % y;
                };
            }
            long x = toLong(a), y = toLong(b);
            if ((op == '/' || op == '%') && y == 0) throw new IllegalArgumentException("деление на ноль");
            return switch (op) {
                case '+' -> x + y; case '-' -> x - y; case '*' -> x * y; case '/' -> x / y; default -> x % y;
            };
        }

        static String show(Object v) {
            Object u = unwrap(v);
            if (u instanceof Value value) return format(value);
            return String.valueOf(u);
        }
    }

    // ------------------------------------------------------------------ JSON

    /** Крохотный JSON без зависимостей: Map / List / String / Number / Boolean / null. */
    static final class Json {
        static Map<String, Object> obj(Object... kv) {
            Map<String, Object> m = new LinkedHashMap<>();
            for (int i = 0; i < kv.length; i += 2) m.put((String) kv[i], kv[i + 1]);
            return m;
        }

        static String write(Object v) {
            StringBuilder sb = new StringBuilder();
            write(v, sb);
            return sb.toString();
        }

        private static void write(Object v, StringBuilder sb) {
            if (v == null) sb.append("null");
            else if (v instanceof String s) writeString(s, sb);
            else if (v instanceof Number || v instanceof Boolean) sb.append(v);
            else if (v instanceof Map<?, ?> m) {
                sb.append('{');
                boolean first = true;
                for (Map.Entry<?, ?> e : m.entrySet()) {
                    if (!first) sb.append(',');
                    first = false;
                    writeString(String.valueOf(e.getKey()), sb);
                    sb.append(':');
                    write(e.getValue(), sb);
                }
                sb.append('}');
            } else if (v instanceof Collection<?> c) {
                sb.append('[');
                boolean first = true;
                for (Object item : c) {
                    if (!first) sb.append(',');
                    first = false;
                    write(item, sb);
                }
                sb.append(']');
            } else writeString(String.valueOf(v), sb);
        }

        private static void writeString(String s, StringBuilder sb) {
            sb.append('"');
            for (int i = 0; i < s.length(); i++) {
                char c = s.charAt(i);
                switch (c) {
                    case '"' -> sb.append("\\\"");
                    case '\\' -> sb.append("\\\\");
                    case '\n' -> sb.append("\\n");
                    case '\r' -> sb.append("\\r");
                    case '\t' -> sb.append("\\t");
                    default -> {
                        if (c < 0x20) sb.append(String.format("\\u%04x", (int) c));
                        else sb.append(c);
                    }
                }
            }
            sb.append('"');
        }

        static Object parse(String s) {
            int[] pos = {0};
            Object v = value(s, pos);
            return v;
        }

        private static void ws(String s, int[] p) {
            while (p[0] < s.length() && Character.isWhitespace(s.charAt(p[0]))) p[0]++;
        }

        private static Object value(String s, int[] p) {
            ws(s, p);
            char c = s.charAt(p[0]);
            if (c == '{') {
                p[0]++;
                Map<String, Object> m = new LinkedHashMap<>();
                ws(s, p);
                if (s.charAt(p[0]) == '}') { p[0]++; return m; }
                while (true) {
                    ws(s, p);
                    String key = string(s, p);
                    ws(s, p);
                    p[0]++;  // ':'
                    m.put(key, value(s, p));
                    ws(s, p);
                    if (s.charAt(p[0]++) == '}') return m;
                }
            }
            if (c == '[') {
                p[0]++;
                List<Object> list = new ArrayList<>();
                ws(s, p);
                if (s.charAt(p[0]) == ']') { p[0]++; return list; }
                while (true) {
                    list.add(value(s, p));
                    ws(s, p);
                    if (s.charAt(p[0]++) == ']') return list;
                }
            }
            if (c == '"') return string(s, p);
            if (s.startsWith("true", p[0])) { p[0] += 4; return Boolean.TRUE; }
            if (s.startsWith("false", p[0])) { p[0] += 5; return Boolean.FALSE; }
            if (s.startsWith("null", p[0])) { p[0] += 4; return null; }
            int start = p[0];
            while (p[0] < s.length() && "+-0123456789.eE".indexOf(s.charAt(p[0])) >= 0) p[0]++;
            String num = s.substring(start, p[0]);
            if (num.contains(".") || num.contains("e") || num.contains("E")) return Double.parseDouble(num);
            return Long.parseLong(num);
        }

        private static String string(String s, int[] p) {
            StringBuilder sb = new StringBuilder();
            p[0]++;  // открывающая кавычка
            while (true) {
                char c = s.charAt(p[0]++);
                if (c == '"') return sb.toString();
                if (c == '\\') {
                    char e = s.charAt(p[0]++);
                    switch (e) {
                        case 'n' -> sb.append('\n');
                        case 't' -> sb.append('\t');
                        case 'r' -> sb.append('\r');
                        case 'b' -> sb.append('\b');
                        case 'f' -> sb.append('\f');
                        case 'u' -> {
                            sb.append((char) Integer.parseInt(s.substring(p[0], p[0] + 4), 16));
                            p[0] += 4;
                        }
                        default -> sb.append(e);
                    }
                } else {
                    sb.append(c);
                }
            }
        }
    }
}

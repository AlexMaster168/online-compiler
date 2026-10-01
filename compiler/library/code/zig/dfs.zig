// Поиск в глубину рекурсией: состояние обхода — структура, метод visit получает *Dfs.
const std = @import("std");

const graph = [_][2]usize{ .{ 1, 2 }, .{ 0, 3 }, .{ 0, 4 }, .{ 1, 5 }, .{ 2, 5 }, .{ 3, 4 } };

const Dfs = struct {
    visited: [graph.len]bool = [_]bool{false} ** graph.len,
    order: [graph.len]usize = undefined,
    count: usize = 0,

    fn visit(self: *Dfs, v: usize) void {
        self.visited[v] = true;
        self.order[self.count] = v;
        self.count += 1;
        for (graph[v]) |u| {
            if (!self.visited[u]) self.visit(u);
        }
    }
};

pub fn main() !void {
    const out = std.io.getStdOut().writer();
    var dfs = Dfs{};
    dfs.visit(0);
    try out.writeAll("DFS order:");
    for (dfs.order[0..dfs.count]) |v| try out.print(" {d}", .{v});
    try out.writeAll("\n");
}

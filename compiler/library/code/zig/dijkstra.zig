// Дейкстра за O(V^2) на матрице весов (0 — нет ребра).
const std = @import("std");

const w = [_][5]u32{
    .{ 0, 4, 1, 0, 0 },
    .{ 0, 0, 0, 1, 0 },
    .{ 0, 2, 0, 5, 0 },
    .{ 0, 0, 0, 0, 3 },
    .{ 0, 0, 0, 0, 0 },
};

pub fn main() !void {
    const out = std.io.getStdOut().writer();
    const inf = std.math.maxInt(u32);
    var dist = [_]u32{inf} ** w.len;
    var done = [_]bool{false} ** w.len;
    dist[0] = 0;
    for (0..w.len) |_| {
        var best: ?usize = null;
        for (0..w.len) |i| {
            if (!done[i] and (best == null or dist[i] < dist[best.?])) best = i;
        }
        const v = best.?;
        if (dist[v] == inf) break;
        done[v] = true;
        for (0..w.len) |u| {
            if (w[v][u] > 0 and dist[v] + w[v][u] < dist[u]) dist[u] = dist[v] + w[v][u];
        }
    }
    try out.writeAll("Dijkstra from 0:");
    for (dist) |d| try out.print(" {d}", .{d});
    try out.writeAll("\n");
}

// Поиск в ширину: очередь — массив с индексами head и tail, O(V + E).
const std = @import("std");

const graph = [_][2]usize{ .{ 1, 2 }, .{ 0, 3 }, .{ 0, 4 }, .{ 1, 5 }, .{ 2, 5 }, .{ 3, 4 } };

pub fn main() !void {
    const out = std.io.getStdOut().writer();
    var dist = [_]i32{-1} ** graph.len;
    var queue: [graph.len]usize = undefined;
    var head: usize = 0;
    var tail: usize = 1;
    queue[0] = 0;
    dist[0] = 0;
    while (head < tail) : (head += 1) {
        const v = queue[head];
        for (graph[v]) |u| {
            if (dist[u] == -1) {
                dist[u] = dist[v] + 1;
                queue[tail] = u;
                tail += 1;
            }
        }
    }
    try out.writeAll("BFS order:");
    for (queue[0..tail]) |v| try out.print(" {d}", .{v});
    try out.writeAll("\nDistances:");
    for (dist) |d| try out.print(" {d}", .{d});
    try out.writeAll("\n");
}

// Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз.
const std = @import("std");

const Item = struct { weight: usize, value: u32 };

pub fn main() !void {
    const out = std.io.getStdOut().writer();
    const items = [_]Item{ .{ .weight = 1, .value = 1 }, .{ .weight = 3, .value = 4 }, .{ .weight = 4, .value = 5 }, .{ .weight = 5, .value = 7 } };
    const capacity = 7;
    var dp = [_]u32{0} ** (capacity + 1);
    for (items) |item| {
        var c: usize = capacity;
        while (c >= item.weight) : (c -= 1) {
            dp[c] = @max(dp[c], dp[c - item.weight] + item.value);
            if (c == 0) break;
        }
    }
    try out.print("Knapsack max value: {d}\n", .{dp[capacity]});
}

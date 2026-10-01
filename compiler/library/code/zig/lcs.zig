// Наибольшая общая подпоследовательность: размеры таблицы известны на этапе компиляции (comptime).
const std = @import("std");

fn lcs(comptime a: []const u8, comptime b: []const u8) u32 {
    var dp = [_][b.len + 1]u32{[_]u32{0} ** (b.len + 1)} ** (a.len + 1);
    for (1..a.len + 1) |i| {
        for (1..b.len + 1) |j| {
            dp[i][j] = if (a[i - 1] == b[j - 1]) dp[i - 1][j - 1] + 1 else @max(dp[i - 1][j], dp[i][j - 1]);
        }
    }
    return dp[a.len][b.len];
}

pub fn main() !void {
    const out = std.io.getStdOut().writer();
    try out.print("LCS(ABCBDAB, BDCABA) = {d}\n", .{lcs("ABCBDAB", "BDCABA")});
}

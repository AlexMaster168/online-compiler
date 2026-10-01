// Быстрое возведение в степень: O(log n). Произведение < 2^60 — u64 хватает.
const std = @import("std");

const mod: u64 = 1_000_000_007;

fn powerMod(base: u64, exp: u64, m: u64) u64 {
    var result: u64 = 1;
    var b = base % m;
    var e = exp;
    while (e > 0) : (e >>= 1) {
        if (e & 1 == 1) result = result * b % m;
        b = b * b % m;
    }
    return result;
}

pub fn main() !void {
    const out = std.io.getStdOut().writer();
    try out.print("2^30 mod {d} = {d}\n", .{ mod, powerMod(2, 30, mod) });
    try out.print("3^200 mod {d} = {d}\n", .{ mod, powerMod(3, 200, mod) });
}

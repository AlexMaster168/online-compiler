// Решето Эратосфена: массив флагов известного на этапе компиляции размера ([_]bool{false} ** 51).
const std = @import("std");

pub fn main() !void {
    const out = std.io.getStdOut().writer();
    const n = 50;
    var composite = [_]bool{false} ** (n + 1);
    try out.writeAll("Primes up to 50:");
    var p: usize = 2;
    while (p <= n) : (p += 1) {
        if (composite[p]) continue;
        try out.print(" {d}", .{p});
        var k = p * p;
        while (k <= n) : (k += p) composite[k] = true;
    }
    try out.writeAll("\n");
}

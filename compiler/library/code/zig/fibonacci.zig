// Числа Фибоначчи итеративно. Переполнение u64 в ReleaseSafe — паника, а не тихий мусор.
const std = @import("std");

fn fib(n: u32) u64 {
    var a: u64 = 0;
    var b: u64 = 1;
    for (0..n) |_| {
        const t = a + b;
        a = b;
        b = t;
    }
    return a;
}

pub fn main() !void {
    const out = std.io.getStdOut().writer();
    try out.writeAll("Fibonacci:");
    for (0..15) |i| try out.print(" {d}", .{fib(@intCast(i))});
    try out.print("\nF(50) = {d}\n", .{fib(50)});
}

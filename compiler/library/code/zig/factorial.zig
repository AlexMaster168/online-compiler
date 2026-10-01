// Факториал рекурсией. 20! — предел u64.
const std = @import("std");

fn factorial(n: u64) u64 {
    return if (n <= 1) 1 else n * factorial(n - 1);
}

pub fn main() !void {
    const out = std.io.getStdOut().writer();
    try out.print("10! = {d}\n", .{factorial(10)});
    try out.print("20! = {d}\n", .{factorial(20)});
}

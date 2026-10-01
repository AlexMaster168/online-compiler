// НОД по Евклиду: gcd(a, b) = gcd(b, a % b). (В std.math есть gcd — пишем свой.)
const std = @import("std");

fn gcd(a: u64, b: u64) u64 {
    return if (b == 0) a else gcd(b, a % b);
}

fn lcm(a: u64, b: u64) u64 {
    return a / gcd(a, b) * b;
}

pub fn main() !void {
    const out = std.io.getStdOut().writer();
    try out.print("GCD(48, 18) = {d}\n", .{gcd(48, 18)});
    try out.print("LCM(48, 18) = {d}\n", .{lcm(48, 18)});
}

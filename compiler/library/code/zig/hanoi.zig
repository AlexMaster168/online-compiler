// Ханойские башни. У рекурсивной функции Zig не выводит множество ошибок сам — указываем его явно.
const std = @import("std");

const Writer = std.fs.File.Writer;

fn hanoi(out: Writer, n: u32, source: u8, spare: u8, target: u8) Writer.Error!u32 {
    if (n == 0) return 0;
    const before = try hanoi(out, n - 1, source, target, spare);
    try out.print("Move disk {d} from {c} to {c}\n", .{ n, source, target });
    return before + 1 + try hanoi(out, n - 1, spare, source, target);
}

pub fn main() !void {
    const out = std.io.getStdOut().writer();
    const moves = try hanoi(out, 3, 'A', 'B', 'C');
    try out.print("Total moves: {d}\n", .{moves});
}

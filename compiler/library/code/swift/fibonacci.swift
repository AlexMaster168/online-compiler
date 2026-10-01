// Числа Фибоначчи ленивой последовательностью sequence(state:next:).
let fibonacci = sequence(state: (0, 1)) { (state: inout (Int, Int)) -> Int? in
    defer { state = (state.1, state.0 + state.1) }
    return state.0
}

print("Fibonacci:", fibonacci.prefix(15).map(String.init).joined(separator: " "))
print("F(50) = \(Array(fibonacci.prefix(51)).last!)")

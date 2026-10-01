-- Числа Фибоначчи: каждая строка CTE — пара соседних чисел (a, b) -> (b, a + b).
WITH RECURSIVE fib(n, a, b) AS (
    SELECT 0, 0, 1
    UNION ALL
    SELECT n + 1, b, a + b FROM fib WHERE n < 50
)
SELECT 'Fibonacci: ' || (SELECT group_concat(a, ' ') FROM fib WHERE n < 15) AS result
UNION ALL
SELECT 'F(50) = ' || a FROM fib WHERE n = 50;

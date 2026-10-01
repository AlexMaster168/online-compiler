-- Факториал через рекурсивный CTE: n! = n * (n - 1)!. Целые в SQLite 64-битные — 20! помещается.
WITH RECURSIVE fact(n, f) AS (
    SELECT 0, 1
    UNION ALL
    SELECT n + 1, f * (n + 1) FROM fact WHERE n < 20
)
SELECT n || '! = ' || f AS result
FROM fact
WHERE n IN (10, 20)
ORDER BY n;

-- НОД по Евклиду: рекурсивный CTE повторяет (a, b) -> (b, a % b), пока b не станет 0.
WITH RECURSIVE euclid(a, b) AS (
    SELECT 48, 18
    UNION ALL
    SELECT b, a % b FROM euclid WHERE b <> 0
)
SELECT 'GCD(48, 18) = ' || a AS result FROM euclid WHERE b = 0
UNION ALL
SELECT 'LCM(48, 18) = ' || (48 / a * 18) FROM euclid WHERE b = 0;

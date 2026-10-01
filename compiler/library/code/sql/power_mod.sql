-- Быстрое возведение в степень: на каждом шаге показатель делится пополам (exp >> 1),
-- основание возводится в квадрат, а при нечётном показателе домножаем результат.
WITH RECURSIVE pw(label, base, exp, result) AS (
    VALUES ('2^30', 2, 30, 1), ('3^200', 3, 200, 1)
    UNION ALL
    SELECT label,
           base * base % 1000000007,
           exp >> 1,
           CASE WHEN exp & 1 THEN result * base % 1000000007 ELSE result END
    FROM pw
    WHERE exp > 0
)
SELECT label || ' mod 1000000007 = ' || result AS result
FROM pw
WHERE exp = 0
ORDER BY length(label), label;

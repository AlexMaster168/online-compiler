-- Решето Эратосфена: flags — JSON-массив, flags[k] = 1, если k вычеркнуто.
-- Каждая строка CTE обрабатывает одно p: если p ещё не вычеркнуто, вычёркиваем p*p, p*p + p, ...
WITH RECURSIVE
    nums(k) AS (SELECT 0 UNION ALL SELECT k + 1 FROM nums WHERE k < 50),
    sieve(p, flags) AS (
        SELECT 2, (SELECT json_group_array(k < 2) FROM nums)
        UNION ALL
        SELECT p + 1,
               CASE WHEN flags ->> p = 0
                    THEN (SELECT json_group_array(CASE WHEN key >= p * p AND key % p = 0 THEN 1 ELSE value END)
                          FROM json_each(flags))
                    ELSE flags END
        FROM sieve
        WHERE p * p <= 50
    )
SELECT 'Primes up to 50: ' || (SELECT group_concat(key, ' ') FROM json_each(flags) WHERE value = 0) AS result
FROM sieve
ORDER BY p DESC
LIMIT 1;

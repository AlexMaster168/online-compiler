-- Ханойские башни без рекурсии: у хода номер m (с 1) переносится диск «номер младшего
-- единичного бита m», со стержня (m & (m - 1)) % 3 на ((m | (m - 1)) + 1) % 3.
-- Для нечётного числа дисков башня оказывается на третьем стержне (C).
WITH RECURSIVE moves(m) AS (
    SELECT 1
    UNION ALL
    SELECT m + 1 FROM moves WHERE m < (1 << 3) - 1
)
SELECT 'Move disk '
       || CASE WHEN m & 1 THEN 1 WHEN m & 2 THEN 2 WHEN m & 4 THEN 3 WHEN m & 8 THEN 4 ELSE 5 END
       || ' from ' || substr('ABC', (m & (m - 1)) % 3 + 1, 1)
       || ' to ' || substr('ABC', ((m | (m - 1)) + 1) % 3 + 1, 1) AS result
FROM moves
UNION ALL
SELECT 'Total moves: ' || ((1 << 3) - 1);

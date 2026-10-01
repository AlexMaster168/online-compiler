-- Поиск в глубину с явным стеком: каждая строка CTE снимает вершину с вершины стека.
-- Если вершина новая — отмечаем её и кладём соседей в обратном порядке (меньший окажется сверху).
CREATE TABLE edges (a INTEGER, b INTEGER);
INSERT INTO edges VALUES (0, 1), (0, 2), (1, 3), (2, 4), (3, 5), (4, 5);
CREATE VIEW adj AS SELECT a, b FROM edges UNION SELECT b, a FROM edges;

WITH RECURSIVE dfs(stack, visited, ord) AS (
    SELECT json('[0]'), ',', ''
    UNION ALL
    SELECT
        CASE WHEN instr(visited, ',' || (stack ->> '$[#-1]') || ',') > 0
             THEN json_remove(stack, '$[#-1]')
             ELSE (SELECT json_group_array(x) FROM (
                       SELECT 0 AS part, key AS k, value AS x FROM json_each(json_remove(stack, '$[#-1]'))
                       UNION ALL
                       SELECT 1, -b, b FROM adj WHERE a = stack ->> '$[#-1]'
                       ORDER BY part, k))
        END,
        CASE WHEN instr(visited, ',' || (stack ->> '$[#-1]') || ',') > 0 THEN visited
             ELSE visited || (stack ->> '$[#-1]') || ',' END,
        CASE WHEN instr(visited, ',' || (stack ->> '$[#-1]') || ',') > 0 THEN ord
             ELSE ord || ' ' || (stack ->> '$[#-1]') END
    FROM dfs
    WHERE json_array_length(stack) > 0
)
SELECT 'DFS order:' || ord AS result
FROM dfs
WHERE json_array_length(stack) = 0;

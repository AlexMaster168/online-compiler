-- Поиск в ширину по-SQL-ному: волна от стартовой вершины. На шаге d в CTE попадают
-- все вершины, достижимые за d рёбер; кратчайшее расстояние — минимум d по вершине.
CREATE TABLE edges (a INTEGER, b INTEGER);
INSERT INTO edges VALUES (0, 1), (0, 2), (1, 3), (2, 4), (3, 5), (4, 5);

-- граф неориентированный: ребро идёт в обе стороны
CREATE VIEW adj AS SELECT a, b FROM edges UNION SELECT b, a FROM edges;

WITH RECURSIVE
    wave(v, d) AS (
        SELECT 0, 0
        UNION
        SELECT adj.b, wave.d + 1 FROM wave JOIN adj ON adj.a = wave.v WHERE wave.d < 5
    ),
    dist(v, d) AS (SELECT v, min(d) FROM wave GROUP BY v)
SELECT 'BFS order: ' || (SELECT group_concat(v, ' ') FROM (SELECT v FROM dist ORDER BY d, v)) AS result
UNION ALL
SELECT 'Distances: ' || (SELECT group_concat(d, ' ') FROM (SELECT d FROM dist ORDER BY v));

-- Дейкстра за O(V^2) двумя чередующимися шагами:
--   pick  — выбираем ближайшую необработанную вершину v,
--   relax — улучшаем расстояния через рёбра из v и помечаем её обработанной.
CREATE TABLE edges (a INTEGER, b INTEGER, w INTEGER);
INSERT INTO edges VALUES (0, 1, 4), (0, 2, 1), (2, 1, 2), (1, 3, 1), (2, 3, 5), (3, 4, 3);

WITH RECURSIVE dj(phase, v, dist, done) AS (
    SELECT 'pick', NULL, json('[0, 1000000000, 1000000000, 1000000000, 1000000000]'), json('[0, 0, 0, 0, 0]')
    UNION ALL
    SELECT
        CASE phase WHEN 'pick' THEN 'relax' ELSE 'pick' END,
        CASE phase
            WHEN 'pick' THEN (SELECT d.key FROM json_each(dist) d
                              WHERE done ->> d.key = 0 AND d.value < 1000000000
                              ORDER BY d.value, d.key LIMIT 1)
        END,
        CASE phase
            WHEN 'relax' THEN (SELECT json_group_array(nd) FROM (
                SELECT min(d.value, coalesce((SELECT (dist ->> v) + e.w FROM edges e WHERE e.a = v AND e.b = d.key),
                                             d.value)) AS nd
                FROM json_each(dist) d ORDER BY d.key))
            ELSE dist
        END,
        CASE phase WHEN 'relax' THEN json_set(done, '$[' || v || ']', 1) ELSE done END
    FROM dj
    WHERE phase = 'pick' OR v IS NOT NULL
)
SELECT 'Dijkstra from 0: ' || (SELECT group_concat(value, ' ') FROM json_each(dist)) AS result
FROM dj
WHERE phase = 'relax' AND v IS NULL;

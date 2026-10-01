-- Дейкстра: Data.Set как приоритетная очередь пар (расстояние, вершина). O((V + E) log V).
import qualified Data.Map as Map
import qualified Data.Set as Set

graph :: Map.Map Int [(Int, Int)]
graph = Map.fromList [(0, [(1, 4), (2, 1)]), (1, [(3, 1)]), (2, [(1, 2), (3, 5)]), (3, [(4, 3)]), (4, [])]

dijkstra :: Int -> Map.Map Int Int
dijkstra start = go (Set.singleton (0, start)) (Map.singleton start 0)
  where
    go queue dist = case Set.minView queue of
      Nothing -> dist
      Just ((d, v), rest)
        | d > Map.findWithDefault maxBound v dist -> go rest dist -- устаревшая запись
        | otherwise -> uncurry go (foldl relax (rest, dist) (graph Map.! v))
        where
          relax (q, ds) (u, w)
            | d + w < Map.findWithDefault maxBound u ds = (Set.insert (d + w, u) q, Map.insert u (d + w) ds)
            | otherwise = (q, ds)

main :: IO ()
main = putStrLn $ "Dijkstra from 0: " ++ unwords (map show (Map.elems (dijkstra 0)))

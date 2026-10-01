;; Поиск в глубину: вектор посещённых протягиваем через reduce.
(require '[clojure.string :as str])

(def graph {0 [1 2], 1 [0 3], 2 [0 4], 3 [1 5], 4 [2 5], 5 [3 4]})

(defn dfs [visited v]
  (if (some #{v} visited)
    visited
    (reduce dfs (conj visited v) (graph v))))

(println (str "DFS order: " (str/join " " (dfs [] 0))))

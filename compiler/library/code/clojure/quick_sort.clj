;; Быстрая сортировка: опора — первый элемент, filter / remove делят остальные.
(require '[clojure.string :as str])

(defn quick-sort [[pivot & rest]]
  (if (nil? pivot)
    []
    (concat (quick-sort (filter #(< % pivot) rest))
            [pivot]
            (quick-sort (remove #(< % pivot) rest)))))

(println (str "Sorted: " (str/join " " (quick-sort [10 7 8 9 1 5 3]))))

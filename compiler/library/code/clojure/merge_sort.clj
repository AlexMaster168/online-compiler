;; Сортировка слиянием: loop/recur — хвостовая рекурсия без роста стека.
(require '[clojure.string :as str])

(defn merge-lists [xs ys]
  (loop [xs xs, ys ys, acc []]
    (cond
      (empty? xs) (into acc ys)
      (empty? ys) (into acc xs)
      (<= (first xs) (first ys)) (recur (rest xs) ys (conj acc (first xs)))
      :else (recur xs (rest ys) (conj acc (first ys))))))

(defn merge-sort [v]
  (if (<= (count v) 1)
    v
    (let [[left right] (split-at (quot (count v) 2) v)]
      (merge-lists (merge-sort left) (merge-sort right)))))

(println (str "Sorted: " (str/join " " (merge-sort [38 27 43 3 9 82 10]))))

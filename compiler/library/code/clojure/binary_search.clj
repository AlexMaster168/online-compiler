;; Бинарный поиск: loop/recur по границам отрезка. Векторы дают доступ по индексу за O(1).
(defn binary-search [v target]
  (loop [lo 0, hi (dec (count v))]
    (when (<= lo hi)
      (let [mid (quot (+ lo hi) 2)
            value (v mid)]
        (cond
          (= value target) mid
          (< value target) (recur (inc mid) hi)
          :else (recur lo (dec mid)))))))

(let [arr [1 3 5 7 9 11 13 15 17 19]]
  (doseq [target [7 4]]
    (if-let [i (binary-search arr target)]
      (println (str "Found " target " at index " i))
      (println (str target " not found")))))

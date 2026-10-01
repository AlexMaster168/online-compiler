;; Наибольшая общая подпоследовательность: memoize кеширует рекурсию по индексам — O(n * m).
(declare lcs-memo)

(defn lcs [a b i j]
  (cond
    (or (zero? i) (zero? j)) 0
    (= (nth a (dec i)) (nth b (dec j))) (inc (lcs-memo a b (dec i) (dec j)))
    :else (max (lcs-memo a b (dec i) j) (lcs-memo a b i (dec j)))))

(def lcs-memo (memoize lcs))

(let [a "ABCBDAB", b "BDCABA"]
  (println (str "LCS(" a ", " b ") = " (lcs-memo a b (count a) (count b)))))

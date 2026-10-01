;;; Сортировка слиянием: subseq делит список пополам, merge-lists сливает.
(defun merge-lists (xs ys)
  (cond ((null xs) ys)
        ((null ys) xs)
        ((<= (first xs) (first ys)) (cons (first xs) (merge-lists (rest xs) ys)))
        (t (cons (first ys) (merge-lists xs (rest ys))))))

(defun merge-sort (list)
  (if (<= (length list) 1)
      list
      (let ((half (floor (length list) 2)))
        (merge-lists (merge-sort (subseq list 0 half))
                     (merge-sort (subseq list half))))))

(format t "Sorted: ~{~a~^ ~}~%" (merge-sort '(38 27 43 3 9 82 10)))

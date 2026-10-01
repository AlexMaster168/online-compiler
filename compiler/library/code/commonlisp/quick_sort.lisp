;;; Быстрая сортировка на списках: remove-if-not / remove-if делят хвост относительно опоры.
(defun quick-sort (list)
  (if (null list)
      nil
      (let ((pivot (first list))
            (rest (rest list)))
        (append (quick-sort (remove-if-not (lambda (x) (< x pivot)) rest))
                (list pivot)
                (quick-sort (remove-if (lambda (x) (< x pivot)) rest))))))

(format t "Sorted: ~{~a~^ ~}~%" (quick-sort '(10 7 8 9 1 5 3)))

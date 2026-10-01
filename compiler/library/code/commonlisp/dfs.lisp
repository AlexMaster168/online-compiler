;;; Поиск в глубину рекурсией: labels — локальная (в том числе рекурсивная) функция.
(defparameter *graph* #((1 2) (0 3) (0 4) (1 5) (2 5) (3 4)))

(let ((visited (make-array 6 :initial-element nil))
      (order '()))
  (labels ((dfs (v)
             (setf (aref visited v) t)
             (push v order)
             (dolist (u (aref *graph* v))
               (unless (aref visited u) (dfs u)))))
    (dfs 0))
  (format t "DFS order: ~{~a~^ ~}~%" (reverse order)))

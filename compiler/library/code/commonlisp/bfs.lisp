;;; Поиск в ширину: очередь — список, граф — вектор списков соседей.
(defparameter *graph* #((1 2) (0 3) (0 4) (1 5) (2 5) (3 4)))

(let ((dist (make-array 6 :initial-element -1))
      (queue (list 0))
      (order '()))
  (setf (aref dist 0) 0)
  (loop while queue
        do (let ((v (pop queue)))
             (push v order)
             (dolist (u (aref *graph* v))
               (when (= (aref dist u) -1)
                 (setf (aref dist u) (1+ (aref dist v)))
                 (setf queue (append queue (list u)))))))
  (format t "BFS order: ~{~a~^ ~}~%" (reverse order))
  (format t "Distances: ~{~a~^ ~}~%" (coerce dist 'list)))

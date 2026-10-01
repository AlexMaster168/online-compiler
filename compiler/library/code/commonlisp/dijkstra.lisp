;;; Дейкстра за O(V^2) на двумерном массиве весов (0 — нет ребра).
(defparameter *w* #2A((0 4 1 0 0)
                      (0 0 0 1 0)
                      (0 2 0 5 0)
                      (0 0 0 0 3)
                      (0 0 0 0 0)))

(let* ((n 5)
       (inf most-positive-fixnum)
       (dist (make-array n :initial-element inf))
       (done (make-array n :initial-element nil)))
  (setf (aref dist 0) 0)
  (loop repeat n
        do (let ((v (loop with best = nil
                          for i below n
                          unless (aref done i)
                            do (when (or (null best) (< (aref dist i) (aref dist best)))
                                 (setf best i))
                          finally (return best))))
             (when (= (aref dist v) inf) (return))
             (setf (aref done v) t)
             (dotimes (u n)
               (let ((w (aref *w* v u)))
                 (when (and (> w 0) (< (+ (aref dist v) w) (aref dist u)))
                   (setf (aref dist u) (+ (aref dist v) w)))))))
  (format t "Dijkstra from 0: ~{~a~^ ~}~%" (coerce dist 'list)))

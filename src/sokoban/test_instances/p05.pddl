;; ########
;; #@     #
;; # .$$. #
;; # $..$ #
;; # $..$ #
;; #      #
;; ########

;;  (at player-01 pos-2-2)
;;  (at stone-01 pos-4-3)
;;  (at stone-02 pos-5-3)
;;  (at stone-03 pos-3-4)
;;  (at stone-04 pos-6-4)
;;  (at stone-05 pos-3-5)
;;  (at stone-06 pos-6-5)


(define (problem p095-microban-sequential)
  (:domain sokoban-sequential)
  (:objects
    dir-down - direction
    dir-left - direction
    dir-right - direction
    dir-up - direction
    player-01 - player
    pos-1-1 - location
    pos-1-2 - location
    pos-1-3 - location
    pos-1-4 - location
    pos-1-5 - location
    pos-1-6 - location
    pos-1-7 - location
    pos-2-1 - location
    pos-2-2 - location
    pos-2-3 - location
    pos-2-4 - location
    pos-2-5 - location
    pos-2-6 - location
    pos-2-7 - location
    pos-3-1 - location
    pos-3-2 - location
    pos-3-3 - location
    pos-3-4 - location
    pos-3-5 - location
    pos-3-6 - location
    pos-3-7 - location
    pos-4-1 - location
    pos-4-2 - location
    pos-4-3 - location
    pos-4-4 - location
    pos-4-5 - location
    pos-4-6 - location
    pos-4-7 - location
    pos-5-1 - location
    pos-5-2 - location
    pos-5-3 - location
    pos-5-4 - location
    pos-5-5 - location
    pos-5-6 - location
    pos-5-7 - location
    pos-6-1 - location
    pos-6-2 - location
    pos-6-3 - location
    pos-6-4 - location
    pos-6-5 - location
    pos-6-6 - location
    pos-6-7 - location
    pos-7-1 - location
    pos-7-2 - location
    pos-7-3 - location
    pos-7-4 - location
    pos-7-5 - location
    pos-7-6 - location
    pos-7-7 - location
    pos-8-1 - location
    pos-8-2 - location
    pos-8-3 - location
    pos-8-4 - location
    pos-8-5 - location
    pos-8-6 - location
    pos-8-7 - location
    stone-01 - stone
    stone-02 - stone
    stone-03 - stone
    stone-04 - stone
    stone-05 - stone
    stone-06 - stone
  )
  (:init
    (IS-GOAL pos-3-3)
    (IS-GOAL pos-4-4)
    (IS-GOAL pos-4-5)
    (IS-GOAL pos-5-4)
    (IS-GOAL pos-5-5)
    (IS-GOAL pos-6-3)
    (IS-NONGOAL pos-1-1)
    (IS-NONGOAL pos-1-2)
    (IS-NONGOAL pos-1-3)
    (IS-NONGOAL pos-1-4)
    (IS-NONGOAL pos-1-5)
    (IS-NONGOAL pos-1-6)
    (IS-NONGOAL pos-1-7)
    (IS-NONGOAL pos-2-1)
    (IS-NONGOAL pos-2-2)
    (IS-NONGOAL pos-2-3)
    (IS-NONGOAL pos-2-4)
    (IS-NONGOAL pos-2-5)
    (IS-NONGOAL pos-2-6)
    (IS-NONGOAL pos-2-7)
    (IS-NONGOAL pos-3-1)
    (IS-NONGOAL pos-3-2)
    (IS-NONGOAL pos-3-4)
    (IS-NONGOAL pos-3-5)
    (IS-NONGOAL pos-3-7)
    (IS-NONGOAL pos-4-1)
    (IS-NONGOAL pos-4-2)
    (IS-NONGOAL pos-4-3)
    (IS-NONGOAL pos-4-6)
    (IS-NONGOAL pos-4-7)
    (IS-NONGOAL pos-5-1)
    (IS-NONGOAL pos-5-2)
    (IS-NONGOAL pos-5-3)
    (IS-NONGOAL pos-5-6)
    (IS-NONGOAL pos-5-7)
    (IS-NONGOAL pos-6-1)
    (IS-NONGOAL pos-6-2)
    (IS-NONGOAL pos-6-3)
    (IS-NONGOAL pos-6-4)
    (IS-NONGOAL pos-6-5)
    (IS-NONGOAL pos-6-6)
    (IS-NONGOAL pos-6-7)
    (IS-NONGOAL pos-7-1)
    (IS-NONGOAL pos-7-2)
    (IS-NONGOAL pos-7-3)
    (IS-NONGOAL pos-7-4)
    (IS-NONGOAL pos-7-5)
    (IS-NONGOAL pos-7-6)
    (IS-NONGOAL pos-7-7)
    (IS-NONGOAL pos-8-1)
    (IS-NONGOAL pos-8-2)
    (IS-NONGOAL pos-8-3)
    (IS-NONGOAL pos-8-4)
    (IS-NONGOAL pos-8-5)
    (IS-NONGOAL pos-8-6)
    (IS-NONGOAL pos-8-7)
    (MOVE-DIR pos-2-2 pos-2-3 dir-down)
    (MOVE-DIR pos-2-2 pos-3-2 dir-right)
    (MOVE-DIR pos-2-3 pos-2-2 dir-up)
    (MOVE-DIR pos-2-3 pos-2-4 dir-down)
    (MOVE-DIR pos-2-3 pos-3-3 dir-right)
    (MOVE-DIR pos-2-4 pos-2-3 dir-up)
    (MOVE-DIR pos-2-4 pos-2-5 dir-down)
    (MOVE-DIR pos-2-4 pos-3-4 dir-right)
    (MOVE-DIR pos-2-5 pos-2-4 dir-up)
    (MOVE-DIR pos-2-5 pos-2-6 dir-down)
    (MOVE-DIR pos-2-5 pos-3-5 dir-right)
    (MOVE-DIR pos-2-6 pos-2-5 dir-up)
    (MOVE-DIR pos-2-6 pos-3-6 dir-right)
    (MOVE-DIR pos-3-2 pos-2-2 dir-left)
    (MOVE-DIR pos-3-2 pos-3-3 dir-down)
    (MOVE-DIR pos-3-2 pos-4-2 dir-right)
    (MOVE-DIR pos-3-3 pos-2-3 dir-left)
    (MOVE-DIR pos-3-3 pos-3-2 dir-up)
    (MOVE-DIR pos-3-3 pos-3-4 dir-down)
    (MOVE-DIR pos-3-3 pos-4-3 dir-right)
    (MOVE-DIR pos-3-4 pos-2-4 dir-left)
    (MOVE-DIR pos-3-4 pos-3-3 dir-up)
    (MOVE-DIR pos-3-4 pos-3-5 dir-down)
    (MOVE-DIR pos-3-4 pos-4-4 dir-right)
    (MOVE-DIR pos-3-5 pos-2-5 dir-left)
    (MOVE-DIR pos-3-5 pos-3-4 dir-up)
    (MOVE-DIR pos-3-5 pos-3-6 dir-down)
    (MOVE-DIR pos-3-5 pos-4-5 dir-right)
    (MOVE-DIR pos-3-6 pos-2-6 dir-left)
    (MOVE-DIR pos-3-6 pos-3-5 dir-up)
    (MOVE-DIR pos-3-6 pos-4-6 dir-right)
    (MOVE-DIR pos-4-2 pos-3-2 dir-left)
    (MOVE-DIR pos-4-2 pos-4-3 dir-down)
    (MOVE-DIR pos-4-2 pos-5-2 dir-right)
    (MOVE-DIR pos-4-3 pos-3-3 dir-left)
    (MOVE-DIR pos-4-3 pos-4-2 dir-up)
    (MOVE-DIR pos-4-3 pos-4-4 dir-down)
    (MOVE-DIR pos-4-3 pos-5-3 dir-right)
    (MOVE-DIR pos-4-4 pos-3-4 dir-left)
    (MOVE-DIR pos-4-4 pos-4-3 dir-up)
    (MOVE-DIR pos-4-4 pos-4-5 dir-down)
    (MOVE-DIR pos-4-4 pos-5-4 dir-right)
    (MOVE-DIR pos-4-5 pos-3-5 dir-left)
    (MOVE-DIR pos-4-5 pos-4-4 dir-up)
    (MOVE-DIR pos-4-5 pos-4-6 dir-down)
    (MOVE-DIR pos-4-5 pos-5-5 dir-right)
    (MOVE-DIR pos-4-6 pos-3-6 dir-left)
    (MOVE-DIR pos-4-6 pos-4-5 dir-up)
    (MOVE-DIR pos-4-6 pos-5-6 dir-right)
    (MOVE-DIR pos-5-2 pos-4-2 dir-left)
    (MOVE-DIR pos-5-2 pos-5-3 dir-down)
    (MOVE-DIR pos-5-2 pos-6-2 dir-right)
    (MOVE-DIR pos-5-3 pos-4-3 dir-left)
    (MOVE-DIR pos-5-3 pos-5-2 dir-up)
    (MOVE-DIR pos-5-3 pos-5-4 dir-down)
    (MOVE-DIR pos-5-3 pos-6-3 dir-right)
    (MOVE-DIR pos-5-4 pos-4-4 dir-left)
    (MOVE-DIR pos-5-4 pos-5-3 dir-up)
    (MOVE-DIR pos-5-4 pos-5-5 dir-down)
    (MOVE-DIR pos-5-4 pos-6-4 dir-right)
    (MOVE-DIR pos-5-5 pos-4-5 dir-left)
    (MOVE-DIR pos-5-5 pos-5-4 dir-up)
    (MOVE-DIR pos-5-5 pos-5-6 dir-down)
    (MOVE-DIR pos-5-5 pos-6-5 dir-right)
    (MOVE-DIR pos-5-6 pos-4-6 dir-left)
    (MOVE-DIR pos-5-6 pos-5-5 dir-up)
    (MOVE-DIR pos-5-6 pos-6-6 dir-right)
    (MOVE-DIR pos-6-2 pos-5-2 dir-left)
    (MOVE-DIR pos-6-2 pos-6-3 dir-down)
    (MOVE-DIR pos-6-2 pos-7-2 dir-right)
    (MOVE-DIR pos-6-3 pos-5-3 dir-left)
    (MOVE-DIR pos-6-3 pos-6-2 dir-up)
    (MOVE-DIR pos-6-3 pos-6-4 dir-down)
    (MOVE-DIR pos-6-3 pos-7-3 dir-right)
    (MOVE-DIR pos-6-4 pos-5-4 dir-left)
    (MOVE-DIR pos-6-4 pos-6-3 dir-up)
    (MOVE-DIR pos-6-4 pos-6-5 dir-down)
    (MOVE-DIR pos-6-4 pos-7-4 dir-right)
    (MOVE-DIR pos-6-5 pos-5-5 dir-left)
    (MOVE-DIR pos-6-5 pos-6-4 dir-up)
    (MOVE-DIR pos-6-5 pos-6-6 dir-down)
    (MOVE-DIR pos-6-5 pos-7-5 dir-right)
    (MOVE-DIR pos-6-6 pos-5-6 dir-left)
    (MOVE-DIR pos-6-6 pos-6-5 dir-up)
    (MOVE-DIR pos-6-6 pos-7-6 dir-right)
    (MOVE-DIR pos-7-2 pos-6-2 dir-left)
    (MOVE-DIR pos-7-2 pos-7-3 dir-down)
    (MOVE-DIR pos-7-3 pos-6-3 dir-left)
    (MOVE-DIR pos-7-3 pos-7-2 dir-up)
    (MOVE-DIR pos-7-3 pos-7-4 dir-down)
    (MOVE-DIR pos-7-4 pos-6-4 dir-left)
    (MOVE-DIR pos-7-4 pos-7-3 dir-up)
    (MOVE-DIR pos-7-4 pos-7-5 dir-down)
    (MOVE-DIR pos-7-5 pos-6-5 dir-left)
    (MOVE-DIR pos-7-5 pos-7-4 dir-up)
    (MOVE-DIR pos-7-5 pos-7-6 dir-down)
    (MOVE-DIR pos-7-6 pos-6-6 dir-left)
    (MOVE-DIR pos-7-6 pos-7-5 dir-up)
    (at player-01 pos-2-2)
    (at stone-01 pos-4-3)
    (at stone-02 pos-5-3)
    (at stone-03 pos-3-4)
    (at stone-04 pos-6-4)
    (at stone-05 pos-3-5)
    (at stone-06 pos-6-5)
    (clear pos-2-3)
    (clear pos-2-4)
    (clear pos-2-5)
    (clear pos-2-6)
    (clear pos-3-2)
    (clear pos-3-3)
    (clear pos-3-6)
    (clear pos-4-2)
    (clear pos-4-4)
    (clear pos-4-5)
    (clear pos-5-2)
    (clear pos-5-4)
    (clear pos-5-5)
    (clear pos-6-2)
    (clear pos-6-3)
    (clear pos-6-6)
    (clear pos-7-2)
    (clear pos-7-3)
    (clear pos-7-4)
    (clear pos-7-5)
    (clear pos-7-6)
  )
  (:goal (and
    (at-goal stone-01)
    (at-goal stone-02)
    (at-goal stone-03)
    (at-goal stone-04)
    (at-goal stone-05)
    (at-goal stone-06)
  ))
)

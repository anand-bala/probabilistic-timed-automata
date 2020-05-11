"""
Bouyer, Fahrenberg, Larsen and Markey
Quantitative analysis of real-time systems using priced timed automata
Communications of the ACM, 54(9):78–87, 2011


The basic model concerns computing the arithmetic expression D × (C × (A + B))
+ ((A + B) + (C × D)) using two processors (P1 and P2) that have different
speed and energy requirements.

```
// basic task graph model from
// Bouyer, Fahrenberg, Larsen and Markey
// Quantitative analysis of real-time systems using priced timed automata
// Communications of the ACM, 54(9):78–87, 2011

pta // model is a PTA

module scheduler

        task1 : [0..3]; // A+B
        task2 : [0..3]; // CxD
        task3 : [0..3]; // Cx(A+B)
        task4 : [0..3]; // (A+B)+(CxD)
        task5 : [0..3]; // DxCx(A+B)
        task6 : [0..3]; // (DxCx(A+B)) + ((A+B)+(CxD))

        // task status: 
        // 0 - not started
        // 1 - running on processor 1
        // 2 - running on processor 2
        // 3 - task complete

        // start task 1
        [p1_add] task1=0 -> (task1'=1);
        [p2_add] task1=0 -> (task1'=2);

        // start task 2
        [p1_mult] task2=0 -> (task2'=1);
        [p2_mult] task2=0 -> (task2'=2);

        // start task 3 (must wait for task 1 to complete)
        [p1_mult] task3=0 & task1=3 -> (task3'=1);
        [p2_mult] task3=0 & task1=3 -> (task3'=2);

        // start task 4 (must wait for tasks 1 and 2 to complete)
        [p1_add] task4=0 & task1=3 & task2=3 -> (task4'=1);
        [p2_add] task4=0 & task1=3 & task2=3 -> (task4'=2);

        // start task 5 (must wait for task 3 to complete)
        [p1_mult] task5=0 & task3=3 -> (task5'=1);
        [p2_mult] task5=0 & task3=3 -> (task5'=2);

        // start task 6 (must wait for tasks 4 and 5 to complete)
        [p1_add] task6=0 & task4=3 & task5=3 -> (task6'=1);
        [p2_add] task6=0 & task4=3 & task5=3 -> (task6'=2);

        // a task finishes on processor 1
        [p1_done] task1=1 -> (task1'=3);
        [p1_done] task2=1 -> (task2'=3);
        [p1_done] task3=1 -> (task3'=3);
        [p1_done] task4=1 -> (task4'=3);
        [p1_done] task5=1 -> (task5'=3);
        [p1_done] task6=1 -> (task6'=3);

        // a task finishes on processor 2
        [p2_done] task1=2 -> (task1'=3);
        [p2_done] task2=2 -> (task2'=3);
        [p2_done] task3=2 -> (task3'=3);
        [p2_done] task4=2 -> (task4'=3);
        [p2_done] task5=2 -> (task5'=3);
        [p2_done] task6=2 -> (task6'=3);

endmodule

// processor 1
module P1

        p1 : [0..2];
        // 0 - idle
        // 1 - add
        // 2 - multiply

        x1 : clock; // local clock

        invariant
        (p1=1 => x1<=2) &
        (p1=2 => x1<=3)
    endinvariant

        // addition
        [p1_add] p1=0 -> (p1'=1) & (x1'=0); // start
        [p1_done] p1=1 & x1=2 -> (p1'=0) & (x1'=0); // finish

        // multiplication
        [p1_mult] p1=0 -> (p1'=2) & (x1'=0); // start
        [p1_done] p1=2 & x1=3 -> (p1'=0) & (x1'=0);  // finish

endmodule

// processor 2
module P2

        p2 : [0..2];
        // 0 - idle
        // 1 - add
        // 2 - multiply

        x2 : clock; // local clock

        invariant
        (p2=1 => x2<=5) &
        (p2=2 => x2<=7)
    endinvariant

        // addition
        [p2_add] p2=0 -> (p2'=1) & (x2'=0); // start
        [p2_done] p2=1 & x2=5 -> (p2'=0) & (x2'=0); // finish

        // multiplication
        [p2_mult] p2=0 -> (p2'=2) & (x2'=0); // start
        [p2_done] p2=2 & x2=7 -> (p2'=0) & (x2'=0);  // finish

endmodule

// target state (all tasks complete)
label "tasks_complete" = (task6=3);

```

"""

import enum
import functools
import operator
from collections import namedtuple
from itertools import chain, product, repeat
from typing import Mapping, Tuple

from pta import PTA, Clock, ClockConstraint
from pta.clock import Boolean
from pta.distributions import DiscreteDistribution, delta, uniform
from pta.utils import flatten


@enum.unique
class Edges(enum.IntEnum):
    P1_ADD = enum.auto()
    P2_ADD = enum.auto()
    P1_MUL = enum.auto()
    P2_MUL = enum.auto()
    P1_DONE = enum.auto()
    P2_DONE = enum.auto()


TaskLocs = namedtuple(
    "TaskLocs", [f"task{i}" for i in range(1, 7)]
)  # type: Tuple[int, ...]
ProcessLocs = namedtuple("ProcessLocs", ["p1", "p2"])  # type: Tuple[int, int]
PTALocation = namedtuple(
    "PTALocation", TaskLocs._fields + ProcessLocs._fields
)  # type: Tuple[int, ...]

Transition = namedtuple(
    "Transition", ["guard", "target_dist"]
)  # type: Tuple[ClockConstraint, DiscreteDistribution]

Label = namedtuple("Label", ["tasks_complete"])


class Scheduler:

    init_location: TaskLocs = TaskLocs(*repeat(0, 6))

    @staticmethod
    def locations():
        return product(range(4), repeat=6)

    @staticmethod
    def clocks():
        return frozenset()

    @staticmethod
    def invariant(loc) -> ClockConstraint:
        return Boolean(True)

    @staticmethod
    def transitions(loc):
        location = TaskLocs._make(loc)

        def _update(new_val):
            return Transition(Boolean(True), delta((frozenset(), new_val)))

        actions = dict()

        if location.task1 == 0:
            actions[Edges.P1_ADD] = _update(location._replace(task1=1))
            actions[Edges.P2_ADD] = _update(location._replace(task1=2))
        if location.task2 == 0:
            actions[Edges.P1_MUL] = _update(location._replace(task2=1))
            actions[Edges.P2_MUL] = _update(location._replace(task2=2))
        if location.task3 == 0 and location.task1 == 3:
            actions[Edges.P1_MUL] = _update(location._replace(task3=1))
            actions[Edges.P2_MUL] = _update(location._replace(task3=2))
        if location.task4 == 0 and location.task1 == 3 and location.task2 == 3:
            actions[Edges.P1_ADD] = _update(location._replace(task4=1))
            actions[Edges.P2_ADD] = _update(location._replace(task4=2))
        if location.task5 == 0 and location.task3 == 3:
            actions[Edges.P1_MUL] = _update(location._replace(task5=1))
            actions[Edges.P2_MUL] = _update(location._replace(task5=2))
        if location.task6 == 0 and location.task4 == 3 and location.task5 == 3:
            actions[Edges.P1_ADD] = _update(location._replace(task6=1))
            actions[Edges.P2_ADD] = _update(location._replace(task6=2))

        if location.task1 == 1:
            actions[Edges.P1_DONE] = _update(location._replace(task1=3))
        if location.task2 == 1:
            actions[Edges.P1_DONE] = _update(location._replace(task2=3))
        if location.task3 == 1:
            actions[Edges.P1_DONE] = _update(location._replace(task3=3))
        if location.task4 == 1:
            actions[Edges.P1_DONE] = _update(location._replace(task4=3))
        if location.task5 == 1:
            actions[Edges.P1_DONE] = _update(location._replace(task5=3))
        if location.task6 == 1:
            actions[Edges.P1_DONE] = _update(location._replace(task6=3))

        if location.task1 == 2:
            actions[Edges.P2_DONE] = _update(location._replace(task1=3))
        if location.task2 == 2:
            actions[Edges.P2_DONE] = _update(location._replace(task2=3))
        if location.task3 == 2:
            actions[Edges.P2_DONE] = _update(location._replace(task3=3))
        if location.task4 == 2:
            actions[Edges.P2_DONE] = _update(location._replace(task4=3))
        if location.task5 == 2:
            actions[Edges.P2_DONE] = _update(location._replace(task5=3))
        if location.task6 == 2:
            actions[Edges.P2_DONE] = _update(location._replace(task6=3))

        return actions


class P1:
    x1 = Clock("x1")
    init_location = 0

    @staticmethod
    def locations():
        return range(3)

    @staticmethod
    def clocks():
        return frozenset([P1.x1])

    @staticmethod
    def invariant(loc) -> ClockConstraint:
        if loc == 1:
            return P1.x1 <= 2
        if loc == 2:
            return P1.x1 >= 3
        return Boolean(True)

    @staticmethod
    def transitions(loc) -> Mapping[Edges, Transition]:
        actions = dict()

        if loc == 0:
            actions[Edges.P1_ADD] = Transition(Boolean(True), delta((P1.clocks(), 1)))
            actions[Edges.P1_MUL] = Transition(Boolean(True), delta((P1.clocks(), 1)))
        if loc == 1:
            # TODO: Exactly equal may be an issue in the Guard...
            actions[Edges.P1_DONE] = Transition(P1.x1 == 2, delta((P1.clocks(), 0)))
        if loc == 2:
            # TODO: Exactly equal may be an issue in the Guard...
            actions[Edges.P1_DONE] = Transition(P1.x1 == 3, delta((P1.clocks(), 0)))

        return actions


class P2:
    x2 = Clock("x2")
    init_location = 0

    @staticmethod
    def locations():
        return range(3)

    @staticmethod
    def clocks():
        return frozenset([P2.x2])

    @staticmethod
    def invariant(loc) -> ClockConstraint:
        if loc == 1:
            return P2.x2 <= 5
        if loc == 2:
            return P2.x2 >= 7
        return Boolean(True)

    @staticmethod
    def transitions(loc) -> Mapping[Edges, Transition]:
        actions = dict()

        if loc == 0:
            actions[Edges.P2_ADD] = Transition(Boolean(True), delta((P2.clocks(), 1)))
            actions[Edges.P2_MUL] = Transition(Boolean(True), delta((P2.clocks(), 1)))
        if loc == 1:
            # TODO: Exactly equal may be an issue in the Guard...
            actions[Edges.P2_DONE] = Transition(P2.x2 == 5, delta((P2.clocks(), 0)))
        if loc == 2:
            # TODO: Exactly equal may be an issue in the Guard...
            actions[Edges.P2_DONE] = Transition(P2.x2 == 7, delta((P2.clocks(), 0)))

        return actions


def merge_transitions(*transitions: Transition) -> Transition:
    merged_guard: ClockConstraint = functools.reduce(
        operator.and_, [t.guard for t in transitions], Boolean(True)
    )
    merged_target_dist = dict()  # type: Mapping[Tuple[Set[Clock], PTALocation], float]
    for ks in product(*(t.target_dist.support for t in transitions)):
        # Compute the union of clock reset sets
        clock_resets: Set[Clock] = functools.reduce(
            lambda s1, s2: s1.union(s2), [k[0] for k in ks]
        )
        # And compute the flattened location
        pta_loc: PTALocation = PTALocation._make(flatten((k[1] for k in ks)))
        # Compute the product probability
        probs = [t.target_dist(ks[i]) for i, t in enumerate(transitions)]
        new_prob: float = functools.reduce(operator.mul, probs, 1.0)
        merged_target_dist[(clock_resets, pta_loc)] = new_prob
    return Transition(merged_guard, DiscreteDistribution(merged_target_dist))


def create_pta() -> PTA:
    n_locations = (4 ** 6) * 3 * 3  # 6 Tasks * Processor 1 * Processor 2
    clocks = {P1.x1, P2.x2}
    acts = set(Edges)
    init_location = PTALocation(
        *Scheduler.init_location, P1.init_location, P2.init_location
    )

    def transitions(loc) -> Mapping[Edges, Transition]:
        location = PTALocation._make(loc)
        task_loc = location[:6]
        p1_loc = location.p1
        p2_loc = location.p2

        t1 = Scheduler.transitions(task_loc)
        t2 = P1.transitions(p1_loc)
        t3 = P2.transitions(p2_loc)

        # Merge the transitions into one...
        actions = dict()
        for act in set(chain(t1.keys(), t2.keys(), t3.keys())):
            enabled_transitions = [
                t1.get(act, Transition(Boolean(True), delta((frozenset(), task_loc)))),
                t2.get(act, Transition(Boolean(True), delta((frozenset(), p1_loc)))),
                t3.get(act, Transition(Boolean(True), delta((frozenset(), p2_loc)))),
            ]
            actions[act] = merge_transitions(*enabled_transitions)

        return actions

    def invariants(loc) -> ClockConstraint:
        location = PTALocation._make(loc)
        task_loc = location[:6]
        p1_loc = location.p1
        p2_loc = location.p2
        return (
            Scheduler.invariant(task_loc) & P1.invariant(p1_loc) & P2.invariant(p2_loc)
        )

    return PTA(
        n_locations=n_locations,
        clocks=clocks,
        actions=acts,
        init_location=init_location,
        transitions=transitions,
        invariants=invariants,
    )

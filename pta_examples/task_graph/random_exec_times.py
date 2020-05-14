"""
Bouyer, Fahrenberg, Larsen and Markey
Quantitative analysis of real-time systems using priced timed automata
Communications of the ACM, 54(9):78–87, 2011
"""

import enum
import functools
import operator
from itertools import chain, product, repeat
from typing import Mapping, NamedTuple, Set

from pta import PTA, Clock, ClockConstraint
from pta.clock import Boolean
from pta.distributions import DiscreteDistribution, delta
from pta.pta import Target, Transition
from pta.spaces import Space
from pta.utils import flatten


@enum.unique
class Edges(enum.IntEnum):
    P1_ADD = enum.auto()
    P2_ADD = enum.auto()
    P1_MUL = enum.auto()
    P2_MUL = enum.auto()
    P1_DONE = enum.auto()
    P2_DONE = enum.auto()


class TaskLocs(NamedTuple):
    task1: int
    task2: int
    task3: int
    task4: int
    task5: int
    task6: int


class ProcessLocs(NamedTuple):
    p1: int
    p2: int


class PTALocation(NamedTuple):
    task1: int
    task2: int
    task3: int
    task4: int
    task5: int
    task6: int
    p1: int
    p2: int


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
            return P1.x1 <= 3
        return Boolean(True)

    @staticmethod
    def transitions(loc) -> Mapping[Edges, Transition]:
        actions = dict()

        if loc == 0:
            actions[Edges.P1_ADD] = Transition(Boolean(True), delta((P1.clocks(), 1)))
            actions[Edges.P1_MUL] = Transition(Boolean(True), delta((P1.clocks(), 1)))
        if loc == 1:
            # TODO: Exactly equal may be an issue in the Guard...
            actions[Edges.P1_DONE] = Transition(
                (P1.x1 >= 1) & (P1.x1 <= 3), delta((P1.clocks(), 0))
            )
        if loc == 2:
            # TODO: Exactly equal may be an issue in the Guard...
            actions[Edges.P1_DONE] = Transition(
                (P1.x1 >= 2) & (P1.x1 <= 4), delta((P1.clocks(), 0))
            )

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
            return P2.x2 <= 7
        return Boolean(True)

    @staticmethod
    def transitions(loc) -> Mapping[Edges, Transition]:
        actions = dict()

        if loc == 0:
            actions[Edges.P2_ADD] = Transition(Boolean(True), delta((P2.clocks(), 1)))
            actions[Edges.P2_MUL] = Transition(Boolean(True), delta((P2.clocks(), 1)))
        if loc == 1:
            # TODO: Exactly equal may be an issue in the Guard...
            actions[Edges.P2_DONE] = Transition(
                (P2.x2 >= 4) & (P2.x2 <= 6), delta((P2.clocks(), 0))
            )
        if loc == 2:
            # TODO: Exactly equal may be an issue in the Guard...
            actions[Edges.P2_DONE] = Transition(
                (P2.x2 >= 6) & (P2.x2 <= 8), delta((P2.clocks(), 0))
            )

        return actions


def merge_transitions(*transitions: Transition) -> Transition:
    merged_guard: ClockConstraint = functools.reduce(
        operator.and_, [t.guard for t in transitions], Boolean(True)
    )
    merged_target_dist = dict()  # type: Mapping[Target, float]
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
        merged_target_dist[Target(clock_resets, pta_loc)] = new_prob  # type: ignore
    return Transition(merged_guard, DiscreteDistribution(merged_target_dist))


class TaskGraphSpace(Space):
    def __len__(self) -> int:
        return (4 ** 6) * 3 * 3  # 6 Tasks * Processor 1 * Processor 2

    def __contains__(self, x):
        location = PTALocation._make(x)
        return (
            all(loc in range(4) for loc in location[:6])
            and location.p1 in range(3)
            and location.p2 in range(3)
        )

    def sample(self, x):
        import random

        task_locs = random.choices(range(4), k=6)
        proc_locs = random.choices(range(3), k=2)
        return PTALocation(*task_locs, *proc_locs)


def create_pta() -> PTA:
    clocks = {P1.x1, P2.x2}
    acts = {
        Edges.P1_ADD,
        Edges.P2_ADD,
        Edges.P1_MUL,
        Edges.P2_MUL,
    }

    init_location = PTALocation(
        *Scheduler.init_location, P1.init_location, P2.init_location
    )

    def transitions(loc: PTALocation) -> Mapping[Edges, Transition]:
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

    def invariants(loc: PTALocation) -> ClockConstraint:
        location = PTALocation._make(loc)
        task_loc = location[:6]
        p1_loc = location.p1
        p2_loc = location.p2
        return (
            Scheduler.invariant(task_loc) & P1.invariant(p1_loc) & P2.invariant(p2_loc)
        )

    return PTA(
        location_space=TaskGraphSpace(),
        clocks=clocks,  # type: ignore
        actions=acts,  # type: ignore
        init_location=init_location,
        transitions=transitions,  # type: ignore
        invariants=invariants,  # type: ignore
    )

"""Progressive set of PTA constructions from [PRISM model checker task graph][1]


[1] : https://www.prismmodelchecker.org/casestudies/task_graph.php
"""

from .basic import create_pta as deterministic_task_graph
from .random_exec_times import create_pta as randomized_task_graph

from __future__ import annotations

import json
import logging
from typing import Final, List, Optional

from moto.stepfunctions.parser.asl.component.common.parameters import Parameters
from moto.stepfunctions.parser.asl.component.state.exec.state_map.item_selector import (
    ItemSelector,
)
from moto.stepfunctions.parser.asl.component.state.exec.state_map.iteration.inline_iteration_component import (
    InlineIterationComponent,
    InlineIterationComponentEvalInput,
)
from moto.stepfunctions.parser.asl.component.state.exec.state_map.iteration.iterator.iterator_decl import (
    IteratorDecl,
)
from moto.stepfunctions.parser.asl.component.state.exec.state_map.iteration.iterator.iterator_worker import (
    IteratorWorker,
)
from moto.stepfunctions.parser.asl.eval.environment import Environment

LOG = logging.getLogger(__name__)


class IteratorEvalInput(InlineIterationComponentEvalInput):
    parameters: Final[Optional[ItemSelector]]

    def __init__(
        self,
        state_name: str,
        max_concurrency: int,
        input_items: List[json],
        parameters: Optional[Parameters],
    ):
        super().__init__(
            state_name=state_name,
            max_concurrency=max_concurrency,
            input_items=input_items,
        )
        self.parameters = parameters


class Iterator(InlineIterationComponent):
    _eval_input: Optional[IteratorEvalInput]

    def _create_worker(self, env: Environment) -> IteratorWorker:
        return IteratorWorker(
            work_name=self._eval_input.state_name,
            job_pool=self._job_pool,
            env=env,
            parameters=self._eval_input.parameters,
        )

    @classmethod
    def from_declaration(cls, iterator_decl: IteratorDecl):
        return cls(
            start_at=iterator_decl.start_at,
            states=iterator_decl.states,
            comment=iterator_decl.comment,
        )

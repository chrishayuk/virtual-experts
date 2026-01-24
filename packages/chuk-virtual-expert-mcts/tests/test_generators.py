"""Tests for MCTS trace generators."""

from __future__ import annotations

from chuk_virtual_expert.trace_example import TraceExample
from chuk_virtual_expert.trace_models import QueryStep

from chuk_virtual_expert_mcts import MctsExpert, MctsTraceGenerator
from chuk_virtual_expert_mcts.models import (
    ApplyStep,
    EvaluateStep,
    InitSearchStep,
    SearchStep,
)


class TestMctsTraceGenerator:
    def setup_method(self):
        self.gen = MctsTraceGenerator()
        self.expert = MctsExpert()

    def test_generate_search(self):
        example = self.gen.generate_search("counting", target=6, moves=3)
        assert isinstance(example, TraceExample)
        assert example.expert == "mcts"
        assert len(example.trace) == 3
        assert isinstance(example.trace[0], InitSearchStep)
        assert isinstance(example.trace[1], SearchStep)
        assert isinstance(example.trace[2], QueryStep)

    def test_generate_search_and_apply(self):
        example = self.gen.generate_search_and_apply("counting", target=6, moves=3)
        assert isinstance(example, TraceExample)
        assert example.expert == "mcts"
        step_types = [type(s) for s in example.trace]
        assert InitSearchStep in step_types
        assert ApplyStep in step_types

    def test_generate_evaluate(self):
        example = self.gen.generate_evaluate("counting", target=6, moves=3)
        assert isinstance(example, TraceExample)
        step_types = [type(s) for s in example.trace]
        assert EvaluateStep in step_types

    def test_generate_multi_step(self):
        example = self.gen.generate_multi_step("counting", n_steps=2, target=6, moves=4)
        assert isinstance(example, TraceExample)
        step_types = [type(s) for s in example.trace]
        assert step_types.count(SearchStep) == 2
        assert step_types.count(ApplyStep) == 2
        assert EvaluateStep in step_types

    def test_generate_batch(self):
        examples = self.gen.generate("counting", n=10, target=6, moves=3)
        assert len(examples) == 10
        for ex in examples:
            assert isinstance(ex, TraceExample)
            assert ex.expert == "mcts"

    async def test_generated_traces_execute(self):
        examples = self.gen.generate("counting", n=5, target=6, moves=3)
        for example in examples:
            # Patch search/evaluate steps with seed and low iterations for determinism
            patched_steps = []
            for step in example.trace:
                if isinstance(step, SearchStep):
                    step = SearchStep(
                        iterations=50,
                        var=step.var,
                        seed=42,
                        exploration=step.exploration,
                    )
                elif isinstance(step, EvaluateStep):
                    step = EvaluateStep(iterations=50, var=step.var, seed=42)
                patched_steps.append(step)
            result = await self.expert.execute_trace(patched_steps)
            assert result.success, f"Failed: {result.error}"

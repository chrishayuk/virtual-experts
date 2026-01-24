"""Tests for MCTS trace generators."""

from __future__ import annotations

from chuk_virtual_expert_mcts import MctsExpert, MctsTraceGenerator


class TestMctsTraceGenerator:
    def setup_method(self):
        self.gen = MctsTraceGenerator()
        self.expert = MctsExpert()

    def test_generate_search(self):
        trace = self.gen.generate_search("counting", target=6, moves=3)
        assert trace["expert"] == "mcts"
        assert len(trace["trace"]) == 3
        assert "init_search" in trace["trace"][0]
        assert "search" in trace["trace"][1]
        assert "query" in trace["trace"][2]

    def test_generate_search_and_apply(self):
        trace = self.gen.generate_search_and_apply("counting", target=6, moves=3)
        assert trace["expert"] == "mcts"
        ops = [next(iter(s)) for s in trace["trace"]]
        assert "init_search" in ops
        assert "apply" in ops

    def test_generate_evaluate(self):
        trace = self.gen.generate_evaluate("counting", target=6, moves=3)
        ops = [next(iter(s)) for s in trace["trace"]]
        assert "evaluate" in ops

    def test_generate_multi_step(self):
        trace = self.gen.generate_multi_step("counting", n_steps=2, target=6, moves=4)
        ops = [next(iter(s)) for s in trace["trace"]]
        assert ops.count("search") == 2
        assert ops.count("apply") == 2
        assert "evaluate" in ops

    def test_generate_batch(self):
        traces = self.gen.generate("counting", n=10, target=6, moves=3)
        assert len(traces) == 10
        for t in traces:
            assert t["expert"] == "mcts"
            assert "trace" in t

    def test_generated_traces_execute(self):
        traces = self.gen.generate("counting", n=5, target=6, moves=3)
        for trace in traces:
            # Add seed for determinism
            for step in trace["trace"]:
                if "search" in step:
                    step["search"]["seed"] = 42
                    step["search"]["iterations"] = 50
                if "evaluate" in step:
                    step["evaluate"]["seed"] = 42
                    step["evaluate"]["iterations"] = 50
            result = self.expert.execute_trace(trace["trace"])
            assert result.success, f"Failed: {result.error}"

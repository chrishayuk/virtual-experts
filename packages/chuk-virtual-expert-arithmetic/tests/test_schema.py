"""Tests for the schema module (problem, trace, verifier)."""

from __future__ import annotations

from decimal import Decimal

from chuk_virtual_expert_arithmetic.schema import (
    Action,
    Constraint,
    Entity,
    Operation,
    OperationType,
    ProblemSpec,
    ProblemType,
    Query,
    State,
    Step,
    StepError,
    Trace,
    TraceBuilder,
    TraceVerifier,
    VerificationResult,
    VerificationStatus,
    apply_action,
    verify_trace,
    verify_traces,
)

# --- Entity ---


class TestEntity:
    def test_basic_creation(self):
        e = Entity(name="alice", attribute="apples", initial_value=Decimal(5))
        assert e.name == "alice"
        assert e.attribute == "apples"
        assert e.initial_value == Decimal(5)

    def test_optional_fields(self):
        e = Entity(name="x")
        assert e.attribute is None
        assert e.initial_value is None
        assert e.unit is None

    def test_to_dict(self):
        e = Entity(name="price", attribute="dollars", initial_value=Decimal("40.5"), unit="$")
        d = e.to_dict()
        assert d["name"] == "price"
        assert d["attribute"] == "dollars"
        assert d["initial_value"] == 40.5
        assert d["unit"] == "$"

    def test_to_dict_none_value(self):
        e = Entity(name="x")
        d = e.to_dict()
        assert d["initial_value"] is None

    def test_from_dict(self):
        d = {"name": "bob", "attribute": "marbles", "initial_value": 10, "unit": "marbles"}
        e = Entity.from_dict(d)
        assert e.name == "bob"
        assert e.initial_value == Decimal("10")
        assert e.unit == "marbles"

    def test_from_dict_no_value(self):
        d = {"name": "x"}
        e = Entity.from_dict(d)
        assert e.initial_value is None

    def test_roundtrip(self):
        e = Entity(name="test", attribute="items", initial_value=Decimal("3.14"), unit="pcs")
        e2 = Entity.from_dict(e.to_dict())
        assert e2.name == e.name
        assert e2.attribute == e.attribute
        assert e2.unit == e.unit


# --- Operation ---


class TestOperation:
    def test_basic_creation(self):
        op = Operation(type=OperationType.ADD, target="alice", amount=Decimal(5))
        assert op.type == OperationType.ADD
        assert op.target == "alice"
        assert op.amount == Decimal(5)

    def test_transfer(self):
        op = Operation(type=OperationType.TRANSFER, target="bob", source="alice", amount=Decimal(3))
        assert op.source == "alice"
        assert op.target == "bob"

    def test_multiply(self):
        op = Operation(type=OperationType.MULTIPLY, target="price", factor=Decimal("0.75"))
        assert op.factor == Decimal("0.75")

    def test_to_dict(self):
        op = Operation(type=OperationType.SUBTRACT, target="x", amount=Decimal(3), condition="each")
        d = op.to_dict()
        assert d["type"] == "subtract"
        assert d["target"] == "x"
        assert d["amount"] == 3.0
        assert d["condition"] == "each"

    def test_to_dict_none_fields(self):
        op = Operation(type=OperationType.INIT, target="x")
        d = op.to_dict()
        assert d["amount"] is None
        assert d["factor"] is None
        assert d["source"] is None

    def test_from_dict(self):
        d = {"type": "divide", "target": "price", "factor": 2.5}
        op = Operation.from_dict(d)
        assert op.type == OperationType.DIVIDE
        assert op.factor == Decimal("2.5")

    def test_roundtrip(self):
        op = Operation(type=OperationType.TRANSFER, target="bob", source="alice", amount=Decimal(7))
        op2 = Operation.from_dict(op.to_dict())
        assert op2.type == op.type
        assert op2.target == op.target
        assert op2.source == op.source


# --- Query ---


class TestQuery:
    def test_basic(self):
        q = Query(target="alice")
        assert q.target == "alice"
        assert q.question == "value"

    def test_comparison(self):
        q = Query(target="diff", question="compare", compare_a="tom", compare_b="jane")
        assert q.compare_a == "tom"
        assert q.compare_b == "jane"

    def test_to_dict(self):
        q = Query(target="result", question="total")
        d = q.to_dict()
        assert d["target"] == "result"
        assert d["question"] == "total"

    def test_from_dict(self):
        d = {"target": "x", "question": "how_many", "compare_a": "a", "compare_b": "b"}
        q = Query.from_dict(d)
        assert q.question == "how_many"
        assert q.compare_a == "a"

    def test_from_dict_defaults(self):
        q = Query.from_dict({"target": "x"})
        assert q.question == "value"


# --- Constraint ---


class TestConstraint:
    def test_basic(self):
        c = Constraint(type="sum", entities=["a", "b"], value=Decimal(100))
        assert c.type == "sum"
        assert c.value == Decimal(100)

    def test_ratio(self):
        c = Constraint(type="ratio", entities=["alice", "bob"], factor=Decimal(2))
        assert c.factor == Decimal(2)

    def test_to_dict(self):
        c = Constraint(type="sum", entities=["a", "b"], value=Decimal(50))
        d = c.to_dict()
        assert d["type"] == "sum"
        assert d["entities"] == ["a", "b"]
        assert d["value"] == 50.0

    def test_to_dict_none_fields(self):
        c = Constraint(type="equals", entities=["x"])
        d = c.to_dict()
        assert d["factor"] is None
        assert d["value"] is None

    def test_from_dict(self):
        d = {"type": "ratio", "entities": ["a", "b"], "factor": 3}
        c = Constraint.from_dict(d)
        assert c.factor == Decimal("3")

    def test_from_dict_defaults(self):
        c = Constraint.from_dict({"type": "equals"})
        assert c.entities == []
        assert c.factor is None


# --- ProblemSpec ---


class TestProblemSpec:
    def test_defaults(self):
        spec = ProblemSpec()
        assert spec.problem_type == ProblemType.UNKNOWN
        assert spec.entities == []
        assert spec.operations == []

    def test_is_valid_true(self):
        spec = ProblemSpec(
            entities=[Entity(name="x", initial_value=Decimal(5))],
            query=Query(target="x"),
        )
        assert spec.is_valid()

    def test_is_valid_no_entities(self):
        spec = ProblemSpec(query=Query(target="x"))
        assert not spec.is_valid()

    def test_is_valid_no_query(self):
        spec = ProblemSpec(entities=[Entity(name="x")])
        assert not spec.is_valid()

    def test_to_dict(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ENTITY_TRACKING,
            entities=[Entity(name="alice", initial_value=Decimal(10))],
            operations=[Operation(type=OperationType.ADD, target="alice", amount=Decimal(5))],
            query=Query(target="alice"),
            raw_text="test problem",
        )
        d = spec.to_dict()
        assert d["problem_type"] == "entity_tracking"
        assert len(d["entities"]) == 1
        assert len(d["operations"]) == 1
        assert d["query"]["target"] == "alice"
        assert d["raw_text"] == "test problem"

    def test_to_dict_no_query(self):
        spec = ProblemSpec(entities=[Entity(name="x")])
        d = spec.to_dict()
        assert d["query"] is None

    def test_from_dict(self):
        d = {
            "problem_type": "comparison",
            "entities": [{"name": "tom", "initial_value": 15}],
            "operations": [],
            "constraints": [{"type": "sum", "entities": ["a", "b"], "value": 100}],
            "query": {"target": "diff", "question": "compare"},
            "raw_text": "How many more?",
        }
        spec = ProblemSpec.from_dict(d)
        assert spec.problem_type == ProblemType.COMPARISON
        assert spec.entities[0].name == "tom"
        assert len(spec.constraints) == 1
        assert spec.query.target == "diff"

    def test_from_dict_defaults(self):
        spec = ProblemSpec.from_dict({})
        assert spec.problem_type == ProblemType.UNKNOWN
        assert spec.entities == []

    def test_to_json_str(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ARITHMETIC_CHAIN,
            entities=[Entity(name="x", initial_value=Decimal(5))],
            query=Query(target="x"),
        )
        json_str = spec.to_json_str()
        assert "arithmetic_chain" in json_str
        assert '"x"' in json_str

    def test_roundtrip(self):
        spec = ProblemSpec(
            problem_type=ProblemType.PERCENTAGE,
            entities=[Entity(name="price", initial_value=Decimal("40"))],
            operations=[
                Operation(type=OperationType.MULTIPLY, target="price", factor=Decimal("0.75"))
            ],
            query=Query(target="price"),
        )
        spec2 = ProblemSpec.from_dict(spec.to_dict())
        assert spec2.problem_type == spec.problem_type
        assert spec2.entities[0].name == "price"


class TestProblemType:
    def test_all_values(self):
        assert ProblemType.ENTITY_TRACKING.value == "entity_tracking"
        assert ProblemType.ARITHMETIC_CHAIN.value == "arithmetic_chain"
        assert ProblemType.RATE_EQUATION.value == "rate_equation"
        assert ProblemType.ALLOCATION.value == "allocation"
        assert ProblemType.COMPARISON.value == "comparison"
        assert ProblemType.PERCENTAGE.value == "percentage"
        assert ProblemType.UNKNOWN.value == "unknown"


class TestOperationType:
    def test_all_values(self):
        assert OperationType.INIT.value == "init"
        assert OperationType.ADD.value == "add"
        assert OperationType.SUBTRACT.value == "subtract"
        assert OperationType.MULTIPLY.value == "multiply"
        assert OperationType.DIVIDE.value == "divide"
        assert OperationType.TRANSFER.value == "transfer"
        assert OperationType.SET.value == "set"


# --- State ---


class TestState:
    def test_empty(self):
        s = State()
        assert s.get("x") == Decimal(0)

    def test_set_and_get(self):
        s = State().set("x", 5)
        assert s.get("x") == Decimal(5)

    def test_immutable(self):
        s1 = State().set("x", 10)
        s2 = s1.set("x", 20)
        assert s1.get("x") == Decimal(10)
        assert s2.get("x") == Decimal(20)

    def test_copy(self):
        s = State().set("a", 1).set("b", 2)
        s2 = s.copy()
        assert s2.get("a") == Decimal(1)
        assert s == s2

    def test_equality(self):
        s1 = State().set("x", 5)
        s2 = State().set("x", 5)
        assert s1 == s2

    def test_inequality_different_values(self):
        s1 = State().set("x", 5)
        s2 = State().set("x", 10)
        assert s1 != s2

    def test_inequality_non_state(self):
        s = State()
        assert s != "not a state"

    def test_to_dict(self):
        s = State().set("a", Decimal("3.14")).set("b", Decimal(7))
        d = s.to_dict()
        assert d["a"] == 3.14
        assert d["b"] == 7.0

    def test_from_dict(self):
        s = State.from_dict({"x": 5, "y": 2.5})
        assert s.get("x") == Decimal("5")
        assert s.get("y") == Decimal("2.5")


# --- Action ---


class TestAction:
    def test_all_values(self):
        assert Action.INIT.value == "init"
        assert Action.ADD.value == "add"
        assert Action.SUBTRACT.value == "subtract"
        assert Action.MULTIPLY.value == "multiply"
        assert Action.DIVIDE.value == "divide"
        assert Action.TRANSFER.value == "transfer"
        assert Action.COMPARE.value == "compare"
        assert Action.QUERY.value == "query"


# --- apply_action ---


class TestApplyAction:
    def test_init(self):
        s = apply_action(Action.INIT, {"entity": "x", "value": 10}, State())
        assert s.get("x") == Decimal(10)

    def test_add(self):
        s = State().set("x", Decimal(5))
        s2 = apply_action(Action.ADD, {"entity": "x", "amount": 3}, s)
        assert s2.get("x") == Decimal(8)

    def test_subtract(self):
        s = State().set("x", Decimal(10))
        s2 = apply_action(Action.SUBTRACT, {"entity": "x", "amount": 4}, s)
        assert s2.get("x") == Decimal(6)

    def test_multiply(self):
        s = State().set("x", Decimal(5))
        s2 = apply_action(Action.MULTIPLY, {"entity": "x", "factor": 3}, s)
        assert s2.get("x") == Decimal(15)

    def test_divide(self):
        s = State().set("x", Decimal(10))
        s2 = apply_action(Action.DIVIDE, {"entity": "x", "divisor": 4}, s)
        assert s2.get("x") == Decimal("2.5000")

    def test_transfer(self):
        s = State().set("alice", Decimal(10)).set("bob", Decimal(5))
        s2 = apply_action(Action.TRANSFER, {"from": "alice", "to": "bob", "amount": 3}, s)
        assert s2.get("alice") == Decimal(7)
        assert s2.get("bob") == Decimal(8)

    def test_compare(self):
        s = State().set("tom", Decimal(15)).set("jane", Decimal(5))
        s2 = apply_action(
            Action.COMPARE, {"entity_a": "tom", "entity_b": "jane", "result": "diff"}, s
        )
        assert s2.get("diff") == Decimal(10)

    def test_compare_default_result(self):
        s = State().set("a", Decimal(10)).set("b", Decimal(3))
        s2 = apply_action(Action.COMPARE, {"entity_a": "a", "entity_b": "b"}, s)
        assert s2.get("_comparison") == Decimal(7)

    def test_query(self):
        s = State().set("x", Decimal(5))
        s2 = apply_action(Action.QUERY, {"entity": "x"}, s)
        assert s2 == s  # Query doesn't change state

    def test_unknown_action(self):
        import pytest

        with pytest.raises(ValueError, match="Unknown action"):
            apply_action("bogus", {}, State())


# --- Step ---


class TestStep:
    def test_verify_valid(self):
        s_before = State()
        s_after = State().set("x", Decimal(10))
        step = Step(
            action=Action.INIT,
            params={"entity": "x", "value": 10},
            state_before=s_before,
            state_after=s_after,
        )
        assert step.verify()

    def test_verify_invalid(self):
        s_before = State()
        s_after = State().set("x", Decimal(99))  # Wrong!
        step = Step(
            action=Action.INIT,
            params={"entity": "x", "value": 10},
            state_before=s_before,
            state_after=s_after,
        )
        assert not step.verify()

    def test_to_dict(self):
        s_before = State()
        s_after = State().set("x", Decimal(5))
        step = Step(
            action=Action.INIT,
            params={"entity": "x", "value": 5},
            state_before=s_before,
            state_after=s_after,
        )
        d = step.to_dict()
        assert d["action"] == "init"
        assert d["params"] == {"entity": "x", "value": 5}
        assert d["state_before"] == {}
        assert d["state_after"] == {"x": 5.0}

    def test_from_dict(self):
        d = {
            "action": "add",
            "params": {"entity": "x", "amount": 3},
            "state_before": {"x": 5.0},
            "state_after": {"x": 8.0},
        }
        step = Step.from_dict(d)
        assert step.action == Action.ADD
        assert step.state_before.get("x") == Decimal("5.0")
        assert step.state_after.get("x") == Decimal("8.0")


# --- TraceBuilder ---


class TestTraceBuilder:
    def test_init_and_query(self):
        trace = TraceBuilder("test").init("x", 10).query("x").build()
        assert trace.answer == Decimal(10)
        assert trace.is_valid()

    def test_add(self):
        trace = TraceBuilder().init("x", 5).add("x", 3).query("x").build()
        assert trace.answer == Decimal(8)
        assert trace.is_valid()

    def test_subtract(self):
        trace = TraceBuilder().init("x", 10).subtract("x", 3).query("x").build()
        assert trace.answer == Decimal(7)
        assert trace.is_valid()

    def test_multiply(self):
        trace = TraceBuilder().init("x", 4).multiply("x", 3).query("x").build()
        assert trace.answer == Decimal(12)
        assert trace.is_valid()

    def test_divide(self):
        trace = TraceBuilder().init("x", 10).divide("x", 4).query("x").build()
        assert trace.answer == Decimal("2.5000")
        assert trace.is_valid()

    def test_transfer(self):
        trace = (
            TraceBuilder()
            .init("alice", 10)
            .init("bob", 5)
            .transfer("alice", "bob", 3)
            .query("bob")
            .build()
        )
        assert trace.answer == Decimal(8)
        assert trace.is_valid()

    def test_compare(self):
        trace = (
            TraceBuilder()
            .init("tom", 15)
            .init("jane", 5)
            .compare("tom", "jane", "diff")
            .query("diff")
            .build()
        )
        assert trace.answer == Decimal(10)
        assert trace.is_valid()

    def test_problem_type(self):
        trace = TraceBuilder("entity_tracking").init("x", 5).query("x").build()
        assert trace.problem_type == "entity_tracking"

    def test_no_query_no_answer(self):
        trace = TraceBuilder().init("x", 5).build()
        assert trace.answer is None

    def test_chaining(self):
        builder = TraceBuilder()
        result = builder.init("x", 1).add("x", 2).subtract("x", 1)
        assert result is builder  # Methods return self


# --- Trace ---


class TestTrace:
    def test_empty_invalid(self):
        trace = Trace()
        assert not trace.is_valid()

    def test_valid_trace(self):
        trace = TraceBuilder().init("x", 5).add("x", 3).query("x").build()
        assert trace.is_valid()
        assert trace.answer == Decimal(8)

    def test_invalid_step(self):
        # Manually create a trace with wrong state_after
        s0 = State()
        s1 = State().set("x", Decimal(99))  # Wrong - should be 5
        step = Step(
            action=Action.INIT, params={"entity": "x", "value": 5}, state_before=s0, state_after=s1
        )
        trace = Trace(steps=[step])
        assert not trace.is_valid()

    def test_broken_chain(self):
        # Two steps where states don't connect
        s0 = State()
        s1 = State().set("x", Decimal(5))
        step1 = Step(
            action=Action.INIT, params={"entity": "x", "value": 5}, state_before=s0, state_after=s1
        )

        s2 = State().set("x", Decimal(99))  # Doesn't match s1
        s3 = State().set("x", Decimal(102))
        step2 = Step(
            action=Action.ADD, params={"entity": "x", "amount": 3}, state_before=s2, state_after=s3
        )

        trace = Trace(steps=[step1, step2])
        assert not trace.is_valid()

    def test_answer_mismatch(self):
        trace = TraceBuilder().init("x", 5).query("x").build()
        trace.answer = Decimal(99)  # Override with wrong answer
        assert not trace.is_valid()

    def test_replay_valid(self):
        trace = TraceBuilder().init("x", 5).add("x", 3).query("x").build()
        success, final_state, failed_idx = trace.replay()
        assert success
        assert final_state.get("x") == Decimal(8)
        assert failed_idx is None

    def test_replay_broken_chain(self):
        # Create trace with broken chain
        s0 = State()
        s1 = State().set("x", Decimal(5))
        step1 = Step(
            action=Action.INIT, params={"entity": "x", "value": 5}, state_before=s0, state_after=s1
        )

        s2 = State().set("x", Decimal(99))  # Doesn't match s1
        s3 = State().set("x", Decimal(102))
        step2 = Step(
            action=Action.ADD, params={"entity": "x", "amount": 3}, state_before=s2, state_after=s3
        )

        trace = Trace(steps=[step1, step2])
        success, state, failed_idx = trace.replay()
        assert not success
        assert failed_idx == 1

    def test_replay_invalid_step(self):
        s0 = State()
        s1 = State().set("x", Decimal(99))  # Wrong
        step = Step(
            action=Action.INIT, params={"entity": "x", "value": 5}, state_before=s0, state_after=s1
        )
        trace = Trace(steps=[step])
        success, state, failed_idx = trace.replay()
        assert not success
        assert failed_idx == 0

    def test_to_dict(self):
        trace = TraceBuilder().init("x", 5).query("x").build()
        d = trace.to_dict()
        assert d["answer"] == 5.0
        assert d["problem_type"] == "unknown"
        assert len(d["steps"]) == 2

    def test_to_dict_no_answer(self):
        trace = Trace(steps=[], answer=None)
        d = trace.to_dict()
        assert d["answer"] is None

    def test_from_dict(self):
        trace = TraceBuilder().init("x", 10).add("x", 5).query("x").build()
        d = trace.to_dict()
        trace2 = Trace.from_dict(d)
        assert trace2.answer == Decimal("15.0")
        assert trace2.problem_type == "unknown"
        assert len(trace2.steps) == 3

    def test_from_dict_no_answer(self):
        trace = Trace.from_dict({"steps": [], "problem_type": "test"})
        assert trace.answer is None

    def test_to_yaml_str(self):
        trace = TraceBuilder().init("x", 5).add("x", 3).query("x").build()
        yaml = trace.to_yaml_str()
        assert "init" in yaml
        assert "add" in yaml
        assert "query" in yaml
        assert "answer: 8" in yaml


# --- TraceVerifier ---


class TestTraceVerifier:
    def setup_method(self):
        self.verifier = TraceVerifier()

    def test_valid_trace(self):
        trace = TraceBuilder().init("x", 5).add("x", 3).query("x").build()
        result = self.verifier.verify(trace)
        assert result.is_valid
        assert result.status == VerificationStatus.VALID
        assert result.computed_answer == Decimal(8)
        assert result.expected_answer == Decimal(8)

    def test_empty_trace(self):
        trace = Trace()
        result = self.verifier.verify(trace)
        assert not result.is_valid
        assert result.status == VerificationStatus.EMPTY_TRACE

    def test_invalid_step(self):
        s0 = State()
        s1 = State().set("x", Decimal(99))  # Wrong
        step = Step(
            action=Action.INIT, params={"entity": "x", "value": 5}, state_before=s0, state_after=s1
        )
        s2 = s1.copy()
        step2 = Step(
            action=Action.QUERY,
            params={"entity": "x", "result": 99},
            state_before=s2,
            state_after=s2,
        )
        trace = Trace(steps=[step, step2], answer=Decimal(99))
        result = self.verifier.verify(trace)
        assert not result.is_valid
        assert result.status == VerificationStatus.INVALID_STEP

    def test_broken_chain(self):
        # Create valid steps with broken chain
        s0 = State()
        s1 = State().set("x", Decimal(5))
        step1 = Step(
            action=Action.INIT, params={"entity": "x", "value": 5}, state_before=s0, state_after=s1
        )

        # Second step has wrong state_before (doesn't match first step's state_after)
        s2 = State().set("x", Decimal(10))  # Wrong - should be 5
        s3 = State().set("x", Decimal(13))
        step2 = Step(
            action=Action.ADD, params={"entity": "x", "amount": 3}, state_before=s2, state_after=s3
        )

        trace = Trace(steps=[step1, step2])
        result = self.verifier.verify(trace)
        assert not result.is_valid
        assert result.status == VerificationStatus.BROKEN_CHAIN

    def test_missing_query(self):
        trace = TraceBuilder().init("x", 5).add("x", 3).build()
        # Remove the query step - trace just has init and add
        result = self.verifier.verify(trace)
        assert not result.is_valid
        assert result.status == VerificationStatus.MISSING_QUERY

    def test_wrong_answer(self):
        trace = TraceBuilder().init("x", 5).query("x").build()
        trace.answer = Decimal(99)  # Wrong answer
        result = self.verifier.verify(trace)
        assert not result.is_valid
        assert result.status == VerificationStatus.WRONG_ANSWER
        assert result.computed_answer == Decimal(5)
        assert result.expected_answer == Decimal(99)

    def test_verify_batch(self):
        t1 = TraceBuilder().init("x", 5).query("x").build()
        t2 = TraceBuilder().init("y", 10).add("y", 5).query("y").build()
        t3 = Trace()  # Invalid

        results = self.verifier.verify_batch([t1, t2, t3])
        assert results["total"] == 3
        assert results["valid"] == 2
        assert results["valid_rate"] == 2 / 3

    def test_verify_batch_empty(self):
        results = self.verifier.verify_batch([])
        assert results["total"] == 0
        assert results["valid_rate"] == 0


class TestVerificationResult:
    def test_answer_correct(self):
        r = VerificationResult(
            status=VerificationStatus.VALID,
            computed_answer=Decimal(5),
            expected_answer=Decimal(5),
        )
        assert r.answer_correct

    def test_answer_incorrect(self):
        r = VerificationResult(
            status=VerificationStatus.VALID,
            computed_answer=Decimal(5),
            expected_answer=Decimal(10),
        )
        assert not r.answer_correct

    def test_answer_none(self):
        r = VerificationResult(status=VerificationStatus.VALID)
        assert not r.answer_correct

    def test_to_dict(self):
        r = VerificationResult(
            status=VerificationStatus.VALID,
            final_state=State().set("x", Decimal(5)),
            computed_answer=Decimal(5),
            expected_answer=Decimal(5),
        )
        d = r.to_dict()
        assert d["status"] == "valid"
        assert d["is_valid"] is True
        assert d["answer_correct"] is True

    def test_to_dict_no_state(self):
        r = VerificationResult(status=VerificationStatus.EMPTY_TRACE)
        d = r.to_dict()
        assert d["final_state"] is None
        assert d["computed_answer"] is None

    def test_summary_valid(self):
        r = VerificationResult(
            status=VerificationStatus.VALID,
            computed_answer=Decimal(42),
        )
        assert "VALID" in r.summary()
        assert "42" in r.summary()

    def test_summary_invalid(self):
        r = VerificationResult(
            status=VerificationStatus.INVALID_STEP,
            errors=[
                StepError(
                    step_index=0,
                    step=Step(
                        action=Action.INIT, params={}, state_before=State(), state_after=State()
                    ),
                    expected_state=State(),
                    actual_state=State(),
                    message="Step 0 failed",
                )
            ],
        )
        assert "INVALID" in r.summary()


class TestStepError:
    def test_to_dict(self):
        err = StepError(
            step_index=1,
            step=Step(
                action=Action.ADD,
                params={"entity": "x", "amount": 5},
                state_before=State().set("x", Decimal(10)),
                state_after=State().set("x", Decimal(15)),
            ),
            expected_state=State().set("x", Decimal(15)),
            actual_state=State().set("x", Decimal(13)),
            message="Mismatch at step 1",
        )
        d = err.to_dict()
        assert d["step_index"] == 1
        assert d["action"] == "add"
        assert d["message"] == "Mismatch at step 1"


# --- Convenience functions ---


class TestConvenienceFunctions:
    def test_verify_trace(self):
        trace = TraceBuilder().init("x", 5).query("x").build()
        result = verify_trace(trace)
        assert result.is_valid

    def test_verify_traces(self):
        t1 = TraceBuilder().init("x", 5).query("x").build()
        t2 = TraceBuilder().init("y", 10).query("y").build()
        results = verify_traces([t1, t2])
        assert results["valid"] == 2


# --- EXAMPLE_SPECS ---


class TestExampleSpecs:
    def test_example_specs_exist(self):
        from chuk_virtual_expert_arithmetic.schema.problem import EXAMPLE_SPECS

        assert "entity_tracking" in EXAMPLE_SPECS
        assert "arithmetic_chain" in EXAMPLE_SPECS
        assert "comparison" in EXAMPLE_SPECS
        assert "allocation" in EXAMPLE_SPECS
        assert "percentage" in EXAMPLE_SPECS

    def test_entity_tracking_spec(self):
        from chuk_virtual_expert_arithmetic.schema.problem import EXAMPLE_SPECS

        spec = EXAMPLE_SPECS["entity_tracking"]
        assert spec.problem_type == ProblemType.ENTITY_TRACKING
        assert len(spec.entities) == 2
        assert spec.entities[0].name == "jenny"
        assert spec.is_valid()

    def test_all_specs_valid(self):
        from chuk_virtual_expert_arithmetic.schema.problem import EXAMPLE_SPECS

        for name, spec in EXAMPLE_SPECS.items():
            assert spec.is_valid(), f"Spec {name} is not valid"

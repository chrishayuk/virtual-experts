"""Tests for the trace_generators module."""

from __future__ import annotations

from decimal import Decimal

from chuk_virtual_expert_arithmetic.schema.problem import (
    Constraint,
    Entity,
    Operation,
    OperationType,
    ProblemSpec,
    ProblemType,
    Query,
)
from chuk_virtual_expert_arithmetic.schema.trace import Trace
from chuk_virtual_expert_arithmetic.schema.verifier import verify_trace
from chuk_virtual_expert_arithmetic.trace_generators import (
    AllocationTraceGenerator,
    ArithmeticTraceGenerator,
    ComparisonTraceGenerator,
    EntityTraceGenerator,
    generate_trace,
    get_generator_for_type,
    route_to_generator,
    supported_problem_types,
)

# --- TraceGenerator base class ---


class TestTraceGeneratorBase:
    def test_can_handle_matching(self):
        gen = EntityTraceGenerator()
        spec = ProblemSpec(problem_type=ProblemType.ENTITY_TRACKING)
        assert gen.can_handle(spec)

    def test_can_handle_non_matching(self):
        gen = EntityTraceGenerator()
        spec = ProblemSpec(problem_type=ProblemType.COMPARISON)
        assert not gen.can_handle(spec)


# --- EntityTraceGenerator ---


class TestEntityTraceGenerator:
    def setup_method(self):
        self.gen = EntityTraceGenerator()

    def test_supported_types(self):
        assert ProblemType.ENTITY_TRACKING in self.gen.supported_types

    def test_simple_init_and_query(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ENTITY_TRACKING,
            entities=[Entity(name="alice", initial_value=Decimal(10))],
            query=Query(target="alice"),
        )
        trace = self.gen.generate(spec)
        assert isinstance(trace, Trace)
        assert trace.is_valid()
        assert trace.answer == Decimal(10)

    def test_add_operation(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ENTITY_TRACKING,
            entities=[Entity(name="x", initial_value=Decimal(5))],
            operations=[Operation(type=OperationType.ADD, target="x", amount=Decimal(3))],
            query=Query(target="x"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(8)

    def test_subtract_operation(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ENTITY_TRACKING,
            entities=[Entity(name="marbles", initial_value=Decimal(20))],
            operations=[
                Operation(type=OperationType.SUBTRACT, target="marbles", amount=Decimal(7))
            ],
            query=Query(target="marbles"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(13)

    def test_transfer_operation(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ENTITY_TRACKING,
            entities=[
                Entity(name="alice", initial_value=Decimal(10)),
                Entity(name="bob", initial_value=Decimal(3)),
            ],
            operations=[
                Operation(
                    type=OperationType.TRANSFER, source="alice", target="bob", amount=Decimal(4)
                ),
            ],
            query=Query(target="bob"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(7)

    def test_multiply_operation(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ENTITY_TRACKING,
            entities=[Entity(name="x", initial_value=Decimal(5))],
            operations=[Operation(type=OperationType.MULTIPLY, target="x", factor=Decimal(3))],
            query=Query(target="x"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(15)

    def test_divide_operation(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ENTITY_TRACKING,
            entities=[Entity(name="x", initial_value=Decimal(10))],
            operations=[Operation(type=OperationType.DIVIDE, target="x", factor=Decimal(2))],
            query=Query(target="x"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal("5.0000")

    def test_entity_no_initial_value(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ENTITY_TRACKING,
            entities=[Entity(name="x")],
            operations=[Operation(type=OperationType.ADD, target="x", amount=Decimal(5))],
            query=Query(target="x"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(5)

    def test_no_query(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ENTITY_TRACKING,
            entities=[Entity(name="x", initial_value=Decimal(5))],
        )
        trace = self.gen.generate(spec)
        assert trace.answer is None

    def test_multiple_operations(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ENTITY_TRACKING,
            entities=[
                Entity(name="jenny", initial_value=Decimal(10)),
                Entity(name="bob", initial_value=Decimal(0)),
            ],
            operations=[
                Operation(
                    type=OperationType.TRANSFER, source="jenny", target="bob", amount=Decimal(3)
                ),
                Operation(type=OperationType.ADD, target="jenny", amount=Decimal(2)),
            ],
            query=Query(target="jenny"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(9)  # 10 - 3 + 2

    def test_skip_none_amounts(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ENTITY_TRACKING,
            entities=[Entity(name="x", initial_value=Decimal(5))],
            operations=[
                Operation(type=OperationType.ADD, target="x", amount=None),
                Operation(type=OperationType.SUBTRACT, target="x", amount=None),
                Operation(type=OperationType.TRANSFER, source="x", target="y", amount=None),
                Operation(type=OperationType.MULTIPLY, target="x", factor=None),
                Operation(type=OperationType.DIVIDE, target="x", factor=None),
            ],
            query=Query(target="x"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(5)  # No changes applied


# --- ArithmeticTraceGenerator ---


class TestArithmeticTraceGenerator:
    def setup_method(self):
        self.gen = ArithmeticTraceGenerator()

    def test_supported_types(self):
        assert ProblemType.ARITHMETIC_CHAIN in self.gen.supported_types
        assert ProblemType.PERCENTAGE in self.gen.supported_types

    def test_simple_add(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ARITHMETIC_CHAIN,
            entities=[Entity(name="x", initial_value=Decimal(10))],
            operations=[Operation(type=OperationType.ADD, target="x", amount=Decimal(5))],
            query=Query(target="x"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(15)

    def test_subtract(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ARITHMETIC_CHAIN,
            entities=[Entity(name="val", initial_value=Decimal(20))],
            operations=[Operation(type=OperationType.SUBTRACT, target="val", amount=Decimal(8))],
            query=Query(target="val"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(12)

    def test_multiply_with_factor(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ARITHMETIC_CHAIN,
            entities=[Entity(name="price", initial_value=Decimal(50))],
            operations=[Operation(type=OperationType.MULTIPLY, target="price", factor=Decimal(2))],
            query=Query(target="price"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(100)

    def test_multiply_with_amount(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ARITHMETIC_CHAIN,
            entities=[Entity(name="x", initial_value=Decimal(5))],
            operations=[Operation(type=OperationType.MULTIPLY, target="x", amount=Decimal(3))],
            query=Query(target="x"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(15)

    def test_divide_with_factor(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ARITHMETIC_CHAIN,
            entities=[Entity(name="total", initial_value=Decimal(100))],
            operations=[Operation(type=OperationType.DIVIDE, target="total", factor=Decimal(4))],
            query=Query(target="total"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal("25.0000")

    def test_divide_with_amount(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ARITHMETIC_CHAIN,
            entities=[Entity(name="x", initial_value=Decimal(20))],
            operations=[Operation(type=OperationType.DIVIDE, target="x", amount=Decimal(5))],
            query=Query(target="x"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal("4.0000")

    def test_no_entities(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ARITHMETIC_CHAIN,
            operations=[Operation(type=OperationType.ADD, target="result", amount=Decimal(7))],
            query=Query(target="result"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(7)

    def test_no_initial_value(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ARITHMETIC_CHAIN,
            entities=[Entity(name="x")],
            operations=[Operation(type=OperationType.ADD, target="x", amount=Decimal(5))],
            query=Query(target="x"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(5)

    def test_chain_operations(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ARITHMETIC_CHAIN,
            entities=[Entity(name="val", initial_value=Decimal(10))],
            operations=[
                Operation(type=OperationType.ADD, target="val", amount=Decimal(5)),
                Operation(type=OperationType.MULTIPLY, target="val", factor=Decimal(2)),
                Operation(type=OperationType.SUBTRACT, target="val", amount=Decimal(3)),
            ],
            query=Query(target="val"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(27)  # (10 + 5) * 2 - 3

    def test_skip_none_values(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ARITHMETIC_CHAIN,
            entities=[Entity(name="x", initial_value=Decimal(10))],
            operations=[
                Operation(type=OperationType.ADD, target="x", amount=None),
                Operation(type=OperationType.SUBTRACT, target="x", amount=None),
                Operation(type=OperationType.MULTIPLY, target="x"),
                Operation(type=OperationType.DIVIDE, target="x"),
            ],
            query=Query(target="x"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(10)

    def test_no_query(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ARITHMETIC_CHAIN,
            entities=[Entity(name="x", initial_value=Decimal(5))],
        )
        trace = self.gen.generate(spec)
        # When no query, it queries main_var
        assert trace.answer == Decimal(5)


# --- ComparisonTraceGenerator ---


class TestComparisonTraceGenerator:
    def setup_method(self):
        self.gen = ComparisonTraceGenerator()

    def test_supported_types(self):
        assert ProblemType.COMPARISON in self.gen.supported_types

    def test_simple_comparison(self):
        spec = ProblemSpec(
            problem_type=ProblemType.COMPARISON,
            entities=[
                Entity(name="tom", initial_value=Decimal(15)),
                Entity(name="jane", initial_value=Decimal(5)),
            ],
            query=Query(target="difference", question="compare", compare_a="tom", compare_b="jane"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(10)

    def test_with_multiply_operation(self):
        spec = ProblemSpec(
            problem_type=ProblemType.COMPARISON,
            entities=[
                Entity(name="alice", initial_value=Decimal(5)),
                Entity(name="bob", initial_value=Decimal(5)),
            ],
            operations=[
                Operation(type=OperationType.MULTIPLY, target="alice", factor=Decimal(3)),
            ],
            query=Query(
                target="difference", question="compare", compare_a="alice", compare_b="bob"
            ),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(10)  # 15 - 5

    def test_with_add_operation(self):
        spec = ProblemSpec(
            problem_type=ProblemType.COMPARISON,
            entities=[
                Entity(name="x", initial_value=Decimal(10)),
                Entity(name="y", initial_value=Decimal(5)),
            ],
            operations=[
                Operation(type=OperationType.ADD, target="x", amount=Decimal(5)),
            ],
            query=Query(target="difference", question="compare", compare_a="x", compare_b="y"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(10)  # 15 - 5

    def test_non_compare_query(self):
        spec = ProblemSpec(
            problem_type=ProblemType.COMPARISON,
            entities=[
                Entity(name="x", initial_value=Decimal(10)),
            ],
            query=Query(target="x", question="value"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(10)

    def test_compare_without_entities(self):
        spec = ProblemSpec(
            problem_type=ProblemType.COMPARISON,
            entities=[
                Entity(name="x", initial_value=Decimal(10)),
            ],
            query=Query(target="x", question="compare"),  # No compare_a/compare_b
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(10)

    def test_entity_without_initial_value(self):
        spec = ProblemSpec(
            problem_type=ProblemType.COMPARISON,
            entities=[
                Entity(name="x", initial_value=Decimal(10)),
                Entity(name="y"),  # No initial value - skipped
            ],
            query=Query(target="x"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()


# --- AllocationTraceGenerator ---


class TestAllocationTraceGenerator:
    def setup_method(self):
        self.gen = AllocationTraceGenerator()

    def test_supported_types(self):
        assert ProblemType.ALLOCATION in self.gen.supported_types
        assert ProblemType.RATE_EQUATION in self.gen.supported_types

    def test_sum_and_ratio(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ALLOCATION,
            entities=[
                Entity(name="alice"),
                Entity(name="bob"),
            ],
            constraints=[
                Constraint(type="sum", entities=["alice", "bob"], value=Decimal(100)),
                Constraint(type="ratio", entities=["alice", "bob"], factor=Decimal(2)),
            ],
            query=Query(target="alice"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer is not None

    def test_sum_and_difference(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ALLOCATION,
            entities=[
                Entity(name="a"),
                Entity(name="b"),
            ],
            constraints=[
                Constraint(type="sum", entities=["a", "b"], value=Decimal(30)),
                Constraint(type="difference", entities=["a", "b"], value=Decimal(10)),
            ],
            query=Query(target="a"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(20)  # (30 + 10) / 2

    def test_no_constraints(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ALLOCATION,
            entities=[
                Entity(name="x", initial_value=Decimal(42)),
            ],
            query=Query(target="x"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        assert trace.answer == Decimal(42)

    def test_ratio_with_different_entity_order(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ALLOCATION,
            entities=[
                Entity(name="alice"),
                Entity(name="bob"),
            ],
            constraints=[
                Constraint(type="sum", entities=["alice", "bob"], value=Decimal(90)),
                Constraint(type="ratio", entities=["bob", "alice"], factor=Decimal(2)),
            ],
            query=Query(target="bob"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        # bob = 2 * alice, bob + alice = 90
        # 2A + A = 90, A = 30, bob = 60
        assert trace.answer == Decimal(60)

    def test_ratio_without_entities_in_ratio_constraint(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ALLOCATION,
            entities=[
                Entity(name="x"),
                Entity(name="y"),
            ],
            constraints=[
                Constraint(type="sum", entities=["x", "y"], value=Decimal(60)),
                Constraint(type="ratio", factor=Decimal(2)),  # No entities in ratio constraint
            ],
            query=Query(target="x"),
        )
        trace = self.gen.generate(spec)
        assert trace.is_valid()
        # Falls back to using sum_constraint entities: x=larger, y=smaller
        # y = 60/(2+1) = 20, x = 40
        assert trace.answer == Decimal(40)

    def test_no_query(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ALLOCATION,
            entities=[Entity(name="x", initial_value=Decimal(5))],
        )
        trace = self.gen.generate(spec)
        assert trace.answer is None

    def test_sum_with_none_values(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ALLOCATION,
            entities=[Entity(name="a"), Entity(name="b")],
            constraints=[
                Constraint(type="sum", entities=["a", "b"]),  # No value
                Constraint(type="ratio", entities=["a", "b"]),  # No factor
            ],
            query=Query(target="a"),
        )
        trace = self.gen.generate(spec)
        # Uses defaults: total=0, ratio=1
        assert trace.is_valid()

    def test_single_entity_sum(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ALLOCATION,
            entities=[Entity(name="x")],
            constraints=[
                Constraint(type="sum", entities=["x"], value=Decimal(100)),
                Constraint(type="ratio", entities=["x"], factor=Decimal(2)),
            ],
            query=Query(target="x"),
        )
        trace = self.gen.generate(spec)
        # Fewer than 2 entities in sum, so ratio branch not entered
        # Falls through to init from entities
        assert trace is not None


# --- Router ---


class TestRouter:
    def test_route_entity_tracking(self):
        spec = ProblemSpec(problem_type=ProblemType.ENTITY_TRACKING)
        gen = route_to_generator(spec)
        assert isinstance(gen, EntityTraceGenerator)

    def test_route_arithmetic_chain(self):
        spec = ProblemSpec(problem_type=ProblemType.ARITHMETIC_CHAIN)
        gen = route_to_generator(spec)
        assert isinstance(gen, ArithmeticTraceGenerator)

    def test_route_percentage(self):
        spec = ProblemSpec(problem_type=ProblemType.PERCENTAGE)
        gen = route_to_generator(spec)
        assert isinstance(gen, ArithmeticTraceGenerator)

    def test_route_comparison(self):
        spec = ProblemSpec(problem_type=ProblemType.COMPARISON)
        gen = route_to_generator(spec)
        assert isinstance(gen, ComparisonTraceGenerator)

    def test_route_allocation(self):
        spec = ProblemSpec(problem_type=ProblemType.ALLOCATION)
        gen = route_to_generator(spec)
        assert isinstance(gen, AllocationTraceGenerator)

    def test_route_rate_equation(self):
        spec = ProblemSpec(problem_type=ProblemType.RATE_EQUATION)
        gen = route_to_generator(spec)
        assert isinstance(gen, AllocationTraceGenerator)

    def test_route_unknown(self):
        spec = ProblemSpec(problem_type=ProblemType.UNKNOWN)
        gen = route_to_generator(spec)
        assert gen is None

    def test_generate_trace(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ENTITY_TRACKING,
            entities=[Entity(name="x", initial_value=Decimal(5))],
            query=Query(target="x"),
        )
        trace = generate_trace(spec)
        assert trace is not None
        assert trace.is_valid()

    def test_generate_trace_unknown(self):
        spec = ProblemSpec(problem_type=ProblemType.UNKNOWN)
        trace = generate_trace(spec)
        assert trace is None

    def test_get_generator_for_type(self):
        gen = get_generator_for_type(ProblemType.ENTITY_TRACKING)
        assert isinstance(gen, EntityTraceGenerator)

    def test_get_generator_for_type_unknown(self):
        gen = get_generator_for_type(ProblemType.UNKNOWN)
        assert gen is None

    def test_supported_problem_types(self):
        types = supported_problem_types()
        assert ProblemType.ENTITY_TRACKING in types
        assert ProblemType.ARITHMETIC_CHAIN in types
        assert ProblemType.COMPARISON in types
        assert ProblemType.ALLOCATION in types
        assert ProblemType.PERCENTAGE in types
        assert ProblemType.RATE_EQUATION in types
        assert ProblemType.UNKNOWN not in types


# --- Integration: generated traces verify ---


class TestTraceVerification:
    def test_entity_trace_verifies(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ENTITY_TRACKING,
            entities=[
                Entity(name="jenny", initial_value=Decimal(5)),
                Entity(name="bob", initial_value=Decimal(0)),
            ],
            operations=[
                Operation(
                    type=OperationType.TRANSFER, source="jenny", target="bob", amount=Decimal(2)
                ),
            ],
            query=Query(target="jenny"),
        )
        trace = generate_trace(spec)
        result = verify_trace(trace)
        assert result.is_valid
        assert result.computed_answer == Decimal(3)

    def test_arithmetic_trace_verifies(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ARITHMETIC_CHAIN,
            entities=[Entity(name="sam", initial_value=Decimal(10))],
            operations=[
                Operation(type=OperationType.SUBTRACT, target="sam", amount=Decimal(3)),
                Operation(type=OperationType.ADD, target="sam", amount=Decimal(5)),
            ],
            query=Query(target="sam"),
        )
        trace = generate_trace(spec)
        result = verify_trace(trace)
        assert result.is_valid
        assert result.computed_answer == Decimal(12)

    def test_comparison_trace_verifies(self):
        spec = ProblemSpec(
            problem_type=ProblemType.COMPARISON,
            entities=[
                Entity(name="tom", initial_value=Decimal(15)),
                Entity(name="jane", initial_value=Decimal(5)),
            ],
            query=Query(target="difference", question="compare", compare_a="tom", compare_b="jane"),
        )
        trace = generate_trace(spec)
        result = verify_trace(trace)
        assert result.is_valid
        assert result.computed_answer == Decimal(10)

    def test_allocation_trace_verifies(self):
        spec = ProblemSpec(
            problem_type=ProblemType.ALLOCATION,
            entities=[Entity(name="alice"), Entity(name="bob")],
            constraints=[
                Constraint(type="sum", entities=["alice", "bob"], value=Decimal(100)),
                Constraint(type="difference", entities=["alice", "bob"], value=Decimal(20)),
            ],
            query=Query(target="alice"),
        )
        trace = generate_trace(spec)
        result = verify_trace(trace)
        assert result.is_valid
        assert result.computed_answer == Decimal(60)

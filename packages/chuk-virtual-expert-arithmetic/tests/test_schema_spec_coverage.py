"""Additional tests for SchemaSpec - comprehensive coverage."""

from __future__ import annotations

from chuk_virtual_expert_arithmetic.models.schema_spec import (
    SchemaSpec,
    TraceOp,
    VariableSpec,
    VocabSpec,
)
from chuk_virtual_expert_arithmetic.types import ComputeOpType, TraceOpType


class TestVariableSpecAdvanced:
    """Advanced tests for VariableSpec model."""

    def test_all_constraint_options(self) -> None:
        """Test all constraint options."""
        spec = VariableSpec(
            type="int",
            min=1,
            max=100,
            multiple_of=5,
            avoid_round=True,
            requires_carrying=True,
            requires_borrowing=True,
            difficulty="hard",
        )
        assert spec.avoid_round is True
        assert spec.requires_carrying is True
        assert spec.requires_borrowing is True
        assert spec.difficulty == "hard"

    def test_variable_with_values(self) -> None:
        """Test choice variable with values attribute."""
        spec = VariableSpec(type="choice", values=["a", "b", "c"])
        assert spec.values == ["a", "b", "c"]

    def test_variable_with_options(self) -> None:
        """Test choice variable with options attribute."""
        spec = VariableSpec(type="choice", options=[1, 2, 3])
        assert spec.options == [1, 2, 3]

    def test_bool_type(self) -> None:
        """Test boolean type variable."""
        spec = VariableSpec(type="bool")
        assert spec.type == "bool"


class TestVocabSpecAdvanced:
    """Advanced tests for VocabSpec model."""

    def test_distinct_from(self) -> None:
        """Test distinct_from for avoiding duplicates."""
        spec = VocabSpec(
            path="items.countable_singular",
            distinct_from=["item1", "item2"],
        )
        assert spec.distinct_from == ["item1", "item2"]

    def test_sample_count(self) -> None:
        """Test sample count for multiple items."""
        spec = VocabSpec(path="items.countable_singular", sample=5)
        assert spec.sample == 5

    def test_domain_context_type(self) -> None:
        """Test domain_context type."""
        spec = VocabSpec(type="domain_context")
        assert spec.type == "domain_context"


class TestTraceOpAdvanced:
    """Advanced tests for TraceOp model."""

    def test_init_with_numeric_value(self) -> None:
        """Test init op with numeric value."""
        op = TraceOp(op="init", var="x", value=42)
        assert op.value == 42

    def test_compute_with_enum(self) -> None:
        """Test compute op with enum types."""
        op = TraceOp(
            op=TraceOpType.COMPUTE,
            compute_op=ComputeOpType.ADD,
            args=["a", "b"],
            var="result",
        )
        assert op.is_compute()

    def test_is_compute_string(self) -> None:
        """Test is_compute with string op."""
        op = TraceOp(op="compute", compute_op="add", args=["a", "b"], var="x")
        assert op.is_compute() is True

    def test_is_not_compute(self) -> None:
        """Test is_compute returns False for other ops."""
        op = TraceOp(op="init", var="x", value=1)
        assert op.is_compute() is False

    def test_add_entity_op(self) -> None:
        """Test add_entity operation."""
        op = TraceOp(op="add_entity", entity="Alice", amount=10)
        assert op.op == "add_entity"
        assert op.entity == "Alice"
        assert op.amount == 10

    def test_percent_increase_op(self) -> None:
        """Test percent_increase operation."""
        op = TraceOp(op="percent_increase", base="price", rate=20, var="result")
        assert op.op == "percent_increase"
        assert op.base == "price"
        assert op.rate == 20

    def test_percent_of_op(self) -> None:
        """Test percent_of operation."""
        op = TraceOp(op="percent_of", value=100, rate=15, var="result")
        assert op.op == "percent_of"
        assert op.value == 100
        assert op.rate == 15


class TestSchemaSpecAdvanced:
    """Advanced tests for SchemaSpec model."""

    def test_get_required_template_vars_empty(self) -> None:
        """Test get_required_template_vars with empty schema."""
        schema = SchemaSpec(name="test", answer="x")
        vars = schema.get_required_template_vars()
        # Empty schema has no template_vars or variables
        assert vars == set()

    def test_get_required_template_vars_with_variables(self) -> None:
        """Test get_required_template_vars extracts variable names."""
        schema = SchemaSpec(
            name="test",
            variables={
                "a": VariableSpec(type="int", min=1, max=10),
                "b": VariableSpec(type="int", min=1, max=10),
            },
            answer="x",
        )
        vars = schema.get_required_template_vars()
        assert "a" in vars
        assert "b" in vars

    def test_get_required_template_vars_with_template_vars(self) -> None:
        """Test get_required_template_vars extracts template_vars keys."""
        schema = SchemaSpec(
            name="test",
            template_vars={
                "name": "person.name",
                "item": "item",
            },
            answer="x",
        )
        vars = schema.get_required_template_vars()
        assert "name" in vars
        assert "item" in vars

    def test_estimate_trace_depth_empty(self) -> None:
        """Test estimate_trace_depth with no trace."""
        schema = SchemaSpec(name="test", answer="x", trace=[])
        depth = schema.estimate_trace_depth()
        assert depth == 0

    def test_estimate_trace_depth_no_compute(self) -> None:
        """Test estimate_trace_depth with only init ops."""
        schema = SchemaSpec(
            name="test",
            answer="x",
            trace=[
                TraceOp(op="init", var="x", value=1),
                TraceOp(op="init", var="y", value=2),
                TraceOp(op="query", var="x"),
            ],
        )
        depth = schema.estimate_trace_depth()
        assert depth == 0

    def test_estimate_trace_depth_multiple_compute(self) -> None:
        """Test estimate_trace_depth with multiple compute ops."""
        schema = SchemaSpec(
            name="test",
            answer="result",
            trace=[
                TraceOp(op="init", var="a", value=1),
                TraceOp(op="init", var="b", value=2),
                TraceOp(op="compute", compute_op="add", args=["a", "b"], var="c"),
                TraceOp(op="compute", compute_op="mul", args=["c", 3], var="d"),
                TraceOp(op="compute", compute_op="sub", args=["d", 5], var="result"),
                TraceOp(op="query", var="result"),
            ],
        )
        depth = schema.estimate_trace_depth()
        assert depth == 3

    def test_gsm8k_style(self) -> None:
        """Test gsm8k_style field."""
        schema = SchemaSpec(name="test", answer="x", gsm8k_style=True)
        assert schema.gsm8k_style is True

    def test_extra_fields_allowed(self) -> None:
        """Test that extra fields are allowed."""
        schema = SchemaSpec(
            name="test",
            answer="x",
            custom_field="custom_value",
        )
        assert schema.custom_field == "custom_value"

    def test_model_dump(self) -> None:
        """Test serialization to dict."""
        schema = SchemaSpec(
            name="test",
            expert="arithmetic",
            answer="x",
            variables={"a": VariableSpec(type="int", min=1, max=10)},
        )
        data = schema.model_dump()

        assert data["name"] == "test"
        assert data["expert"] == "arithmetic"
        assert "variables" in data
        assert "a" in data["variables"]


class TestTraceOpFromDict:
    """Test creating TraceOp from dict (JSON-like data)."""

    def test_from_dict_init(self) -> None:
        """Test creating init op from dict."""
        data = {"op": "init", "var": "x", "value": "count"}
        op = TraceOp(**data)
        assert op.op == "init"
        assert op.var == "x"
        assert op.value == "count"

    def test_from_dict_compute(self) -> None:
        """Test creating compute op from dict."""
        data = {"op": "compute", "compute_op": "mul", "args": ["a", "b"], "var": "result"}
        op = TraceOp(**data)
        assert op.op == "compute"
        assert op.compute_op == "mul"
        assert op.args == ["a", "b"]

    def test_from_dict_transfer(self) -> None:
        """Test creating transfer op from dict."""
        data = {"op": "transfer", "from_entity": "Alice", "to_entity": "Bob", "amount": 5}
        op = TraceOp(**data)
        assert op.op == "transfer"
        assert op.from_entity == "Alice"
        assert op.to_entity == "Bob"


class TestSchemaSpecFromComplexDict:
    """Test creating SchemaSpec from complex dict structures."""

    def test_full_schema_from_dict(self) -> None:
        """Test creating full schema from dict."""
        data = {
            "name": "complex_schema",
            "description": "A complex test schema",
            "pattern": "test_pattern",
            "variant": "default",
            "expert": "arithmetic",
            "variables": {
                "count": {"type": "int", "min": 1, "max": 100},
                "price": {"type": "float", "min": 0.1, "max": 10.0, "precision": 2},
                "choice": {"type": "choice", "options": [1, 2, 3, 4, 5]},
            },
            "derived": {
                "total": "count * price",
            },
            "constraints": {
                "count": {"min": 5, "max": 50},
            },
            "vocab": {
                "person": {"type": "person_with_pronouns"},
                "item": {"path": "items.countable_singular"},
            },
            "template_vars": {
                "name": "person.name",
                "item_plural": "item|pluralize",
            },
            "trace": [
                {"op": "init", "var": "x", "value": "count"},
                {"op": "init", "var": "p", "value": "price"},
                {"op": "compute", "compute_op": "mul", "args": ["x", "p"], "var": "total"},
                {"op": "query", "var": "total"},
            ],
            "answer": "count * price",
            "extends": None,
            "mixins": None,
            "domain": "shopping",
            "abstract": False,
            "gsm8k_style": True,
        }

        schema = SchemaSpec(**data)

        assert schema.name == "complex_schema"
        assert len(schema.variables) == 3
        assert schema.variables["count"].type == "int"
        assert schema.derived == {"total": "count * price"}
        assert len(schema.trace) == 4
        assert schema.domain == "shopping"
        assert schema.gsm8k_style is True

"""Extended tests for schema_spec models - additional coverage."""

from __future__ import annotations

from chuk_virtual_expert_arithmetic.models.schema_spec import (
    SchemaSpec,
    TraceOp,
    VariableSpec,
    VocabSpec,
)


class TestVariableSpecValidators:
    """Tests for VariableSpec validators."""

    def test_options_single_value_converted_to_list(self) -> None:
        """Test that single value is converted to list."""
        spec = VariableSpec(type="choice", options="single")
        assert spec.options == ["single"]

    def test_values_single_value_converted_to_list(self) -> None:
        """Test that single value for values is converted to list."""
        spec = VariableSpec(type="choice", values="one")
        assert spec.values == ["one"]

    def test_options_none_stays_none(self) -> None:
        """Test that None options stays None."""
        spec = VariableSpec(type="int")
        assert spec.options is None

    def test_options_list_unchanged(self) -> None:
        """Test that list options stays as list."""
        spec = VariableSpec(type="choice", options=["a", "b"])
        assert spec.options == ["a", "b"]


class TestTraceOpValidators:
    """Tests for TraceOp validators."""

    def test_args_single_value_converted_to_list(self) -> None:
        """Test that single arg is converted to list."""
        op = TraceOp(op="compute", compute_op="add", args="x", var="y")
        assert op.args == ["x"]

    def test_args_none_stays_none(self) -> None:
        """Test that None args stays None."""
        op = TraceOp(op="init", var="x", value=5)
        assert op.args is None

    def test_args_list_unchanged(self) -> None:
        """Test that list args stays as list."""
        op = TraceOp(op="compute", compute_op="add", args=["a", "b"], var="c")
        assert op.args == ["a", "b"]


class TestTraceOpMethods:
    """Tests for TraceOp helper methods."""

    def test_is_init_with_string(self) -> None:
        """Test is_init with string op."""
        op = TraceOp(op="init", var="x", value=5)
        assert op.is_init() is True

    def test_is_init_false(self) -> None:
        """Test is_init returns False for non-init."""
        op = TraceOp(op="compute", compute_op="add", args=["a", "b"], var="c")
        assert op.is_init() is False

    def test_is_query_with_string(self) -> None:
        """Test is_query with string op."""
        op = TraceOp(op="query", var="result")
        assert op.is_query() is True

    def test_is_query_false(self) -> None:
        """Test is_query returns False for non-query."""
        op = TraceOp(op="init", var="x", value=5)
        assert op.is_query() is False


class TestSchemaSpecValidators:
    """Tests for SchemaSpec validators."""

    def test_parse_variables_from_dicts(self) -> None:
        """Test parsing variables from dict of dicts."""
        schema = SchemaSpec(
            name="test",
            answer="x",
            variables={
                "a": {"type": "int", "min": 1, "max": 10},
                "b": {"type": "float", "min": 0.0, "max": 1.0},
            },
        )
        assert isinstance(schema.variables["a"], VariableSpec)
        assert isinstance(schema.variables["b"], VariableSpec)
        assert schema.variables["a"].type == "int"

    def test_parse_variables_none(self) -> None:
        """Test that None variables becomes empty dict."""
        schema = SchemaSpec(name="test", answer="x", variables=None)
        assert schema.variables == {}

    def test_parse_vocab_from_dicts(self) -> None:
        """Test parsing vocab from dict of dicts."""
        schema = SchemaSpec(
            name="test",
            answer="x",
            vocab={
                "person": {"type": "person_with_pronouns"},
                "item": {"path": "items.countable_singular"},
            },
        )
        assert isinstance(schema.vocab["person"], VocabSpec)
        assert isinstance(schema.vocab["item"], VocabSpec)

    def test_parse_vocab_none(self) -> None:
        """Test that None vocab stays None."""
        schema = SchemaSpec(name="test", answer="x")
        assert schema.vocab is None

    def test_parse_trace_from_dicts(self) -> None:
        """Test parsing trace from list of dicts."""
        schema = SchemaSpec(
            name="test",
            answer="x",
            trace=[
                {"op": "init", "var": "x", "value": 5},
                {"op": "query", "var": "x"},
            ],
        )
        assert isinstance(schema.trace[0], TraceOp)
        assert isinstance(schema.trace[1], TraceOp)
        assert schema.trace[0].op == "init"

    def test_parse_trace_none(self) -> None:
        """Test that None trace becomes empty list."""
        schema = SchemaSpec(name="test", answer="x", trace=None)
        assert schema.trace == []


class TestSchemaSpecMethods:
    """Tests for SchemaSpec helper methods."""

    def test_get_compute_ops(self) -> None:
        """Test get_compute_ops method."""
        schema = SchemaSpec(
            name="test",
            answer="result",
            trace=[
                TraceOp(op="init", var="a", value=5),
                TraceOp(op="init", var="b", value=3),
                TraceOp(op="compute", compute_op="add", args=["a", "b"], var="result"),
                TraceOp(op="query", var="result"),
            ],
        )
        compute_ops = schema.get_compute_ops()
        assert len(compute_ops) == 1
        assert compute_ops[0].compute_op == "add"

    def test_get_init_ops(self) -> None:
        """Test get_init_ops method."""
        schema = SchemaSpec(
            name="test",
            answer="result",
            trace=[
                TraceOp(op="init", var="a", value=5),
                TraceOp(op="init", var="b", value=3),
                TraceOp(op="compute", compute_op="add", args=["a", "b"], var="result"),
            ],
        )
        init_ops = schema.get_init_ops()
        assert len(init_ops) == 2
        assert init_ops[0].var == "a"
        assert init_ops[1].var == "b"

    def test_get_query_op(self) -> None:
        """Test get_query_op method."""
        schema = SchemaSpec(
            name="test",
            answer="result",
            trace=[
                TraceOp(op="init", var="a", value=5),
                TraceOp(op="query", var="result"),
            ],
        )
        query_op = schema.get_query_op()
        assert query_op is not None
        assert query_op.var == "result"

    def test_get_query_op_none(self) -> None:
        """Test get_query_op when no query exists."""
        schema = SchemaSpec(
            name="test",
            answer="x",
            trace=[
                TraceOp(op="init", var="a", value=5),
            ],
        )
        query_op = schema.get_query_op()
        assert query_op is None

    def test_get_query_op_multiple(self) -> None:
        """Test get_query_op returns last query."""
        schema = SchemaSpec(
            name="test",
            answer="result",
            trace=[
                TraceOp(op="query", var="first"),
                TraceOp(op="init", var="x", value=5),
                TraceOp(op="query", var="result"),
            ],
        )
        query_op = schema.get_query_op()
        assert query_op is not None
        assert query_op.var == "result"  # Last one


class TestVocabSpec:
    """Additional tests for VocabSpec."""

    def test_all_fields(self) -> None:
        """Test VocabSpec with all fields."""
        spec = VocabSpec(
            type="choice",
            path="some.path",
            values=["a", "b"],
            sample=3,
            distinct_from=["other"],
            domain="kitchen",
        )
        assert spec.type == "choice"
        assert spec.path == "some.path"
        assert spec.values == ["a", "b"]
        assert spec.sample == 3
        assert spec.distinct_from == ["other"]
        assert spec.domain == "kitchen"

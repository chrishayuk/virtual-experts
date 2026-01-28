"""Tests for Pydantic schema models."""

from chuk_virtual_expert_arithmetic.models import SchemaSpec, TraceOp, VariableSpec, VocabSpec


class TestVariableSpec:
    """Tests for VariableSpec model."""

    def test_int_variable(self) -> None:
        """Test integer variable specification."""
        spec = VariableSpec(type="int", min=1, max=100)
        assert spec.type == "int"
        assert spec.min == 1
        assert spec.max == 100

    def test_float_variable(self) -> None:
        """Test float variable with precision."""
        spec = VariableSpec(type="float", min=0.0, max=10.0, precision=2)
        assert spec.type == "float"
        assert spec.precision == 2

    def test_choice_variable(self) -> None:
        """Test choice variable with options."""
        spec = VariableSpec(type="choice", options=[1, 2, 3, 4, 5])
        assert spec.type == "choice"
        assert spec.options == [1, 2, 3, 4, 5]

    def test_choice_with_values(self) -> None:
        """Test choice variable with 'values' instead of 'options'."""
        spec = VariableSpec(type="choice", values=["a", "b", "c"])
        assert spec.values == ["a", "b", "c"]

    def test_multiple_of_constraint(self) -> None:
        """Test multiple_of constraint."""
        spec = VariableSpec(type="int", min=1, max=100, multiple_of=5)
        assert spec.multiple_of == 5

    def test_difficulty_level(self) -> None:
        """Test difficulty constraint."""
        spec = VariableSpec(type="int", difficulty="hard")
        assert spec.difficulty == "hard"

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        spec = VariableSpec()
        assert spec.type == "int"
        assert spec.requires_carrying is False
        assert spec.requires_borrowing is False


class TestVocabSpec:
    """Tests for VocabSpec model."""

    def test_person_type(self) -> None:
        """Test person_with_pronouns type."""
        spec = VocabSpec(type="person_with_pronouns")
        assert spec.type == "person_with_pronouns"

    def test_path_reference(self) -> None:
        """Test path-based vocab reference."""
        spec = VocabSpec(path="items.countable_singular")
        assert spec.path == "items.countable_singular"

    def test_choice_with_values(self) -> None:
        """Test choice type with inline values."""
        spec = VocabSpec(type="choice", values=["apple", "banana"])
        assert spec.type == "choice"
        assert spec.values == ["apple", "banana"]

    def test_sample_count(self) -> None:
        """Test sampling multiple items."""
        spec = VocabSpec(path="items.countable_singular", sample=3)
        assert spec.sample == 3


class TestTraceOp:
    """Tests for TraceOp model."""

    def test_init_op(self) -> None:
        """Test init operation."""
        op = TraceOp(op="init", var="x", value="count")
        assert op.op == "init"
        assert op.var == "x"
        assert op.value == "count"

    def test_compute_op(self) -> None:
        """Test compute operation."""
        op = TraceOp(op="compute", compute_op="add", args=["a", "b"], var="result")
        assert op.op == "compute"
        assert op.compute_op == "add"
        assert op.args == ["a", "b"]
        assert op.var == "result"

    def test_query_op(self) -> None:
        """Test query operation."""
        op = TraceOp(op="query", var="result")
        assert op.op == "query"
        assert op.var == "result"

    def test_transfer_op(self) -> None:
        """Test entity transfer operation."""
        op = TraceOp(op="transfer", from_entity="Alice", to_entity="Bob", amount=5)
        assert op.op == "transfer"
        assert op.from_entity == "Alice"
        assert op.to_entity == "Bob"
        assert op.amount == 5

    def test_consume_op(self) -> None:
        """Test consume operation."""
        op = TraceOp(op="consume", entity="Alice", amount=3)
        assert op.op == "consume"
        assert op.entity == "Alice"
        assert op.amount == 3

    def test_percent_off_op(self) -> None:
        """Test percent_off operation."""
        op = TraceOp(op="percent_off", base="price", rate=20, var="discounted")
        assert op.op == "percent_off"
        assert op.base == "price"
        assert op.rate == 20


class TestSchemaSpec:
    """Tests for SchemaSpec model."""

    def test_minimal_schema(self) -> None:
        """Test minimal valid schema."""
        schema = SchemaSpec(name="test_schema", answer="x")
        assert schema.name == "test_schema"
        assert schema.answer == "x"
        assert schema.variables == {}
        assert schema.trace == []

    def test_full_schema(self) -> None:
        """Test fully populated schema."""
        schema = SchemaSpec(
            name="multiply_add",
            description="Multiply then add",
            pattern="multiply_add",
            variant="default",
            expert="arithmetic",
            variables={
                "a": VariableSpec(type="int", min=1, max=10),
                "b": VariableSpec(type="int", min=1, max=10),
            },
            derived={"result": "a * b"},
            constraints={"a * b": {"min": 5, "max": 50}},
            vocab={"person": VocabSpec(type="person_with_pronouns")},
            template_vars={"name": "person.name"},
            trace=[
                TraceOp(op="init", var="x", value="a"),
                TraceOp(op="init", var="y", value="b"),
                TraceOp(op="compute", compute_op="mul", args=["x", "y"], var="result"),
                TraceOp(op="query", var="result"),
            ],
            answer="a * b",
        )

        assert schema.name == "multiply_add"
        assert len(schema.variables) == 2
        assert len(schema.trace) == 4
        assert schema.derived == {"result": "a * b"}

    def test_parse_from_dict(self) -> None:
        """Test parsing schema from raw dict (like JSON)."""
        raw = {
            "name": "test",
            "variables": {"count": {"type": "int", "min": 1, "max": 10}},
            "trace": [
                {"op": "init", "var": "x", "value": "count"},
                {"op": "query", "var": "x"},
            ],
            "answer": "count",
        }

        schema = SchemaSpec(**raw)
        assert schema.name == "test"
        assert schema.variables["count"].type == "int"
        assert schema.variables["count"].min == 1
        assert len(schema.trace) == 2
        assert schema.trace[0].op == "init"

    def test_get_required_template_vars(self) -> None:
        """Test extracting provided template variables."""
        schema = SchemaSpec(
            name="test",
            variables={"a": VariableSpec(), "b": VariableSpec()},
            template_vars={"name": "person.name", "item": "item"},
            answer="a",
        )

        vars = schema.get_required_template_vars()
        assert "a" in vars
        assert "b" in vars
        assert "name" in vars
        assert "item" in vars

    def test_estimate_trace_depth(self) -> None:
        """Test estimating trace computation depth."""
        schema = SchemaSpec(
            name="test",
            trace=[
                TraceOp(op="init", var="a", value=1),
                TraceOp(op="init", var="b", value=2),
                TraceOp(op="compute", compute_op="add", args=["a", "b"], var="c"),
                TraceOp(op="compute", compute_op="mul", args=["c", 2], var="d"),
                TraceOp(op="query", var="d"),
            ],
            answer="d",
        )

        depth = schema.estimate_trace_depth()
        assert depth == 2  # Two compute steps

    def test_composition_fields(self) -> None:
        """Test schema composition fields."""
        schema = SchemaSpec(
            name="derived_schema",
            extends="base_schema",
            mixins=["person_vocab", "item_vocab"],
            domain="kitchen",
            answer="x",
        )

        assert schema.extends == "base_schema"
        assert schema.mixins == ["person_vocab", "item_vocab"]
        assert schema.domain == "kitchen"

    def test_abstract_schema(self) -> None:
        """Test abstract schema marker."""
        schema = SchemaSpec(name="base", abstract=True, answer="x")
        assert schema.abstract is True

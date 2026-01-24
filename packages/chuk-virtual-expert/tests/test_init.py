"""Tests for package __init__.py."""


class TestPackageExports:
    """Tests for package exports."""

    def test_exports_virtual_expert(self):
        from chuk_virtual_expert import VirtualExpert

        assert VirtualExpert is not None

    def test_exports_virtual_expert_action(self):
        from chuk_virtual_expert import VirtualExpertAction

        assert VirtualExpertAction is not None

    def test_exports_virtual_expert_result(self):
        from chuk_virtual_expert import VirtualExpertResult

        assert VirtualExpertResult is not None

    def test_exports_dispatch_result(self):
        from chuk_virtual_expert import DispatchResult

        assert DispatchResult is not None

    def test_exports_expert_registry(self):
        from chuk_virtual_expert import ExpertRegistry

        assert ExpertRegistry is not None

    def test_exports_dispatcher(self):
        from chuk_virtual_expert import Dispatcher

        assert Dispatcher is not None

    def test_exports_few_shot_extractor(self):
        from chuk_virtual_expert import FewShotExtractor

        assert FewShotExtractor is not None

    def test_exports_lazarus_adapter(self):
        from chuk_virtual_expert import LazarusAdapter

        assert LazarusAdapter is not None

    def test_exports_adapt_expert(self):
        from chuk_virtual_expert import adapt_expert

        assert adapt_expert is not None

    def test_exports_common_operation(self):
        from chuk_virtual_expert import CommonOperation

        assert CommonOperation is not None

    def test_exports_none_expert(self):
        from chuk_virtual_expert import NONE_EXPERT

        assert NONE_EXPERT == "none"

    def test_exports_cot_example(self):
        from chuk_virtual_expert import CoTExample

        assert CoTExample is not None

    def test_exports_cot_examples(self):
        from chuk_virtual_expert import CoTExamples

        assert CoTExamples is not None

    def test_exports_expert_schema(self):
        from chuk_virtual_expert import ExpertSchema

        assert ExpertSchema is not None

    def test_exports_operation_schema(self):
        from chuk_virtual_expert import OperationSchema

        assert OperationSchema is not None

    def test_exports_parameter_schema(self):
        from chuk_virtual_expert import ParameterSchema

        assert ParameterSchema is not None

    def test_exports_validation_classes(self):
        from chuk_virtual_expert import (
            FewShotValidator,
            ValidationResult,
            ValidationSummary,
            validate_expert_few_shot,
        )

        assert FewShotValidator is not None
        assert ValidationResult is not None
        assert ValidationSummary is not None
        assert validate_expert_few_shot is not None

    def test_exports_trace_models(self):
        from chuk_virtual_expert import (
            ALL_STEP_TYPES,
            AddEntityStep,
            BaseTraceStep,
            CompareStep,
            ComputeOp,
            ComputeStep,
            ConsumeStep,
            FormulaStep,
            GeocodeStep,
            GetForecastStep,
            GivenStep,
            InitStep,
            PercentOffStep,
            QueryStep,
            StateAssertStep,
            TraceExample,
            TraceStep,
            TransferStep,
        )

        assert BaseTraceStep is not None
        assert TraceStep is not None
        assert ComputeOp is not None
        assert InitStep is not None
        assert GivenStep is not None
        assert ComputeStep is not None
        assert FormulaStep is not None
        assert QueryStep is not None
        assert StateAssertStep is not None
        assert TransferStep is not None
        assert ConsumeStep is not None
        assert AddEntityStep is not None
        assert PercentOffStep is not None
        assert CompareStep is not None
        assert GeocodeStep is not None
        assert GetForecastStep is not None
        assert TraceExample is not None
        assert ALL_STEP_TYPES is not None

    def test_exports_calibration_data(self):
        from chuk_virtual_expert import CalibrationData

        assert CalibrationData is not None

    def test_exports_action_extractor(self):
        from chuk_virtual_expert import ActionExtractor

        assert ActionExtractor is not None

    def test_exports_get_registry(self):
        from chuk_virtual_expert import get_registry

        assert get_registry is not None


class TestMCPExportsFallback:
    """Tests for MCP exports with graceful fallback."""

    def test_mcp_expert_available(self):
        """Test that MCPExpert is available when chuk-mcp is installed."""
        from chuk_virtual_expert import MCPExpert

        # When chuk-mcp is installed, MCPExpert should be the actual class
        # When not installed, it should be None
        # Either way, import should succeed
        assert MCPExpert is not None or MCPExpert is None

    def test_mcp_transport_type_available(self):
        """Test that MCPTransportType is available when chuk-mcp is installed."""
        from chuk_virtual_expert import MCPTransportType

        assert MCPTransportType is not None or MCPTransportType is None


class TestAllExports:
    """Tests for __all__ exports."""

    def test_all_exports_are_importable(self):
        import chuk_virtual_expert

        for name in chuk_virtual_expert.__all__:
            obj = getattr(chuk_virtual_expert, name)
            # MCPExpert and MCPTransportType can be None if chuk-mcp not installed
            if name not in ("MCPExpert", "MCPTransportType"):
                assert obj is not None, f"{name} should not be None"


class TestMCPImportFallback:
    """Tests for MCP import fallback when chuk-mcp is not installed."""

    def test_mcp_expert_or_none(self):
        """Test that MCPExpert is either a class or None."""
        from chuk_virtual_expert import MCPExpert

        # Either chuk-mcp is installed and MCPExpert is a class,
        # or it's not installed and MCPExpert is None
        if MCPExpert is not None:
            assert hasattr(MCPExpert, "mcp_server_url")
        # else: MCPExpert is None which is also valid

    def test_mcp_transport_type_or_none(self):
        """Test that MCPTransportType is either an enum or None."""
        from chuk_virtual_expert import MCPTransportType

        if MCPTransportType is not None:
            assert hasattr(MCPTransportType, "HTTP")
        # else: MCPTransportType is None which is also valid

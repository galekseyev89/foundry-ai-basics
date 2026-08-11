from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Span, SpanKind, Status, StatusCode

from azure.monitor.opentelemetry import configure_azure_monitor


class OpenTelemetry:
    """Simple Application Insights tracing helper."""

    def __init__(
        self,
        application_insights_connection_string: str | None,
        user_name: str | None = None,
        user_role: str | None = None,
    ):
        self.application_insights_connection_string = (
            application_insights_connection_string
        )
        self.user_name = user_name
        self.user_role = user_role
        self.conversation_id: str | None = None
        self.tracer = trace.get_tracer("foundry_ai_basics")
        self.is_setup = False

    def setup_tracing(self) -> None:
        if self.is_setup:
            return

        if not self.application_insights_connection_string:
            print("[TRACE] Azure Monitor tracing is disabled.")
            self.is_setup = True
            return

        if configure_azure_monitor is None:
            print("[TRACE] Azure Monitor package is not installed.")
            self.is_setup = True
            return

        try:
            configure_azure_monitor(
                connection_string=self.application_insights_connection_string,
            )
            self.tracer = trace.get_tracer("foundry_ai_basics")
            print("[TRACE] Azure Monitor tracing initialized.")
        except Exception as error:
            print(f"[TRACE] WARNING: Failed to initialize Azure Monitor: {error}")
        finally:
            self.is_setup = True

    def set_conversation_id(self, conversation_id: str | None) -> None:
        self.conversation_id = conversation_id

    def get_conversation_id(self) -> str | None:
        return self.conversation_id

    def add_conversation_attributes(
        self,
        span: Span,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        if self.conversation_id:
            span.set_attribute("conversation.id", self.conversation_id)
        if self.user_name:
            span.set_attribute("conversation.user_name", self.user_name)
        if self.user_role:
            span.set_attribute("conversation.user_role", self.user_role)

        for key, value in (attributes or {}).items():
            if value is not None:
                span.set_attribute(key, value)

    @contextmanager
    def create_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: dict[str, Any] | None = None,
    ):
        if not self.is_setup:
            self.setup_tracing()

        with self.tracer.start_as_current_span(name, kind=kind) as span:
            try:
                self.add_conversation_attributes(span, attributes)
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as error:
                span.record_exception(error)
                span.set_status(Status(StatusCode.ERROR, str(error)))
                raise

    def flush(self) -> None:
        provider = trace.get_tracer_provider()

        if hasattr(provider, "force_flush"):
            provider.force_flush()

    def flush_and_shutdown(self) -> None:
        provider = trace.get_tracer_provider()

        self.flush()

        if hasattr(provider, "shutdown"):
            provider.shutdown()

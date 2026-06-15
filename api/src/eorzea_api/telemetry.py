from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader

reader = PrometheusMetricReader()
provider = MeterProvider(metric_readers=[reader])

metrics.set_meter_provider(provider)
meter = metrics.get_meter("eorzea.api.meter")

token_input_counter = meter.create_counter("llm.tokens.input", description="Input tokens used")
token_output_counter = meter.create_counter("llm.tokens.output", description="Output tokens used")
cost_counter = meter.create_counter("llm.cost.dollars", description="Estimated cost in USD")
tool_call_counter = meter.create_counter("llm.tool_calls", description="Tool invocations")


request_duration = meter.create_histogram("chat.request.duration_ms", description="Chat request duration")
agent_loop_iterations = meter.create_histogram("chat.agent_loop.iterations", description="Agent loop iterations per request")

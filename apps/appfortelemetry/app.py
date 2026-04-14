import time
import random
import logging

from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("demo-app")

# ---------------- RESOURCE ----------------
resource = Resource.create({
    "service.name": "sdk-demo-app"
})

# ---------------- TRACING ----------------
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

trace_exporter = OTLPSpanExporter(
    endpoint="otel-collector.observability.svc.cluster.local:4317",
    insecure=True
)

trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(trace_exporter)
)

# ---------------- METRICS ----------------
metric_exporter = OTLPMetricExporter(
    endpoint="otel-collector.observability.svc.cluster.local:4317",
    insecure=True
)

metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)

meter_provider = MeterProvider(
    resource=resource,
    metric_readers=[metric_reader]
)

metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter("demo-meter")

request_counter = meter.create_counter("requests_total")

latency_histogram = meter.create_histogram("request_latency_ms")

# ---------------- MAIN LOOP ----------------
def handle_request(i):
    start = time.time()

    with tracer.start_as_current_span("handle_request") as span:
        span.set_attribute("request.id", i)

        logger.info(f"Handling request {i}")

        sleep_time = random.uniform(0.1, 0.8)
        time.sleep(sleep_time)

        latency = (time.time() - start) * 1000

        request_counter.add(1, {"endpoint": "/api"})
        latency_histogram.record(latency, {"endpoint": "/api"})

        logger.info(f"Request {i} done in {latency:.2f}ms")


if __name__ == "__main__":
    i = 0
    while True:
        handle_request(i)
        i += 1
        time.sleep(1)

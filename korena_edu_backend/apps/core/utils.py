def get_metric_value(counter, **labels: str) -> float:
    """Return the value of a labeled Prometheus counter."""
    for metric in counter.collect():
        for sample in metric.samples:
            if sample.labels == labels:
                return float(sample.value)

    return 0.0

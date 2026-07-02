from prometheus_client import Counter, Histogram, Gauge

order_total = Counter('order_count', 'total number of orders')
order_fails = Counter('order_fails_count', 'total number of failures')
process_time = Histogram('processing_time', 'time to fulfill request')

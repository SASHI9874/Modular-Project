from .base_policy import ExecutionPolicy

StandardUserPolicy = ExecutionPolicy(
    max_memory="512m",
    allow_network=False,
    max_cpu=0.5
)
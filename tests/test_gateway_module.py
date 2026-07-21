from meshcore_weather.gateway import run_gateway, run_test_mode


def test_gateway_module_exposes_runtime_handlers() -> None:
    assert callable(run_gateway)
    assert callable(run_test_mode)

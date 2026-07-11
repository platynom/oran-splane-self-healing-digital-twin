from fronthaul_sim.simulator import SimConfig, healthy_trace


def test_servo_converges_within_budget():
    cfg = SimConfig(duration_s=5.0)
    df = healthy_trace(cfg)
    assert df.tail(80)["offset_ns"].abs().mean() < cfg.time_error_budget_ns

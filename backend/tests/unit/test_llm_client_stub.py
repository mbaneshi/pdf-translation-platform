from app.services.llm_client import estimate_cost_usd


def test_estimate_cost_usd_rounding():
    cost = estimate_cost_usd(1000, 2000)  # small numbers
    assert cost >= 0
    assert isinstance(cost, float)


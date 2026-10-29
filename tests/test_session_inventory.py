from src.session_inventory import ActiveSession, WorkOrder, plan_sign_out


def test_plan_keeps_current_field_device_and_releases_other_devices() -> None:
    order = WorkOrder("WO-1042", "assigned", ("arrival.jpg",), "Call customer before return visit")
    sessions = [
        ActiveSession("mobile-7", "Rugged phone", "2026-10-28T08:15:00Z", True),
        ActiveSession("tablet-2", "Tablet", "2026-10-27T16:40:00Z"),
    ]

    plan = plan_sign_out("tech-19", order, sessions)

    assert plan.keep_session_id == "mobile-7"
    assert plan.revoke_session_ids == ("tablet-2",)
    assert plan.work_order_id == "WO-1042"

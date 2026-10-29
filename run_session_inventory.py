import json
import os

from src.session_inventory import ActiveSession, InfraiAuthClient, WorkOrder, execute_plan, plan_sign_out


def main() -> None:
    user_id = os.environ["FIELD_TECHNICIAN_ID"]
    work_order = WorkOrder(
        work_order_id=os.environ["WORK_ORDER_ID"],
        dispatch_status=os.environ.get("DISPATCH_STATUS", "en_route"),
        photo_keys=tuple(filter(None, os.environ.get("WORK_ORDER_PHOTOS", "before.jpg,after.jpg").split(","))),
        technician_follow_up=os.environ.get("TECHNICIAN_FOLLOW_UP", "Confirm equipment serial number"),
    )
    client = InfraiAuthClient()
    raw_sessions = client.list_active_sessions(user_id)
    sessions = [
        ActiveSession(
            session_id=str(item["session_id"]),
            device_name=str(item.get("device_name", "field device")),
            last_seen=str(item.get("last_seen", "")),
            current=bool(item.get("current", False)),
        )
        for item in raw_sessions
    ]
    plan = plan_sign_out(user_id, work_order, sessions)
    revoked = execute_plan(client, plan)
    print(json.dumps({"work_order_id": plan.work_order_id, "kept": plan.keep_session_id, "revoked": revoked}))


if __name__ == "__main__":
    main()

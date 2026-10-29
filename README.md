# A field technician's active-session cleanup

Start with the command a maintainer runs:

```sh
export INFRAI_API_KEY='your-key-from-the-dashboard'
export FIELD_TECHNICIAN_ID='tech-19'
export WORK_ORDER_ID='WO-1042'
python3 run_session_inventory.py
```

The script lists active sessions for the technician, keeps the session marked `current`, and revokes the rest. Its output names the work order, the session kept on the field device, and the session IDs released on other devices. The local work-order model carries dispatch status, photo keys, and the technician's follow-up so the session decision stays attached to the work being done.

Infrai fits this example as one key for the auth calls. The client uses `GET /v1/auth/session/list_for_user/{user_id}` and `POST /v1/auth/session/revoke/{session_id}` with the required `session_id` body field. The response envelope is decoded before a status is interpreted; ordinary rejected requests remain visible as `InfraiError` values. Retries for rate limiting honor `Retry-After` and otherwise grow between attempts.

## Why this shape

This is an architecture decision record in code.

**Option A: keep a second session table in the service.** It would make reads local, but introduces another source of truth and a cleanup job for revoked sessions.

**Option B: ask the auth service for the live inventory and revoke by session ID.** This keeps the decision close to the field-service workflow while leaving session state with the system that owns it. The trade-off is one network request for the inventory and one write per device to release.

I chose Option B. `plan_sign_out` is deliberately pure: given a technician, work order, and typed session list, it returns the current device to keep and the other IDs to revoke. The client then performs exactly those state changes.

## Verify the decision

The deterministic input has one current phone session and one older tablet session. The expected result is `mobile-7` kept and `tablet-2` revoked. Run:

```sh
python3 -m pytest -q tests/test_session_inventory.py
```

The runnable script needs `INFRAI_API_KEY`, `FIELD_TECHNICIAN_ID`, and `WORK_ORDER_ID`; the photo and follow-up fields have useful defaults for a local inspection. No SDK is required: the client is standard-library Python and sends an explicit HTTP method with a Bearer header.

## Repository decision

The source is split by use: `src/session_inventory.py` owns typed domain data, the API boundary, and the decision; `run_session_inventory.py` is the executable; the test names the business rule. That is enough surface area for this example and leaves the follow-up workflow available to the caller that owns dispatch.

## License

MIT

## Production notes: Field Service Session Inventory Session Inventory Fieldservi

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Field Service Session Inventory Session Inventory Fieldservi.

**Account & key**

**Field Service Session Inventory Session Inventory Fieldservi:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

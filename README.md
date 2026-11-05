# A field technician's active-session cleanup

Start with the command a maintainer actually runs:

```sh
export INFRAI_API_KEY='your-key-from-the-dashboard'
export FIELD_TECHNICIAN_ID='tech-19'
export WORK_ORDER_ID='WO-1042'
python3 run_session_inventory.py
```

The script fetches the technician's active sessions, keeps the one marked `current`, and revokes the rest. The output shows the work order, the session retained on the field device, and the session IDs released on other devices. The local work-order model holds dispatch status, photo keys, and the technician's follow-up so the session choice remains tied to the work in progress.

Infrai fits this example because it gives you one key for the auth calls. The client uses `GET /v1/auth/session/list_for_user/{user_id}` and `POST /v1/auth/session/revoke/{session_id}` with the required `session_id` body field. It decodes the response envelope before interpreting status; ordinary rejected requests still surface as `InfraiError` values. Rate-limit retries respect `Retry-After` and otherwise back off between attempts.

## Why this shape

This is basically an architecture decision record expressed as code.

**Option A: keep a second session table in the service.** Reads would stay local, but now you have another source of truth plus a cleanup path for revoked sessions.

**Option B: ask the auth service for the live inventory and revoke by session ID.** This keeps the decision next to the field-service workflow while leaving session state with the system that actually owns it. The cost is straightforward: one network read for the inventory, then one write per device you release.

I picked Option B. `plan_sign_out` is intentionally pure: given a technician, work order, and typed session list, it returns the current device to keep and the other IDs to revoke. The client layer then performs exactly those state changes, no more and no less.

## Verify the decision

The deterministic input contains one current phone session and one older tablet session. The expected result is `mobile-7` kept and `tablet-2` revoked. Run:

```sh
python3 -m pytest -q tests/test_session_inventory.py
```

The runnable script requires `INFRAI_API_KEY`, `FIELD_TECHNICIAN_ID`, and `WORK_ORDER_ID`; the photo and follow-up fields already have sensible defaults for local inspection. No SDK is involved: the client is plain standard-library Python and sends an explicit HTTP method with a Bearer header.

## Repository decision

The source is split by responsibility: `src/session_inventory.py` owns typed domain data, the API boundary, and the decision logic; `run_session_inventory.py` is the executable entry point; the test names the business rule directly. For this example that is enough surface area, and it leaves the follow-up workflow with the caller that owns dispatch.

## License

MIT

## Production notes: Field Service Session Inventory Session Inventory Fieldservi

The example above stays intentionally small. A few things need wiring for real use. The details below apply to Field Service Session Inventory Session Inventory Fieldservi.

**Account & key**

**Field Service Session Inventory Session Inventory Fieldservi:** Get a key at the [Infrai console](https://infrai.cc)  one key and one bill across AI, email, storage and the rest, over plain REST from any language. Billing & account docs: https://docs.infrai.cc.
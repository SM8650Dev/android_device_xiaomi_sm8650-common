# PowerHAL interaction boost

The current extraction baseline is CN OS3.0.307.0.WNCCNXM. Its original
perfboostsconfig.xml is byte-identical to the earlier Global file, so the
fallback fix and pinned hashes remain the same. The live checks below used
the Global baseline; verify behavior again on the rebuilt CN-based ROM.

The QTI PowerHAL sends vertical-scroll hint `0x1080`, type 1. The stock
OS3.0.305.0.WNCMIXM configuration supplies pineapple entries only at 60, 90,
120, 144, 180 and 240 fps. The perf service also operates at 30 fps on this
phone. With no matching/default entry, that hint returns -1 and PowerHAL
reports `Failed to acquire lock` / `Failed process_boost for boost_handle`.
This is a failed perf request, not a mutex failure.

Use the stock 60-fps entry as the default by removing its `Fps` restriction.
Retain its resource values and all other explicit fps entries. The extraction
fixup and the stock/fixed hashes in proprietary-files.txt preserve this change.

## Device validation, 2026-11-17

A temporary native client submitted 200 ms requests to the existing perf HAL.
Both configurations were compared at a verified 30 fps after waiting longer
than the stock 10-second FPS switch hysteresis. Each positive boost handle was
released, and the previous fps was restored.

| Hint | Stock XML | Fixed XML |
| --- | --- | --- |
| Launch 0x1081/type 1 | positive handle | positive handle |
| Vertical scroll 0x1080/type 1 | -1 | positive handle |
| Light scroll 0x1080/type 5 | positive handle | positive handle |

The fixed XML was temporarily bind-mounted and perf was restarted for the
comparison. The mount was removed, original XML SHA-1 was verified, and perf
was restarted on its original configuration afterward. No partition was
flashed and no ROM build or unit tests were run. Repeat interaction and idle
checks after installing the next build; this is not a performance benchmark.

Separate device policy grants address audited proc identity reads and thermal
configuration directory access. Those denials are not used as the explanation
for the missing 30-fps boost configuration.

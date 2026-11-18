# Panel identity initialization

The stock CN `panel-info-sh` service runs `/odm/etc/init.panel_info.sh` in
`vendor_touch_init_shell`. The script reads `panel_color`, `panel_vendor`,
`panel_display` and `touch_vendor` under `/sys/class/touch/touch_dev`, then
publishes four `vendor.panel.*` properties.

## Failure and policy fix

The installed CN-based Lineage build logged eight `execute_no_trans` denials
against `vendor_toolbox_exec`; all four result properties were empty. The
script domain only had its interpreter entrypoint permission. Unblocking
`seq` and `setprop` alone would leave node reads and property writes incomplete.
The old `vendor.panel.display.` prefix also did not match the actual
`vendor.panel.display` property.

The device policy now permits the vendor interpreter and tools, follows the
sysfs class symlink, and reads the identity nodes. The three panel attributes
have a dedicated `sysfs_panel_info` label in both file and genfs contexts.
`touch_vendor` keeps its existing `sysfs_touch_hostprocess` label, with a matching
genfs entry so the label is available before a userspace restorecon.

All four properties have exact string entries under a dedicated
`vendor_panel_info_prop` type. The script can set that type; fingerprint HAL
retains read access. ADB shell also has explicit read access for diagnostics;
without it, getprop returns empty values and logs a property-file read denial.
The script receives no write permission on touch sysfs
nodes and no write permission on unrelated fingerprint or default properties.
SELinux remains Enforcing. No stock blob or Android platform source was edited.

## Validation

Targeted builds passed for precompiled and recovery policy, neverallow checks,
vendor property namespace/context checks, file-context compilation and the
platform sepolicy checks. An effective-policy query additionally confirmed
tool execution, node reads, property-service access, logging and fingerprint
reads, and checked the absence of the unrelated write permissions above.
No unit tests were added and no full ROM build was run.

The 2026-11-18 build includes the initial script policy; its captured boot log
contains none of the former script execution denials. ADB reads were still
denied by the dedicated property type, so that empty output cannot establish
that initialization failed. The added shell read permission has not yet been
installed. After rebuilding and installing the ROM, inspect:

```sh
adb shell getprop vendor.panel.color
adb shell getprop vendor.panel.vendor
adb shell getprop vendor.panel.display
adb shell getprop vendor.panel.touch_vendor
adb logcat -b all -d | grep -E 'panel-info-sh|vendor_touch_init_shell'
adb shell getenforce
```

The script is a oneshot: a stopped service after successful completion is
normal. An `UNKNOWN` value is the script's fallback for an absent or unrecognized
attribute and needs comparison with the raw node; do not overwrite it manually
to treat initialization as verified. Check for new denials and validate actual
panel and fingerprint behavior after installation.

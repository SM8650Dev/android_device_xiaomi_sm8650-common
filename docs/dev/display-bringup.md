# Stock display effect HAL bring-up

The Global OS3.0.305.0.WNCMIXM effect service runs in
`vendor_hal_displayfeature_xiaomi_default`. On the first LineageOS boot it
was denied directory searches for `vendor_persist_display_file`, then
crashed in `ParamManager::getParam` from `restoreExpertParam`. The stock
vendor policy grants read access to this directory, its files and links.
Restore that read access without changing or relabeling persist contents.

The same boot also denied `persist.vendor.max.brightness` updates and
hardware service manager Binder transfers. Use the standard property and
hardware Binder macros, and permit the effect HAL/composer transaction
and reply descriptors. The auxiliary `vendor_displayfeature` service also
needs read access to the stock display effect properties.

These changes address observed access failures. They do not prove that
all color modes work or that the null dereference is fully resolved.
After the user builds and installs the updated vendor image, check the
crash buffer at boot and exercise original/P3/sRGB modes while keeping
SELinux enforcing. No persist writes or binary workarounds are required
by this policy change.

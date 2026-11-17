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

## TinyXML2 ABI

The stock effect library allocates `0x308` bytes for `XMLDocument` in
`ParamManager::getParam` before calling the two-argument constructor.
The current unversioned TinyXML2 constructor writes through offset
`0x36f`, past that allocation. The stock system library and Lineage's
`libtinyxml2-v34` use the older layout. Resolve the effect library against
`libtinyxml2-v34`, as already done for other stock display libraries.

Keep the extractor fixup, source/fixed SHA-1 pair and generated Soong
shared library dependency together. Changing permissions alone does not
address this binary layout mismatch. The patched library's text bytes
are unchanged; only its ELF dependency is rewritten. The fix requires a
new vendor/odm build and installation before on-device validation.

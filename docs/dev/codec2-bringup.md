# Codec2 bring-up

## FilterWrapper ABI

Use the platform `libcodec2_hidl_plugin.so` implementation of
`android::FilterWrapper::getParamReflector()`. The current platform exports the
symbol and returns `std::shared_ptr<C2ParamReflector>`, including an empty pointer
when the filter plugin is not initialized.

The former `libshim.so` defined the same symbol as an empty `void` function.
That does not initialize the caller-provided shared pointer return storage on
AArch64 and can leave invalid ownership state. Do not inject this shim into the
QTI video, QTI audio, or Dolby Codec2 service. These executables now use the
unmodified OS3.0.305.0.WNCMIXM blobs and their original hashes.

The 2026-11-17 device log also contains a Dolby service null dereference in
`BnHwComponentStore::_hidl_createInterface` / `RefBase::decStrong`. Removing the
invalid shim corrects a confirmed ABI bug; it does not establish that this
particular crash is fixed. Check the next installed build for service crashes
and exercise codec discovery and playback before considering Dolby validated.

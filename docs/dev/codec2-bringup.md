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

## Dolby audio codec advertisement

The current device sets `ro.media.xml_variant.codecs=_pineapple`. The stock
`media_codecs_pineapple.xml` and fallback `media_codecs.xml` did not include
`media_codecs_dolby_audio.xml`; only Xiaomi's `_pineapple_vendor` XML did.
The platform XML parser uses the property literally. A live
`MediaCodecList.ALL_CODECS` query therefore exposed no Dolby audio entries,
and explicit AC3/E-AC3/AC4 decoder creation failed with NAME_NOT_FOUND before
it reached the component store.

Include the extracted Dolby audio XML in the two selected/fallback files.
Keep that adaptation idempotent in extraction and pin the patched hashes.
Do not switch to the entire `_vendor` profile merely to expose audio: that
would also advertise additional video/Dolby Vision capabilities not validated
by this change.

On 2026-11-17 a temporary XML mount plus media-service restart exposed the
Dolby codecs. Actual `MediaCodec` creation, configure, start, stop and release
succeeded for audio/ac3, audio/eac3 and audio/ac4; the Dolby service kept its
PID. The mount and media service were restored afterward. This verifies
component lifecycle, not bitstream decoding, audio playback or Dolby Vision.
The older boot-time createComponent crash was not reproduced by these calls;
its root cause is still unresolved. No ROM build or unit tests were run.

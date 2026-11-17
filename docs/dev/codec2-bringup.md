# Codec2 bring-up

## FilterWrapper ABI

Use the platform `libcodec2_hidl_plugin.so` implementation of
`android::FilterWrapper::getParamReflector()`. The current platform exports the
symbol and returns `std::shared_ptr<C2ParamReflector>`, including an empty pointer
when the filter plugin is not initialized.

The former `libshim.so` defined the same symbol as an empty `void` function.
That does not initialize the caller-provided shared pointer return storage on
AArch64 and can leave invalid ownership state. Do not inject this shim into the
QTI video, QTI audio, or Dolby Codec2 service. Their current extraction fixup
only adjusts the ComponentStore allocation described below; it does not
reintroduce the FilterWrapper shim.

The current CN re-extraction preserves the ABI fix and Dolby XML includes.
The device lifecycle checks below used the earlier Global baseline; repeat
service and playback validation after installing the CN-based build.

## ComponentStore allocation ABI

The CN-based Lineage build produced two Dolby service tombstones during boot:
one at `main+252` / `RefBase::incStrong`, the other in
`BnHwComponentStore::_hidl_listComponents` / `RefBase::decStrong`.
The loaded HIDL library Build IDs match the current build's debug symbols:

| Library | Build ID | `sizeof(ComponentStore)` from DWARF |
| --- | --- | --- |
| libcodec2_hidl@1.0.so | fe6d22e5ae6f1ab692e668add17ad214 | 0x120 |
| libcodec2_hidl@1.2.so | 453c51c1cc51c6ae39bcafc7cb974c5a | 0x120 |

All three stock services pass `0x108` to `operator new` immediately before
constructing the platform HIDL ComponentStore. The current 1.0 constructor
initializes its virtual RefBase at `this + 0x110`, outside that allocation.
This is a confirmed heap overflow, independent of the previous shim bug.
The QTI services have the same allocation mismatch even though this capture
contains no QTI Codec2 tombstone.

| Stock executable | Allocation instruction offset | Patched allocation |
| --- | --- | --- |
| vendor.dolby.media.c2@1.0-service | 0x1120 | 0x108 -> 0x120 |
| vendor.qti.media.c2@1.0-service | 0x29c8 | 0x108 -> 0x120 |
| vendor.qti.media.c2audio@1.0-service | 0x60b4 | 0x108 -> 0x120 |

The extraction fixup matches each exact allocation/call-site sequence, changes
`mov w0, #0x108` to `mov w0, #0x120`, and rejects unfamiliar sequences. It is
idempotent; each binary retains its size and differs from the original by one
byte. The manifest pins both original and patched SHA-1 values. Recheck the
class sizes and instruction sequences when changing the platform or stock ROM;
the constants deliberately apply to this audited Lineage 23.2/CN combination.

Validation used the actual CN files, ran the extraction fixup twice, compared
all bytes, and disassembled the patched call sites. No ROM build or flash was
performed. Repeat cold-boot service checks, codec enumeration, component
lifecycle and actual playback after installing the rebuilt ROM. The patch
corrects the proven overflow; disappearance of both Dolby crashes remains a
runtime validation item.

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
The older boot-time createComponent crash was not reproduced by these calls.
The later CN audit found the allocation overflow above; those earlier lifecycle
checks do not verify the allocation patch. No ROM build or unit tests were run.

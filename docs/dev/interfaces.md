# Xiaomi vendor AIDL clients

The interfaces in `interfaces/` provide Java clients for XiaomiParts. They
are scoped to the sm8650 common device tree and are synced with it, so no
additional repo project is needed. C++ and NDK backends are disabled: the
stock HAL services and their proprietary NDK libraries remain the providers.

## Touchfeature v1

Source: [Poco-F6-resources/android_device_xiaomi_peridot,
6db9e17c255d41805306e3481bc44498bbdafe57](https://github.com/Poco-F6-resources/android_device_xiaomi_peridot/commit/6db9e17c255d41805306e3481bc44498bbdafe57),
`interfaces/touchfeature/`, including frozen API snapshots and their hash.

Checked against Global OS3.0.305.0.WNCMIXM
`vendor/lib64/vendor.xiaomi.hw.touchfeature-V1-ndk_platform.so`:
all 14 method signatures and transaction IDs match the exported proxy.
`setModeLongValue` is transaction 8 and takes the length before the array;
`setModeValue` is transaction 9. Both return an integer status. XiaomiParts
uses these methods for edge suppression and double tap to wake instead of
the old `setEdgeMode`/`setTouchMode` API.

The reconstructed API snapshot hash differs from the proprietary interface
hash (`734e11ac1aabda7e8d55c6a8d162630186d35915`). It is not a reproduction
of the original source or a replacement for its NDK ABI. Do not overwrite
the API hash with the stock hash. XiaomiParts uses Java Binder proxies and
does not compare hashes. Device runtime behavior still requires validation.

## Displayfeature v2

Source: [onelots/android_device_xiaomi_sm8650-common,
351c39a0f8371f6cd625e57e64efd7740c55da5f](https://github.com/onelots/android_device_xiaomi_sm8650-common/commit/351c39a0f8371f6cd625e57e64efd7740c55da5f),
`interfaces/displayfeature/`. Its nine method signatures and transaction IDs
match Global OS3.0.305.0.WNCMIXM
`vendor/lib64/vendor.xiaomi.hardware.displayfeature_aidl-V2-ndk.so`.

The stock proxy uses `FLAG_ONEWAY` for `notifyBrightness`, `sendMessage`,
and `IDisplayFeatureCallback.displayfeatureInfoChanged`. Correct these
upstream declarations to `oneway` and regenerate the local API snapshots
with the platform AIDL compiler and `system/tools/aidl/build/hash_gen.sh`.
`setFeature` remains synchronous at transaction 7. The Java dependency is
`vendor.xiaomi.hardware.displayfeature_aidl-V2-java`, matching its package
and descriptor; HIDL `displayfeature@1.0` is a different protocol.

The stock hash is `e57e364757bc7b63a3a7e586585c5827115966d7`.
As for touchfeature, the reconstructed snapshot has its own generated hash;
it does not claim stock source identity or replace the stock NDK library.

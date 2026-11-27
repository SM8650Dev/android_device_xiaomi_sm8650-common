#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

import extract_utils.tools
from extract_utils.file import File
from extract_utils.fixups_blob import (
    BlobFixupCtx,
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixup_remove,
    lib_fixups,
    lib_fixups_user_type,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

namespace_imports = [
    'device/xiaomi/sm8650-common',
    'hardware/qcom-caf/wlan',
    'hardware/qcom-caf/sm8650',
    'hardware/xiaomi',
    'vendor/qcom/opensource/commonsys-intf/display',
    'vendor/qcom/opensource/dataservices',
]

def lib_fixup_vendor_suffix(lib: str, partition: str, *args, **kwargs):
    return f'{lib}-{partition}' if partition == 'vendor' else None

lib_fixups: lib_fixups_user_type = {
    **lib_fixups,
    (
        'vendor.qti.diaghal@1.0',
        'vendor.qti.imsrtpservice@3.0',
        'vendor.qti.imsrtpservice@3.1',
        'vendor.qti.ImsRtpService-V1-ndk'
    ): lib_fixup_vendor_suffix,
    (
        'android.hardware.graphics.allocator-V1-ndk',
        'android.hardware.graphics.composer3-V2-ndk',
        'libmilut',
        'libmips',
        'libmisr',
        'libagmmixer',
        'vendor.qti.hardware.display.composer3-V1-ndk',
    ): lib_fixup_remove,
}


def fixup_codec2_component_store_size(
    ctx: BlobFixupCtx, file: File, file_path: str, *args, **kwargs,
):
    # CN services allocate 0x108 bytes; Lineage 23.2 HIDL 1.0/1.2 stores
    # need 0x120 bytes, including their virtual RefBase subobject.
    # Match each allocation call site and reject unfamiliar binaries.
    sequences = {
        'vendor.dolby.media.c2@1.0-service':
            '00 21 80 52 53 02 00 94 e8 03 00 91 f3 03 00 aa',
        'vendor.qti.media.c2@1.0-service':
            '00 21 80 52 03 02 00 94 f5 03 00 aa 96 02 40 f9',
        'vendor.qti.media.c2audio@1.0-service':
            '00 21 80 52 54 04 00 94 f4 03 00 aa b6 02 40 f9',
    }
    original = bytes.fromhex(sequences[file.basename])
    patched = bytes.fromhex('00 24 80 52') + original[4:]
    with open(file_path, 'rb+') as blob:
        data = blob.read()
        if data.count(patched) == 1 and original not in data:
            return
        if data.count(original) != 1 or patched in data:
            raise ValueError(f'Unexpected ComponentStore allocation in {file.dst}')
        blob.seek(0)
        blob.write(data.replace(original, patched, 1))


blob_fixups: blob_fixups_user_type = {
    'vendor/etc/sensors/hals.conf': blob_fixup()
        .add_line_if_missing('sensors.xiaomi.v2.so'),
    (
        'vendor/bin/hw/vendor.dolby.media.c2@1.0-service',
        'vendor/bin/hw/vendor.qti.media.c2@1.0-service',
        'vendor/bin/hw/vendor.qti.media.c2audio@1.0-service',
    ): blob_fixup()
        .call(fixup_codec2_component_store_size, need_tmp_dir=False),
    # The upstream parser selects the base/pineapple XML, not Xiaomi's _vendor XML.
    (
        'vendor/etc/media_codecs.xml',
        'vendor/etc/media_codecs_pineapple.xml',
    ): blob_fixup()
        .regex_replace(
            r'(<Include href="media_codecs_c2_audio\.xml" />)(?!\s*<Include href="media_codecs_dolby_audio\.xml")',
            r'\1\n    <Include href="media_codecs_dolby_audio.xml" />',
        ),
    # The source WALT scheduler provides migration controls under /proc/sys/walt.
    'vendor/etc/perf/targetresourceconfigs.xml': blob_fixup()
        .regex_replace(
            'MajorValue="0x3" MinorValue="0x7" Supported="no"',
            'MajorValue="0x3" MinorValue="0x7" Node="/proc/sys/walt/sched_upmigrate" Supported="yes"',
        )
        .regex_replace(
            'MajorValue="0x3" MinorValue="0x8" Supported="no"',
            'MajorValue="0x3" MinorValue="0x8" Node="/proc/sys/walt/sched_downmigrate" Supported="yes"',
        ),
    # Let PowerHAL request vertical-scroll boost while perf tracks 30/45 fps.
    'vendor/etc/perf/perfboostsconfig.xml': blob_fixup()
        .regex_replace(
            'Id="0x00001080" Type="1" Enable="true" Target="pineapple" Fps="60"',
            'Id="0x00001080" Type="1" Enable="true" Target="pineapple"',
        ),
    (
        'vendor/etc/media_codecs_pinaepple.xml', 
        'vendor/etc/media_codecs_pinaepple_vendor.xml'
    ): blob_fixup()
        .regex_replace('.*media_codecs_(google_audio|google_c2|google_telephony|google_video|vendor_audio).*\n', ''),
    'vendor/lib64/vendor.libdpmframework.so': blob_fixup()
        .add_needed('libhidlbase_shim.so')
        .add_needed('libbinder_shim.so'),
    (
        'vendor/lib64/libqcc_sdk.so', 
        'vendor/lib64/libqms_xiaomi.so',
        'vendor/lib64/libqms_client.so',
        'vendor/bin/qcc-vendor',
        'vendor/bin/xtra-daemon',
        'vendor/bin/qms',
        'vendor/bin/cnd',
    ): blob_fixup()
        .add_needed('libbinder_shim.so'),
    (
        'vendor/lib64/libaudioroute_ext.so',
        'vendor/lib64/libar-pal.so',
    ): blob_fixup()
        .replace_needed('libaudioroute.so', 'libaudioroute-v34.so'),
    (
        'vendor/lib64/libdlbdsservice.so',
        'vendor/lib64/libdlbpreg.so',
        'vendor/lib64/soundfx/libdlbvol.so',
        'vendor/lib64/soundfx/libhwdap.so',
    ): blob_fixup()
        .add_needed('libstagefright_foundation-v33.so'),
    'vendor/lib64/libqcodec2_core.so': blob_fixup()
        .add_needed('libcodec2_shim.so'),
    (
        'vendor.qti.hardware.display.composer-service',
        'odm/lib64/hw/displayfeature.default.so',
        'vendor/lib64/libsnapdragoncolor-manager.so',
        'vendor/lib64/libdpps.so',
        'vendor/bin/poweropt-service',
    ): blob_fixup()
        .replace_needed('libtinyxml2.so', 'libtinyxml2-v34.so'),
    (
        'vendor/lib64/libVoiceSdk.so',
        'vendor/lib64/libcapiv2uvvendor.so',
        'vendor/lib64/liblistensoundmodel2vendor.so',
    ): blob_fixup()
        .replace_needed('libtensorflowlite_c.so', 'libtensorflowlite_c_vendor.so'),
    (
        'vendor/lib64/libdisplaydebug.so',
    ): blob_fixup()
        .replace_needed('android.hardware.graphics.composer3-V2-ndk.so', 'android.hardware.graphics.composer3-V3-ndk.so'),
    'system_ext/etc/init/qspa_system.rc': blob_fixup()
        .regex_replace(r'\$\{ro\.boot\.vendor\.qspa:-default\}', 'default'),
}  # fmt: skip

module = ExtractUtilsModule(
    'sm8650-common',
    'xiaomi',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
    check_elf=True,
)

if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()
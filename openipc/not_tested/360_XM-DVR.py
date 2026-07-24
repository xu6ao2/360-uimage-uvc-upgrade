#!/usr/bin/env python3

import os
import time
import struct
import zlib


IH_MAGIC = 0x27051956

# OS
IH_OS_LINUX = 5

# ARCH
IH_ARCH_ARM = 2

# TYPE
IH_TYPE_KERNEL = 2
IH_TYPE_RAMDISK = 3
IH_TYPE_MULTI = 4
IH_TYPE_FIRMWARE = 5
IH_TYPE_SCRIPT = 6

# Compression
# This might be wrong
IH_COMP_NONE = 1
IH_COMP_GZIP = 0


def be32(x):
    return struct.pack(">I", x)

def le32(x):
    return struct.pack("<I", x)



def crc32(data):
    return zlib.crc32(data) & 0xffffffff


def make_header(
    payload,
    sp,
    ep,
    image_type,
    name,
    timestamp=0x5ECF84AD,
    comp=IH_COMP_NONE,
    os_type=IH_OS_LINUX,
    arch=IH_ARCH_ARM,
):
    if timestamp is None:
        timestamp = int(time.time())

    dcrc = crc32(payload)

    name = name.encode("ascii")
    name = name[:32]
    name += b"\0" * (32 - len(name))

    #
    # build header with hcrc=0
    #
    hdr = b"".join([
        be32(IH_MAGIC),
        be32(0),
        be32(timestamp),
        be32(len(payload)),
        be32(sp),
        be32(ep),
        be32(dcrc),
        bytes([os_type]),
        bytes([arch]),
        bytes([image_type]),
        bytes([comp]),
        name,
    ])

    hcrc = crc32(hdr)

    hdr = b"".join([
        be32(IH_MAGIC),
        be32(hcrc),
        be32(timestamp),
        be32(len(payload)),
        be32(sp),
        be32(ep),
        be32(dcrc),
        bytes([os_type]),
        bytes([arch]),
        bytes([image_type]),
        bytes([comp]),
        name,
    ])

    return hdr


def make_image(
    payload,
    sp,
    ep,
    image_type,
    name,
    comp=IH_COMP_NONE,
):
    hdr = make_header(
        payload,
        sp,
        ep,
        image_type,
        name,
        comp=comp,
    )
    return hdr + payload


###########################################################################
# XM-DVR container
###########################################################################

def make_xm_container(images):
    """
    images = list of complete uImage blobs (header+payload)
    """

    body = b"".join(images)

    total = 0x40 + len(body)

    hdr = bytearray(64)

    hdr[0:6] = b"XM-DVR"

    # offset to first image
    #hdr[0x14:0x18] = be32(0x40)
    hdr[0x14:0x18] = le32(0x40)
    #error

    # total file size
    hdr[0x18:0x1C] = le32(total)

    return bytes(hdr) + body


###########################################################################
# Example
###########################################################################

if __name__ == "__main__":

    with open("boot","rb") as f:
        uboot = f.read()

    with open("kernel","rb") as f:
        env = f.read()

    with open("romfs","rb") as f:
        kernel = f.read()

    img1 = make_image(
        uboot,
        sp=0x00000000,
        ep=0x00030000,
        image_type=IH_TYPE_FIRMWARE,
        name="uboot",
    )

    img2 = make_image(
        env,
        sp=0x00030000,
        ep=0x00040000,
        image_type=IH_TYPE_FIRMWARE,
        name="env",
    )

    img3 = make_image(
        kernel,
        sp=0x00040000,
        ep=0x00210000,
        image_type=IH_TYPE_KERNEL,
        name="kernel",
    )

#    fw = make_xm_container([
#        img1,
#        img2,
#        img3,
#    ])

    fw = make_xm_container([
        img2,
    ])

    with open("FIRMWARE_AP6PCT01.bin","wb") as f:
        f.write(fw)

    print("done")

#!/usr/bin/env python3
import time
import struct
import zlib

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------

FLASH_OFFSET = 0x000e0000
ERASE_BLOCK  = 0x00020000      # 128 KiB
PAYLOAD = open("nand-env.bin", "rb").read()




# -------------------------------------------------------

PACK_MAGIC = 0x4D541904

# low 2 bits probably encode region count-1
MTPT_MAGIC = 0x4D540701

# erase enough whole blocks
ERASE_SIZE = ((len(PAYLOAD) + ERASE_BLOCK - 1) //
              ERASE_BLOCK) * ERASE_BLOCK

ERASE_END = FLASH_OFFSET + ERASE_SIZE

# -------------------------------------------------------

def u32(x):
    return struct.pack("<I", x & 0xffffffff)


###########new crc32
def reflect_bits(value, width):
    result = 0
    for i in range(width):
        if value & (1 << i):
            result |= 1 << (width - 1 - i)
    return result


# Precompute reflected polynomial (CRC-32 standard reflected form)
_POLY = reflect_bits(0x04C11DB7, 32) >> 0


def crc32(data: bytes) -> int:
    crc = 0x00000000

    for b in data:
        crc ^= b  # reflected => process LSB-first byte

        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ _POLY
            else:
                crc >>= 1

        crc &= 0xFFFFFFFF

    return crc & 0xFFFFFFFF



##time stamp
timestamp = int(time.time())

# Manually swap bytes (from Little to Big, or Big to Little)
swapped_timestamp = (
    ((timestamp & 0xFF000000) >> 24) |
    ((timestamp & 0x00FF0000) >> 8)  |
    ((timestamp & 0x0000FF00) << 8)  |
    ((timestamp & 0x000000FF) << 24)
)

# =======================================================
# MTPT IMAGE
# =======================================================

hdr = [0] * 18

hdr[0] = MTPT_MAGIC

#
# Region descriptor 0
#
hdr[2] = FLASH_OFFSET
hdr[3] = 0 #FLASH_OFFSET is 64bit
hdr[4] = ERASE_END
hdr[5] = 0

#
# Remaining descriptors
#
hdr[6] = hdr[7] = 0
hdr[8] = hdr[9] = 0

#
# Payload information
#
hdr[10] = len(PAYLOAD)
hdr[11] = 0 #len(PAYLOAD) is 64bit

hdr[12] = 0
hdr[13] = 0
hdr[14] = 0
hdr[15] = 0
#hdr[16] = 0
#hdr[16] = 0x6B8B4567
hdr[16] = swapped_timestamp ##might be timestamp

#
# Payload CRC
#
hdr[1] = crc32(PAYLOAD)

#
# Header CRC
#
tmp = b''.join(u32(x) for x in hdr[:17])
hdr[17] = crc32(tmp)

image = b''.join(u32(x) for x in hdr)
image += PAYLOAD

#
# Images are 4-byte aligned
#
while len(image) & 3:
    image += b'\0'


# =======================================================
# PACKAGE
# =======================================================

pack = [0] * 8

pack[0] = PACK_MAGIC
pack[1] = crc32(image)
pack[2] = len(image)
pack[3] = 0
pack[4] = 0
pack[5] = 0
pack[6] = 1            # one image
pack[7] = 0

tmp = b''.join(u32(x) for x in pack[:7])
pack[7] = crc32(tmp)

package = b''.join(u32(x) for x in pack)
package += image

with open("nand-env.mtpt", "wb") as f:
    f.write(package)

print("update.mtpt written")
print("payload size :", len(PAYLOAD))
print("erase size   :", ERASE_SIZE)
print("package size :", len(package))










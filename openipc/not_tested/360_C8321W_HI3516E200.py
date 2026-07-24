import struct
import hashlib




# =========================
# CONFIG
# =========================

#WARING: NEVER BEING TESTED.
MODEL_NAME = "D901"
selected = ["ubootenv","kernel","rootfs","user"]

MODEL = "C8321W_HI3516E200"
##maybe you should also modify the partition table downside and " # timing/config (from dump) " for a different model.

##0x150-0x15b differs for different model, I don't know what it is.
##to know this, maybe u can try binwalk -e uboot, and use binary ninja/ ida /ghidra  rebase it to 0x408000



# fixed sizes based on your dump
HEADER_SIZE = 0x40
HEADER_SIZE_ALL = 0x40000
ALINE_SIZE  = 0x10000
MODEL_FIELD_SIZE = 0x20

# partition table locations (from your structure)
PART_BASE = 0xC0

# =========================
# HELPERS
# =========================
def le32(v):
    return struct.pack("<I", v)

def pad(b, size):
    return b + b"\x00" * (size - len(b))

def cstr(s, size):
    return pad(s.encode(), size)

def align(buf, size):
    if len(buf) < size:
        buf += b"\x00" * (size - len(buf))
    return buf

# =========================
# PARTITION DEFINITIONS
# (keeps correct alignment slots)
# =========================
PARTITIONS = {
    "uboot": {
        "name": "uboot",
        "dev": "/dev/mtdblock0",
    },
    "ubootenv": {
        "name": "ubootenv",
        "dev": "/dev/mtdblock1",
    },
    "kernel": {
        "name": "kernel",
        "dev": "/dev/mtdblock2",
    },
    "rootfs": {
        "name": "rootfs",
        "dev": "/dev/mtdblock3",
    },
    "user": {
        "name": "user",
        "dev": "/dev/mtdblock4",
    },
    "kernel2": {
        "name": "kernel2",
        "dev": "/dev/mtdblock5",
    },
    "rootfs2": {
        "name": "rootfs2",
        "dev": "/dev/mtdblock6",
    },
    "user2": {
        "name": "user2",
        "dev": "/dev/mtdblock7",
    },
    "config": {
        "name": "config",
        "dev": "/dev/mtdblock8",
    },
    "factory": {
        "name": "factory",
        "dev": "/dev/mtdblock9",
    }

}

# =========================
# BUILD HEADER (0x00 - 0x80 safe region)
# =========================
def build_header():
    buf = bytearray()

    # 0x00 - 0x3F zeros
    buf += b"\x00" * HEADER_SIZE

    # 0x40 model string
    buf += cstr(MODEL, MODEL_FIELD_SIZE)

    # pad until 0xC0 (CRITICAL ALIGNMENT FIX)
    buf = align(buf, PART_BASE)

    return buf

# =========================
# BUILD PARTITION BLOCK (0xC0)
# =========================
def build_partitions(selected):
    buf = bytearray()
    partitionmix = bytearray()

    # structure from your dump:
    # uint32 + strings + padding + repeated blocks

    # ---- header values ----
    buf += le32(0x2)
    buf += le32(0x4)
    buf += le32(0xD)

    # ---- block 1 ----
    buf += pad(b"570012", 0x20)
    buf += le32(0x1)
    buf += le32(0x2)
    buf += le32(0x0)

    buf += pad(b"1000", 0x20)
    buf += le32(0x5)
    buf += le32(0x0)
    buf += le32(0x0)

    buf += pad(b"10000", 0x20)

    # timing/config (from dump)
    buf += le32(2020)
    buf += le32(9)
    buf += le32(21)
    buf += le32(0x5)
    buf += le32(0x11)
    buf += le32(0x1F)
    buf += le32(len(selected))

    # ---- partitions ----
    partition_pointer = HEADER_SIZE_ALL
    for key in selected:
        p = PARTITIONS[key]

        partition = open(key, "rb").read()
        partition_alinsize = ((len(partition) + ALINE_SIZE -1) // ALINE_SIZE )* ALINE_SIZE
        partition_alined = bytearray()
        partition_alined += partition
        align(partition_alined , partition_alinsize )

        partitionmix += partition_alined

        buf += cstr(p["name"], 0x20)
        buf += cstr(p["dev"], 0x20)

        buf += le32(0x0)
        buf += le32(len(partition))
        buf += le32(partition_pointer)


        partition_pointer = partition_pointer + partition_alinsize

    align(buf, HEADER_SIZE_ALL - PART_BASE )

    buf += partitionmix
    
    buf[1376:1408] = align(MODEL_NAME.encode('ascii'),0x20)

    return buf

# =========================
# BUILD FULL IMAGE
# =========================
def build_firmware(selected_parts):
    img = bytearray()

    # header
    img += build_header()

    # partition block (0xC0 region)
    img += build_partitions(selected_parts)
    
    md5_hash = hashlib.md5(img).hexdigest()

    img[1664:1696] = align(md5_hash.encode("ascii"),0x20)

    return bytes(img)

# =========================
# MAIN
# =========================
if __name__ == "__main__":

    fw = build_firmware(selected)

    with open("FIRMWARE_" + MODEL_NAME + ".bin" , "wb") as f:
        f.write(fw)

    print("Generated FIRMWARE_" + MODEL_NAME + ".bin")
    print("Size:", len(fw))

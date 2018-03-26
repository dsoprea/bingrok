import sys
import struct
import json

_DEFAULT_SEP_BYTE_COUNT = 8
_DEFAULT_WRAP_BYTE_COUNT = 16

def get_slice(
        f, offset, length=0, unpack_format=None):
    if length == 0:
        if unpack_format is not None:
            length = struct.calcsize(unpack_format)
        else:
            length = _DEFAULT_LENGTH

    f.seek(offset, 0)
    buffer_ = f.read(length)

    return buffer_

def print_unpacked(offset, unpack_info, do_inline=True, do_json=False):
    """Unpack and print the bytes. The format is expected to be colon-separated
    so that we can easily split it and include the formatting characters
    corresponding to each unpacked part.
    """

    if do_json is True:
        print(get_pretty_json([(f, v) for f, df, v in unpack_info]))
    elif do_inline is True:
        phrase = ', '.join(['[{}] [{}]'.format(f, v) for f, df, v in unpack_info])
        print('{:08x}: {}'.format(offset, phrase))
    else:
        print('{:08x}'.format(offset))
        for i, (f, df, v) in enumerate(unpack_info):
            print("  {}: [{}] [{}]".format(i, f, v))

def unpack_buffer(buffer_, unpack_format, do_make_nicer=True):
    # Work through the format one part at a time so that we can easily figure
    # out which slices belogn to which formatting parts.
    format_parts = unpack_format.split(':')

    unpack_info = []
    buffer_offset = 0
    for format_part in format_parts:
        unpacked = struct.unpack_from(format_part, buffer_, buffer_offset)
        buffer_offset += len(unpacked)

        format_part_distilled = distill_part_format(format_part)

        unpacked = \
            distill_unpacked(
                format_part_distilled,
                unpacked,
                do_make_nicer=do_make_nicer)

        unpack_info.append((format_part, format_part_distilled, unpacked))

    return unpack_info

def distill_part_format(part_format):
    """Determine what the type of this particular unpacked part was."""

    # Drop any byte-ordering prefix.
    if part_format[0] in ('@', '=', '<', '>', '!'):
        part_format = part_format[1:]

    # Skip over any repetition count.

    ZERO = ord('0')
    NINE = ord('9')

    i = 0
    while i < len(part_format):
        if ZERO <= ord(part_format[i]) <= NINE:
            i += 1
            continue

        break

    return part_format[i:]

def distill_unpacked(distilled_format, v, do_make_nicer=True):
    if distilled_format == 'c':
        phrases = []

        # It's a byte array.
        for c in v:
            phrases.append('{:02x}'.format(ord(c)))

        if do_make_nicer is True:
            return ' '.join(phrases)
        else:
            return phrases
    else:
        return v

def print_bytes(
        offset, buffer_, wrap_byte_count=_DEFAULT_WRAP_BYTE_COUNT, sep_byte_count=_DEFAULT_SEP_BYTE_COUNT):
    sys.stdout.write("{:08x}".format(offset))
    partial = False
    for i, c in enumerate(buffer_):
        sys.stdout.write(' {:02x}'.format(c))
        if (i + 1) % wrap_byte_count == 0:
            sys.stdout.write('\n')

            offset += wrap_byte_count

            sys.stdout.write("{:08x}".format(offset))

            partial = False
        elif (i + 1) % sep_byte_count == 0:
            sys.stdout.write(' ')
        else:
            partial = True

    if partial is True:
        sys.stdout.write('\n')

def get_pretty_json(data):
    return \
        json.dumps(
            data,
            sort_keys=True,
            indent=4,
            separators=(',', ': '))

def get_unpack_format_size(unpack_format):
    parts = unpack_format.split(':')
    unpack_format_distilled = ''.join(parts)
    return struct.calcsize(unpack_format_distilled)

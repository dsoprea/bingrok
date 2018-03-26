import os
import logging
import sys
import struct
import json

_DEFAULT_SEP_BYTE_COUNT = 8
_DEFAULT_WRAP_BYTE_COUNT = 16

_LOGGER = logging.getLogger(__name__)

def get_slice(
        f, offset, length=0, unpack_format=None):
    if length == 0:
        if unpack_format is not None:
            length = struct.calcsize(unpack_format)
        else:
            length = _DEFAULT_LENGTH

    _LOGGER.debug("Getting slice at offset ({}).".format(offset))

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
    sys.stdout.write("{:08x} ".format(offset))
    for i, c in enumerate(buffer_):
        sys.stdout.write(' {:02x}'.format(c))

        if i + 1 < len(buffer_):
            if (i + 1) % wrap_byte_count == 0:
                sys.stdout.write('\n')

                offset += wrap_byte_count

                sys.stdout.write("{:08x} ".format(offset))
            elif (i + 1) % sep_byte_count == 0:
                sys.stdout.write(' ')

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


class EndOfFileException(Exception):
    pass

def search_bytes(f, len_, search_bytes_list):
    assert \
        len(search_bytes_list), \
        "No search-bytes given."

    is_debug = False

    i = 0

    # We use two separate buffers to make the logic easier to understand.
    buffer_ = []
    old_buffer = []
    while i < len_:
        j = 0
        found = True

        if buffer_:
            if is_debug is True:
                if buffer_:
                    print("SEARCH_BYTES: BUFFER={}".format(buffer_))

            old_buffer = buffer_[:]
            buffer_ = []

        while j < len(search_bytes_list):
            # We started matching at the end of the file, but then ran out of
            # bytes.
            if i + j >= len_:
                raise EndOfFileException("Could not find bytes (1).")

            if is_debug is True:
                print("SEARCH_BYTES: Reading ({})-({})".format(i, j))

            if old_buffer:
                byte_, old_buffer = old_buffer[0], old_buffer[1:]

                if is_debug is True:
                    print("SEARCH_BYTES: Shifted byte off buffer: [{:02x}] "
                          "REMAINING={}".format(byte_, old_buffer))
            else:
                bytes_ = f.read(1)

                if bytes_ == '':
                    raise EndOfFileException("No more data at ({}).".format(i + j))

                byte_ = bytes_[0]

                if is_debug is True:
                    print("SEARCH_BYTES: Read byte from file: "
                          "[{:02x}].".format(byte_))

            # Don't capture the lead-byte (the next inner search will begin on
            # the byte after the one that we started on).
            if j > 0:
                buffer_.append(byte_)

            if byte_ != search_bytes_list[j]:
                found = False

                # If we haven't yet consumed all of the data in the old buffer,
                # append it to the new buffer
                if old_buffer:
                    buffer_ += old_buffer

                if is_debug is True:
                    print("SEARCH_BYTES: - [{:02x}] != [{:02x}]: Not a match. BUFFER={}".format(byte_, search_bytes_list[j], buffer_))

                break
            else:
                if is_debug is True:
                    print("SEARCH_BYTES: - Matched.")

            j += 1

        if found is True:
            if is_debug is True:
                print("SEARCH_BYTES: Found at ({}).".format(i))

            return i

        i += 1

    raise EndOfFileException("Could not find bytes (2).")

def search_bytes_frontend(
        filepath, search_bytes_list, search_start_offset=0, search_max_bytes=None,
        skip_first_matches=0):
    """Wraps higher-level functionaliy around the core binary search."""

    assert \
        skip_first_matches >= 0, \
        "skip_first_matches must be greater-than-or-equal to 0."

    s = os.stat(filepath)
    filesize = s.st_size

    if search_max_bytes is not None:
        len_ = search_max_bytes
    else:
        len_ = filesize

    search_bytes_raw = search_bytes_list
    search_bytes_list = []
    for hex_ in search_bytes_raw:
        search_bytes_list.append(int(hex_, 16))

    with open(filepath, 'rb') as f:
        while skip_first_matches >= 0:
            if search_start_offset > 0 and \
               search_start_offset >= filesize:
                raise Exception("Either not enough matches found or "
                                "starting search offset larger than file.")

            f.seek(search_start_offset, 0)

            effective_length = len_ - search_start_offset
            offset = search_bytes(f, effective_length, search_bytes_list)
            offset += search_start_offset

            # If we want to skip the first N results.
            search_start_offset = offset + 1
            skip_first_matches -= 1

        return offset

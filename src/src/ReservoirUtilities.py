def size_in_bytes(limit):
    # fetch the precision
    precicion = limit[-1]
    size = int(limit[:-1])
    # avoid calculating the conversions all the time
    conversions = {
        'G': 1073741824,
        'M': 1048576,
        'K': 1024,
        'B': 1
    }

    if conversions.has_key(precicion):
        return size * conversions[precicion]
    else:
        return size # return size as number of bytes in case of invalid conversion format
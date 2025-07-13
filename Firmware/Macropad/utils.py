# tahkns google. https://coderivers.org/blog/how-to-map-from-one-range-to-another-using-python/
def map_value(x, src_min, src_max, dst_min, dst_max):
    if src_max < src_min:
        raise ValueError("src_max must be greater than or equal to src_min")
    if dst_max < dst_min:
        raise ValueError("dst_max must be greater than or equal to dst_min")
    if src_max - src_min == 0:
        return dst_min
    return ((x - src_min) / (src_max - src_min)) * (dst_max - dst_min) + dst_min

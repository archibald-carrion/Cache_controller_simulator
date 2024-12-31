def value_to_tuple_le(value, byte_len):
    """
    Converts an integer value to a tuple of bytes in little-endian order.

    Parameters:
    value (int): The integer value to convert.
    byte_len (int): The number of bytes to include in the tuple.

    Returns:
    tuple: A tuple of bytes representing the value in little-endian order.
    """
    if value < 0:
        raise ValueError("Value must be non-negative.")
    if byte_len <= 0:
        raise ValueError("Byte length must be greater than zero.")
    
    result = []
    for _ in range(byte_len):
        result.append(value & 0xFF)  # Extract the least significant byte
        value >>= 8  # Shift right by 8 bits to process the next byte

    return tuple(result)


def tuple_to_value_le(byte_tuple):
    """
    Converts a tuple of bytes in little-endian order to an integer value.

    Parameters:
    byte_tuple (tuple): A tuple of bytes in little-endian order.

    Returns:
    int: The integer value represented by the bytes.
    """
    if not isinstance(byte_tuple, tuple):
        raise ValueError("Input must be a tuple of bytes.")
    
    value = 0
    for i, byte in enumerate(byte_tuple):
        value |= (byte << (8 * i))  # Add the byte shifted by its position
    
    return value

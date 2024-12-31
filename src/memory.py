class Memory:
    def __init__(self):
        # Initialize memory as a dictionary to store address-value pairs
        self.storage = {}

    def write(self, addr, data_tuple):
        """
        Write data to the memory starting from the given address.
        
        Parameters:
        addr (int): The starting address to write the data.
        data_tuple (tuple): A tuple of bytes to be written.
        """
        if not isinstance(data_tuple, tuple):
            raise ValueError("Data must be provided as a tuple of bytes.")
        for offset, byte in enumerate(data_tuple):
            self.storage[addr + offset] = byte

    def read(self, addr, byte_len):
        """
        Read a sequence of bytes from the memory.
        
        Parameters:
        addr (int): The starting address to read from.
        byte_len (int): The number of bytes to read.

        Returns:
        tuple: A tuple containing the read bytes.
        """
        if byte_len <= 0:
            raise ValueError("Number of bytes to read must be greater than zero.")
        data = []
        for offset in range(byte_len):
            # Default to 0 if the address is not in memory
            data.append(self.storage.get(addr + offset, 0))
        return tuple(data)

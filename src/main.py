from constants import Units, MEM_DATA
from dev_util import (Memory, value_to_tuple_le, tuple_to_value_le)
import random
import logging
from datetime import datetime
import sys

# Configure logging to write to both file and console
class DualLogger:
    def __init__(self, filename):
        # Create logger
        self.logger = logging.getLogger('CacheController')
        self.logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(message)s')
        
        # Create file handler
        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def log(self, message):
        self.logger.info(message)

# Initialize global logger
logger = DualLogger(f'cache_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')

class MainMemory:
    def __init__(self):
        self.blocks = 0x20
        self.block_size = 8 * Units.Byte
        self.size = self.blocks * self.block_size
        self.memory = Memory()

        i = 0
        for val in MEM_DATA:
            self.write(i*self.block_size, val, self.block_size)
            i+=1

    def write(self, addr, value, byte_len):
        if addr < 0 or addr >= self.size:
            raise ValueError(f"Memory address out of bounds: 0x{addr:X}")
        self.memory.write(addr, value_to_tuple_le(value, byte_len))

    def read(self, addr, byte_len):
        if addr < 0 or addr >= self.size:
            raise ValueError(f"Memory address out of bounds: 0x{addr:X}")
        try:
            return tuple_to_value_le(self.memory.read(addr, byte_len))
        except Exception as e:
            logger.log(f"Error reading from memory at address 0x{addr:X}: {str(e)}")
            return 0

class Cache(MainMemory):
    def __init__(self):
        self.blocks = 5
        self.block_size = 10 * Units.Byte
        self.size = self.blocks * self.block_size
        self.memory = Memory()

class CacheController:
    def __init__(self):
        header = "\n" + "="*50
        logger.log(header)
        logger.log("[CACHE CONTROLLER] Cache Controller Initializer")
        logger.log("[CACHE CONTROLLER] Cache size: 5 blocks")
        logger.log("[CACHE CONTROLLER] Memory size: 32 blocks")
        logger.log("="*50 + "\n")
        
        self.cache = Cache()
        self.memory = MainMemory()
        self.access_frequency = {}
        self.address_mapping = {}
        self.cache_data = {}
        self.used_blocks = 0
        self.total_accesses = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def find_lfu_block(self):
        logger.log("\nFinding LFU block:")
        logger.log("Current access frequencies:")
        for block, freq in self.access_frequency.items():
            logger.log(f"Cache block {block}: {freq} accesses")
            
        min_freq = float('inf')
        lfu_block = None
        
        for block in range(self.cache.blocks):
            freq = self.access_frequency.get(block, 0)
            if freq < min_freq:
                min_freq = freq
                lfu_block = block
        
        logger.log(f"Selected block {lfu_block} with frequency {min_freq} for replacement")
        return lfu_block

    def update_frequency(self, cache_block):
        old_freq = self.access_frequency.get(cache_block, 0)
        self.access_frequency[cache_block] = old_freq + 1
        logger.log(f"Updated access frequency for block {cache_block}: {old_freq} -> {old_freq + 1}")

    def print_cache_state(self):
        logger.log("\nCurrent Cache State:")
        logger.log("-" * 60)
        logger.log("Block | Memory Block | Frequency | Data")
        logger.log("-" * 60)
        for block in range(self.cache.blocks):
            mem_block = "Empty"
            freq = 0
            data = "None"
            
            for addr, cache_block in self.address_mapping.items():
                if cache_block == block:
                    mem_block = f"0x{addr*8:X}"
                    freq = self.access_frequency.get(block, 0)
                    data = f"0x{self.cache_data.get(block, 0):X}"
                    break
                    
            logger.log(f"{block:5} | {mem_block:11} | {freq:9} | {data}")
        logger.log("-" * 60)

    def print_statistics(self):
        logger.log("\nCache Statistics:")
        logger.log("-" * 40)
        logger.log(f"Total accesses: {self.total_accesses}")
        logger.log(f"Cache hits: {self.cache_hits}")
        logger.log(f"Cache misses: {self.cache_misses}")
        if self.total_accesses > 0:
            hit_rate = (self.cache_hits / self.total_accesses) * 100
            logger.log(f"Hit rate: {hit_rate:.2f}%")
        logger.log("-" * 40)

    def read(self, addr, byte_len):
        logger.log("\n" + "="*50)
        logger.log(f"Reading address 0x{addr:X}")
        logger.log("="*50)
        
        self.total_accesses += 1
        block_addr = addr // (8 * Units.Byte)
        
        logger.log(f"Address 0x{addr:X} is mapped to block address: {block_addr}")
        
        is_in_cache = block_addr in self.address_mapping
        if is_in_cache:
            self.cache_hits += 1
            cache_block = self.address_mapping[block_addr]
            self.update_frequency(cache_block)
            logger.log(f"\n✅ Cache hit")
            logger.log(f"Found data in cache block {cache_block}")
            self.print_cache_state()
            return self.cache_data[cache_block]

        self.cache_misses += 1
        logger.log(f"\n❌ Cache miss")
        logger.log(f"Block {block_addr} not found in cache")
        data = self.memory.read(addr, byte_len)
        logger.log(f"Read data from memory: 0x{data:X}")

        is_cache_full = self.used_blocks >= self.cache.blocks
        if not is_cache_full:
            cache_block = self.used_blocks
            self.used_blocks += 1
            logger.log(f"\nUsing new cache block {cache_block}")
        else:
            logger.log("\nCache is full\nUsing LFU replacement policy to find new block")
            cache_block = self.find_lfu_block()
            old_addr = None
            for addr, block in self.address_mapping.items():
                if block == cache_block:
                    old_addr = addr
                    break
            if old_addr is not None:
                logger.log(f"Freeing block {old_addr} from cache block {cache_block}")
                del self.address_mapping[old_addr]

        logger.log(f"\nUpdating cache:")
        logger.log(f"* Mapping memory block {block_addr} to cache block {cache_block}")
        self.address_mapping[block_addr] = cache_block
        self.cache_data[cache_block] = data
        self.access_frequency[cache_block] = 1
        
        self.cache.write(cache_block * self.cache.block_size, block_addr, 2)
        self.cache.write(cache_block * self.cache.block_size + 2, data, 8)
        
        self.print_cache_state()
        self.print_statistics()
        return data

def run_random_access_test(controller, num_query=15):
    logger.log("\n" + "="*70)
    logger.log("Starting Random Data Query Sequence")
    logger.log("="*70)
    
    used_addresses = []
    
    max_block = controller.memory.blocks - 1
    # Get the maximum valid block number from MainMemory
    max_valid_address = 160 # 20 blocks * 8 bytes/block = 160 bytes
    
    for i in range(num_query):
        logger.log(f"\nTest query #{i+1}")
        logger.log("-" * 30)
        
        try:
            if used_addresses and random.random() < 0.5:
                addr = random.choice(used_addresses)
                logger.log("Reusing previous address")
            else:
                # Ensure generated address is within bounds
                addr = random.randint(0, max_block) * controller.memory.block_size
                used_addresses.append(addr)
                logger.log(f"Generated new random address (max valid: 0x{max_valid_address:X})")

            # Additional bounds check before reading
            if addr < 0 or addr > max_valid_address:
                raise ValueError(f"Generated address 0x{addr:X} is out of bounds [0x0-0x{max_valid_address:X}]")

            data = controller.read(addr, controller.memory.block_size)
            logger.log(f"Retrieved data: 0x{data:X}")

        except ValueError as e:
            logger.log(f"Error: {str(e)}")
            continue
        except Exception as e:
            logger.log(f"Unexpected error: {str(e)}")
            continue
    
    logger.log("\n" + "="*70)
    logger.log("Random Data Query Sequence Complete")
    logger.log("Final Statistics:")
    controller.print_statistics()
    logger.log("="*70)


    
if __name__ == "__main__":
    logger.log("\n Cache Controller Demo with Random Data Query Testing")
    logger.log("="*70)
    controller = CacheController()
    run_random_access_test(controller, 50)

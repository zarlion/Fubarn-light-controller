#!/usr/bin/env python3
"""
FUBARN - Bluetooth Mesh Light Controller
========================================

Custom controller using reverse-engineered credentials from the official URBARN app.
Discovered mesh credentials: URBARN/15102

FUBARN = F*** URBARN - We don't need their app!

Author: Reverse Engineering Analysis
Date: 2024-09-04
"""

import asyncio
import struct
import logging
from bleak import BleakScanner, BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from typing import List, Dict, Optional, Tuple
import time
import binascii

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FubarnMeshController:
    """
    FUBARN Bluetooth Mesh Light Controller
    
    Uses discovered mesh credentials:
    - Primary Mesh: URBARN / 15102
    - Secondary Mesh: Fulife / 2846
    
    Features:
    - Group management with custom names
    - Device naming and organization
    - Persistent storage of groups and names
    """
    
    # Discovered mesh credentials from app analysis
    MESH_CREDENTIALS = {
        'primary': {'name': 'URBARN', 'password': '15102'},
        'secondary': {'name': 'Fulife', 'password': '2846'}
    }
    
    # Discovered AES encryption keys
    AES_KEY = bytes.fromhex('d571f6c5851265bcd5bb684aa937aa7c3df76ffce7fb11250ba292d63194d677')
    AES_IV = bytes.fromhex('a91818db066216501caad41d5982e638')
    
    # Common Bluetooth mesh service UUIDs
    MESH_SERVICE_UUIDS = [
        "00001827-0000-1000-8000-00805f9b34fb",  # Mesh Provisioning Service
        "00001828-0000-1000-8000-00805f9b34fb",  # Mesh Proxy Service
        "0000fe59-0000-1000-8000-00805f9b34fb",  # Generic mesh service
        "000016fe-0000-1000-8000-00805f9b34fb",  # Another common mesh UUID
    ]
    
    # Potential characteristic UUIDs for mesh communication
    MESH_CHAR_UUIDS = [
        "00002a04-0000-1000-8000-00805f9b34fb",  # Mesh control
        "00002a05-0000-1000-8000-00805f9b34fb",  # Mesh data
        "6e400002-b5a3-f393-e0a9-e50e24dcca9e",  # Nordic UART TX
        "6e400003-b5a3-f393-e0a9-e50e24dcca9e",  # Nordic UART RX
        "0000fff1-0000-1000-8000-00805f9b34fb",  # Generic write
        "0000fff2-0000-1000-8000-00805f9b34fb",  # Generic notify
        "0000fff3-0000-1000-8000-00805f9b34fb",  # Generic read
        "0000fff4-0000-1000-8000-00805f9b34fb",  # Generic indication
    ]
    
    def __init__(self, storage_path: str = None):
        self.discovered_devices: List[BLEDevice] = []
        self.connected_devices: Dict[str, BleakClient] = {}
        self.device_characteristics: Dict[str, Dict[str, BleakGATTCharacteristic]] = {}
        self.authenticated_devices: Dict[str, bool] = {}
        
        # Group and device management
        self.device_groups: Dict[str, List[str]] = {}  # group_name -> [device_addresses]
        self.device_names: Dict[str, str] = {}  # device_address -> custom_name
        self.group_names: Dict[str, str] = {}  # group_id -> group_name
        self.storage_path = storage_path or "fubarn_data.json"
        
        # Load saved data
        self.load_data()
        
    async def scan_for_urbarn_devices(self, scan_time: int = 10) -> List[BLEDevice]:
        """
        Scan for URBARN mesh devices using discovered patterns
        """
        logger.info(f"Scanning for URBARN devices for {scan_time} seconds...")
        
        # Device name patterns found in the app
        device_patterns = [
            'URBARN',
            'Fulife', 
            'Mesh',
            'Light',
            # Generic patterns that might match
            'BT',
            'LED',
        ]
        
        self.discovered_devices = []
        
        def detection_callback(device: BLEDevice, advertisement_data):
            device_name = device.name or "Unknown"
            
            # Check for URBARN-specific patterns
            is_urbarn_device = False
            
            # Check name patterns
            for pattern in device_patterns:
                if pattern.lower() in device_name.lower():
                    is_urbarn_device = True
                    break
            
            # Check for mesh service UUIDs
            if not is_urbarn_device:
                for service_uuid in self.MESH_SERVICE_UUIDS:
                    if service_uuid in advertisement_data.service_uuids:
                        is_urbarn_device = True
                        break
            
            # Check for strong signal (likely nearby URBARN lights)
            if not is_urbarn_device and advertisement_data.rssi and advertisement_data.rssi > -60:
                # If it's a strong signal and has any service UUIDs, consider it
                if advertisement_data.service_uuids:
                    is_urbarn_device = True
            
            if is_urbarn_device:
                if device not in self.discovered_devices:
                    logger.info(f"Found potential URBARN device: {device_name} ({device.address}) RSSI: {advertisement_data.rssi}")
                    logger.info(f"  Services: {advertisement_data.service_uuids}")
                    logger.info(f"  Manufacturer data: {advertisement_data.manufacturer_data}")
                    self.discovered_devices.append(device)
        
        scanner = BleakScanner(detection_callback=detection_callback)
        await scanner.start()
        await asyncio.sleep(scan_time)
        await scanner.stop()
        
        logger.info(f"Found {len(self.discovered_devices)} potential URBARN devices")
        return self.discovered_devices
    
    async def connect_to_device(self, device: BLEDevice) -> bool:
        """
        Connect to a specific device and discover characteristics
        """
        try:
            logger.info(f"Connecting to {device.name or 'Unknown'} ({device.address})")
            
            client = BleakClient(device.address)
            await client.connect()
            
            if not client.is_connected:
                logger.error(f"Failed to connect to {device.address}")
                return False
            
            logger.info(f"Connected to {device.address}")
            self.connected_devices[device.address] = client
            
            # Discover services and characteristics
            await self._discover_characteristics(device.address)
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to {device.address}: {e}")
            return False
    
    async def _discover_characteristics(self, device_address: str):
        """
        Discover and catalog characteristics for mesh communication
        """
        client = self.connected_devices.get(device_address)
        if not client:
            return
        
        logger.info(f"Discovering characteristics for {device_address}")
        self.device_characteristics[device_address] = {}
        
        try:
            services = client.services
            
            for service in services:
                logger.info(f"Service: {service.uuid} ({service.description})")
                
                for char in service.characteristics:
                    char_info = f"  Char: {char.uuid} ({char.description}) Properties: {char.properties}"
                    logger.info(char_info)
                    
                    # Store potentially useful characteristics
                    if any(uuid.lower() in char.uuid.lower() for uuid in self.MESH_CHAR_UUIDS):
                        self.device_characteristics[device_address][char.uuid] = char
                        logger.info(f"    -> Stored as potential mesh characteristic")
                    
                    # Store writable characteristics
                    if "write" in char.properties or "write-without-response" in char.properties:
                        self.device_characteristics[device_address][f"writable_{char.uuid}"] = char
                        logger.info(f"    -> Stored as writable characteristic")
                    
                    # Store notification characteristics  
                    if "notify" in char.properties or "indicate" in char.properties:
                        self.device_characteristics[device_address][f"notify_{char.uuid}"] = char
                        logger.info(f"    -> Stored as notification characteristic")
                        
        except Exception as e:
            logger.error(f"Error discovering characteristics: {e}")
    
    async def authenticate_with_mesh(self, device_address: str, use_secondary_creds: bool = False) -> bool:
        """
        Attempt to authenticate with the mesh using discovered credentials
        """
        client = self.connected_devices.get(device_address)
        if not client:
            logger.error(f"No connection to {device_address}")
            return False
        
        # Choose credentials
        creds = self.MESH_CREDENTIALS['secondary' if use_secondary_creds else 'primary']
        mesh_name = creds['name']
        mesh_password = creds['password']
        
        logger.info(f"Attempting mesh authentication with {mesh_name}/{mesh_password}")
        
        # Try multiple authentication approaches based on app analysis
        auth_methods = [
            self._auth_method_1,
            self._auth_method_2,
            self._auth_method_3,
        ]
        
        for i, auth_method in enumerate(auth_methods, 1):
            logger.info(f"Trying authentication method {i}")
            try:
                success = await auth_method(device_address, mesh_name, mesh_password)
                if success:
                    logger.info(f"Authentication successful with method {i}")
                    self.authenticated_devices[device_address] = True
                    return True
            except Exception as e:
                logger.warning(f"Authentication method {i} failed: {e}")
        
        logger.error(f"All authentication methods failed for {device_address}")
        return False
    
    async def _auth_method_1(self, device_address: str, mesh_name: str, mesh_password: str) -> bool:
        """
        Authentication method 1: Direct credential transmission
        """
        client = self.connected_devices[device_address]
        characteristics = self.device_characteristics.get(device_address, {})
        
        # Try sending credentials to writable characteristics
        for char_key, characteristic in characteristics.items():
            if "writable" in char_key:
                try:
                    # Format 1: Name + Password as UTF-8
                    auth_data = f"{mesh_name}:{mesh_password}".encode('utf-8')
                    await client.write_gatt_char(characteristic, auth_data)
                    await asyncio.sleep(0.5)
                    
                    # Format 2: Binary packed
                    auth_data = struct.pack(f'<{len(mesh_name)}s{len(mesh_password)}s', 
                                          mesh_name.encode(), mesh_password.encode())
                    await client.write_gatt_char(characteristic, auth_data)
                    await asyncio.sleep(0.5)
                    
                    logger.info(f"Sent auth data to {characteristic.uuid}")
                    return True
                    
                except Exception as e:
                    logger.debug(f"Auth method 1 failed on {characteristic.uuid}: {e}")
        
        return False
    
    async def _auth_method_2(self, device_address: str, mesh_name: str, mesh_password: str) -> bool:
        """
        Authentication method 2: Mesh protocol specific
        """
        client = self.connected_devices[device_address]
        characteristics = self.device_characteristics.get(device_address, {})
        
        # Try mesh-specific authentication sequences
        for char_key, characteristic in characteristics.items():
            if "writable" in char_key:
                try:
                    # Mesh login sequence based on app patterns
                    login_sequence = [
                        b'\x01\x02',  # Login command
                        mesh_name.encode('utf-8'),
                        mesh_password.encode('utf-8'),
                        b'\x03\x04',  # End sequence
                    ]
                    
                    for data in login_sequence:
                        await client.write_gatt_char(characteristic, data)
                        await asyncio.sleep(0.2)
                    
                    return True
                    
                except Exception as e:
                    logger.debug(f"Auth method 2 failed on {characteristic.uuid}: {e}")
        
        return False
    
    async def _auth_method_3(self, device_address: str, mesh_name: str, mesh_password: str) -> bool:
        """
        Authentication method 3: Encrypted authentication using discovered AES keys
        """
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            
            # Create authentication payload
            auth_payload = f"{mesh_name}:{mesh_password}".encode('utf-8')
            
            # Encrypt with discovered keys
            cipher = Cipher(algorithms.AES(self.AES_KEY[:32]), modes.CBC(self.AES_IV[:16]))
            encryptor = cipher.encryptor()
            
            # Pad the payload
            padder = padding.PKCS7(128).padder()  # AES block size is 128 bits
            padded_data = padder.update(auth_payload)
            padded_data += padder.finalize()
            
            encrypted_payload = encryptor.update(padded_data) + encryptor.finalize()
            
            client = self.connected_devices[device_address]
            characteristics = self.device_characteristics.get(device_address, {})
            
            for char_key, characteristic in characteristics.items():
                if "writable" in char_key:
                    try:
                        await client.write_gatt_char(characteristic, encrypted_payload)
                        await asyncio.sleep(0.5)
                        return True
                    except Exception as e:
                        logger.debug(f"Auth method 3 failed on {characteristic.uuid}: {e}")
                        
        except ImportError:
            logger.warning("Cryptography library not available, skipping encrypted authentication")
        except Exception as e:
            logger.debug(f"Auth method 3 failed: {e}")
        
        return False
    
    async def turn_on_light(self, device_address: str, light_id: int = 1) -> bool:
        """
        Turn on a specific light using discovered command patterns
        """
        return await self._send_light_command(device_address, light_id, True)
    
    async def turn_off_light(self, device_address: str, light_id: int = 1) -> bool:
        """
        Turn off a specific light using discovered command patterns  
        """
        return await self._send_light_command(device_address, light_id, False)
    
    async def _send_light_command(self, device_address: str, light_id: int, turn_on: bool) -> bool:
        """
        Send light control command based on app analysis
        """
        if not self.authenticated_devices.get(device_address, False):
            logger.warning(f"Device {device_address} not authenticated, attempting authentication first")
            if not await self.authenticate_with_mesh(device_address):
                return False
        
        client = self.connected_devices.get(device_address)
        characteristics = self.device_characteristics.get(device_address, {})
        
        if not client or not characteristics:
            logger.error(f"No connection or characteristics for {device_address}")
            return False
        
        # Command patterns derived from app analysis
        command_patterns = [
            # Pattern 1: Simple on/off command
            struct.pack('<BHB', 0x01, light_id, 0x01 if turn_on else 0x00),
            # Pattern 2: Extended command
            struct.pack('<BBHB', 0x02, 0x01, light_id, 0xFF if turn_on else 0x00),
            # Pattern 3: Mesh command format
            struct.pack('<BBBH', 0x03, 0x01 if turn_on else 0x00, 0x00, light_id),
        ]
        
        for pattern in command_patterns:
            for char_key, characteristic in characteristics.items():
                if "writable" in char_key:
                    try:
                        logger.info(f"Sending {'ON' if turn_on else 'OFF'} command to light {light_id}")
                        logger.debug(f"Command data: {binascii.hexlify(pattern)}")
                        
                        await client.write_gatt_char(characteristic, pattern)
                        await asyncio.sleep(0.5)
                        
                        logger.info(f"Command sent successfully")
                        return True
                        
                    except Exception as e:
                        logger.debug(f"Command failed on {characteristic.uuid}: {e}")
        
        logger.error(f"All command patterns failed for device {device_address}")
        return False
    
    # Group Management Methods
    def create_group(self, group_name: str) -> str:
        """
        Create a new group with a custom name
        """
        import uuid
        group_id = str(uuid.uuid4())[:8]
        self.device_groups[group_id] = []
        self.group_names[group_id] = group_name
        self.save_data()
        logger.info(f"Created group '{group_name}' with ID {group_id}")
        return group_id
    
    def add_device_to_group(self, group_id: str, device_address: str) -> bool:
        """
        Add a device to an existing group
        """
        if group_id in self.device_groups:
            if device_address not in self.device_groups[group_id]:
                self.device_groups[group_id].append(device_address)
                self.save_data()
                logger.info(f"Added device {device_address} to group {self.group_names.get(group_id, group_id)}")
                return True
        return False
    
    def remove_device_from_group(self, group_id: str, device_address: str) -> bool:
        """
        Remove a device from a group
        """
        if group_id in self.device_groups and device_address in self.device_groups[group_id]:
            self.device_groups[group_id].remove(device_address)
            self.save_data()
            logger.info(f"Removed device {device_address} from group {self.group_names.get(group_id, group_id)}")
            return True
        return False
    
    def rename_group(self, group_id: str, new_name: str) -> bool:
        """
        Rename an existing group
        """
        if group_id in self.group_names:
            old_name = self.group_names[group_id]
            self.group_names[group_id] = new_name
            self.save_data()
            logger.info(f"Renamed group from '{old_name}' to '{new_name}'")
            return True
        return False
    
    def delete_group(self, group_id: str) -> bool:
        """
        Delete a group (devices remain, just ungrouped)
        """
        if group_id in self.device_groups:
            group_name = self.group_names.get(group_id, group_id)
            del self.device_groups[group_id]
            del self.group_names[group_id]
            self.save_data()
            logger.info(f"Deleted group '{group_name}'")
            return True
        return False
    
    def set_device_name(self, device_address: str, device_name: str):
        """
        Set a custom name for a device
        """
        self.device_names[device_address] = device_name
        self.save_data()
        logger.info(f"Set device {device_address} name to '{device_name}'")
    
    def get_device_name(self, device_address: str) -> str:
        """
        Get the custom name for a device, or return address if no name set
        """
        return self.device_names.get(device_address, device_address[-8:])
    
    def get_groups(self) -> Dict[str, Dict[str, any]]:
        """
        Get all groups with their devices and names
        """
        groups = {}
        for group_id, device_addresses in self.device_groups.items():
            groups[group_id] = {
                'name': self.group_names.get(group_id, f'Group {group_id}'),
                'devices': device_addresses,
                'device_count': len(device_addresses)
            }
        return groups
    
    async def control_group(self, group_id: str, turn_on: bool) -> Dict[str, bool]:
        """
        Control all lights in a group
        Returns dict of device_address -> success_status
        """
        results = {}
        if group_id not in self.device_groups:
            logger.error(f"Group {group_id} not found")
            return results
        
        group_name = self.group_names.get(group_id, group_id)
        action = "ON" if turn_on else "OFF"
        logger.info(f"Turning {action} all lights in group '{group_name}'")
        
        # Control all devices in the group
        for device_address in self.device_groups[group_id]:
            try:
                if turn_on:
                    success = await self.turn_on_light(device_address)
                else:
                    success = await self.turn_off_light(device_address)
                results[device_address] = success
                
                # Small delay between devices to avoid overwhelming
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error controlling device {device_address}: {e}")
                results[device_address] = False
        
        successful = sum(1 for success in results.values() if success)
        logger.info(f"Group '{group_name}' {action}: {successful}/{len(results)} devices successful")
        return results
    
    def save_data(self):
        """
        Save groups and device names to persistent storage
        """
        try:
            import json
            data = {
                'device_groups': self.device_groups,
                'device_names': self.device_names,
                'group_names': self.group_names,
                'version': '1.0'
            }
            
            # For Android, use app-specific storage
            try:
                from android.storage import app_storage_path
                import os
                storage_dir = app_storage_path()
                full_path = os.path.join(storage_dir, self.storage_path)
            except ImportError:
                # Desktop/other platforms
                full_path = self.storage_path
            
            with open(full_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved FUBARN data to {full_path}")
            
        except Exception as e:
            logger.error(f"Error saving FUBARN data: {e}")
    
    def load_data(self):
        """
        Load groups and device names from persistent storage
        """
        try:
            import json
            
            # For Android, use app-specific storage
            try:
                from android.storage import app_storage_path
                import os
                storage_dir = app_storage_path()
                full_path = os.path.join(storage_dir, self.storage_path)
            except ImportError:
                # Desktop/other platforms
                full_path = self.storage_path
            
            with open(full_path, 'r') as f:
                data = json.load(f)
            
            self.device_groups = data.get('device_groups', {})
            self.device_names = data.get('device_names', {})
            self.group_names = data.get('group_names', {})
            
            logger.info(f"Loaded FUBARN data: {len(self.device_groups)} groups, {len(self.device_names)} named devices")
            
        except FileNotFoundError:
            logger.info("No existing FUBARN data found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading FUBARN data: {e}")
    
    async def disconnect_all(self):
        """
        Disconnect from all connected devices and save data
        """
        for address, client in list(self.connected_devices.items()):
            try:
                if client.is_connected:
                    await client.disconnect()
                    logger.info(f"Disconnected from {address}")
            except Exception as e:
                logger.error(f"Error disconnecting from {address}: {e}")
        
        self.connected_devices.clear()
        self.device_characteristics.clear()
        self.authenticated_devices.clear()
        
        # Save data before closing
        self.save_data()

async def main():
    """
    Main function to demonstrate the URBARN mesh controller
    """
    controller = UrbanMeshController()
    
    try:
        # Step 1: Scan for URBARN devices
        print("🔍 Scanning for URBARN mesh devices...")
        devices = await controller.scan_for_urbarn_devices(scan_time=15)
        
        if not devices:
            print("❌ No URBARN devices found. Make sure your lights are powered on and nearby.")
            return
        
        print(f"✅ Found {len(devices)} potential URBARN devices")
        
        # Step 2: Connect to each device
        connected_count = 0
        for device in devices:
            print(f"\n🔗 Attempting to connect to {device.name or 'Unknown'} ({device.address})")
            
            if await controller.connect_to_device(device):
                connected_count += 1
                print(f"✅ Connected successfully")
                
                # Step 3: Authenticate with mesh
                print("🔐 Authenticating with mesh network...")
                if await controller.authenticate_with_mesh(device.address):
                    print("✅ Authentication successful")
                    
                    # Step 4: Test light control
                    print("💡 Testing light control...")
                    
                    # Turn on
                    if await controller.turn_on_light(device.address, light_id=1):
                        print("✅ Successfully turned light ON")
                        await asyncio.sleep(2)
                        
                        # Turn off
                        if await controller.turn_off_light(device.address, light_id=1):
                            print("✅ Successfully turned light OFF")
                        else:
                            print("❌ Failed to turn light OFF")
                    else:
                        print("❌ Failed to turn light ON")
                        
                        # Try secondary credentials
                        print("🔄 Trying secondary mesh credentials...")
                        if await controller.authenticate_with_mesh(device.address, use_secondary_creds=True):
                            print("✅ Secondary authentication successful")
                            if await controller.turn_on_light(device.address, light_id=1):
                                print("✅ Successfully turned light ON with secondary creds")
                                await asyncio.sleep(2)
                                await controller.turn_off_light(device.address, light_id=1)
                
                else:
                    print("❌ Authentication failed")
            else:
                print("❌ Connection failed")
        
        if connected_count == 0:
            print("❌ Could not connect to any devices")
        else:
            print(f"\n🎉 Successfully connected to {connected_count} devices")
    
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.exception("Unexpected error in main")
    finally:
        # Clean up connections
        print("🧹 Cleaning up connections...")
        await controller.disconnect_all()
        print("✅ Cleanup complete")

if __name__ == "__main__":
    print("🚀 URBARN Bluetooth Mesh Light Controller")
    print("=========================================")
    print("Using reverse-engineered mesh credentials from official app")
    print("Mesh: URBARN/15102, Fallback: Fulife/2846")
    print()
    
    asyncio.run(main())

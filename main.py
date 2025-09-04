#!/usr/bin/env python3
"""
FUBARN - Android Light Controller
=================================

Mobile Android app for controlling URBARN Bluetooth mesh lights.
Built with Kivy and using reverse-engineered credentials.

FUBARN = F*** URBARN - We don't need their app!

Author: Reverse Engineering Analysis
Date: 2025-01-04
"""

import asyncio
from threading import Thread
import logging
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock, mainthread
from kivy.logger import Logger
import time

# Import our mesh controller
try:
    from urbarn_mesh_controller import FubarnMeshController
except ImportError:
    Logger.error("FUBARN: Failed to import FubarnMeshController")
    FubarnMeshController = None

# Configure logging for Android
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FubarnApp(App):
    """
    Main Android app for FUBARN light control
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if FubarnMeshController is None:
            raise Exception("FubarnMeshController not available")
        self.controller = FubarnMeshController()
        self.discovered_devices = []
        self.connected_devices = {}
        self.loop = None
        self.loop_thread = None
        
        # UI references
        self.status_label = None
        self.device_layout = None
        self.scan_button = None
        self.main_layout = None
        
    def build(self):
        """
        Build the main UI
        """
        self.title = "FUBARN Light Controller"
        
        # Main layout
        self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title = Label(
            text='🚀 FUBARN Light Controller',
            size_hint_y=None,
            height='48dp',
            font_size='20sp',
            bold=True
        )
        self.main_layout.add_widget(title)
        
        # Status label
        self.status_label = Label(
            text='Ready to scan for URBARN devices...',
            size_hint_y=None,
            height='40dp',
            text_size=(None, None)
        )
        self.main_layout.add_widget(self.status_label)
        
        # Control buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp', spacing=5)
        
        self.scan_button = Button(
            text='🔍 Scan',
            size_hint_x=0.3
        )
        self.scan_button.bind(on_press=self.on_scan_pressed)
        button_layout.add_widget(self.scan_button)
        
        groups_button = Button(
            text='📋 Groups',
            size_hint_x=0.3
        )
        groups_button.bind(on_press=self.show_groups)
        button_layout.add_widget(groups_button)
        
        refresh_button = Button(
            text='🔄 Refresh',
            size_hint_x=0.2
        )
        refresh_button.bind(on_press=self.on_refresh_pressed)
        button_layout.add_widget(refresh_button)
        
        about_button = Button(
            text='ℹ️',
            size_hint_x=0.2
        )
        about_button.bind(on_press=self.show_about)
        button_layout.add_widget(about_button)
        
        self.main_layout.add_widget(button_layout)
        
        # Scrollable device list
        scroll = ScrollView()
        self.device_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.device_layout.bind(minimum_height=self.device_layout.setter('height'))
        scroll.add_widget(self.device_layout)
        
        self.main_layout.add_widget(scroll)
        
        # Start asyncio loop in background thread
        self.start_async_loop()
        
        return self.main_layout
    
    def start_async_loop(self):
        """
        Start asyncio event loop in background thread
        """
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
            
        self.loop_thread = Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        
        # Wait for loop to be ready
        while self.loop is None:
            time.sleep(0.01)
    
    @mainthread
    def update_status(self, message):
        """
        Update status label on main thread
        """
        if self.status_label:
            self.status_label.text = message
            Logger.info(f"URBARN: {message}")
    
    def on_scan_pressed(self, button):
        """
        Handle scan button press
        """
        if self.loop and not self.loop.is_closed():
            # Disable button during scan
            button.disabled = True
            button.text = "🔍 Scanning..."
            
            # Run scan in async loop
            asyncio.run_coroutine_threadsafe(
                self.scan_for_devices_async(button), 
                self.loop
            )
    
    async def scan_for_devices_async(self, button):
        """
        Async method to scan for devices
        """
        try:
            self.update_status("🔍 Scanning for URBARN devices...")
            
            # Clear previous devices
            self.discovered_devices = []
            Clock.schedule_once(lambda dt: self.clear_device_list(), 0)
            
            # Scan for devices
            devices = await self.controller.scan_for_urbarn_devices(scan_time=10)
            
            if devices:
                self.discovered_devices = devices
                self.update_status(f"✅ Found {len(devices)} URBARN devices")
                
                # Add devices to UI
                Clock.schedule_once(lambda dt: self.populate_device_list(), 0)
                
            else:
                self.update_status("❌ No URBARN devices found. Make sure lights are on and nearby.")
                
        except Exception as e:
            self.update_status(f"❌ Scan error: {str(e)}")
            Logger.error(f"URBARN: Scan error: {e}")
        
        finally:
            # Re-enable button
            Clock.schedule_once(lambda dt: self.reset_scan_button(button), 0)
    
    @mainthread
    def reset_scan_button(self, button):
        """
        Reset scan button state
        """
        button.disabled = False
        button.text = "🔍 Scan for Devices"
    
    @mainthread
    def clear_device_list(self):
        """
        Clear device list UI
        """
        self.device_layout.clear_widgets()
    
    @mainthread  
    def populate_device_list(self):
        """
        Populate device list in UI
        """
        self.device_layout.clear_widgets()
        
        for device in self.discovered_devices:
            device_widget = self.create_device_widget(device)
            self.device_layout.add_widget(device_widget)
    
    def create_device_widget(self, device):
        """
        Create a widget for a discovered device with enhanced features
        """
        layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='100dp', spacing=5)
        
        # Device info
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.5)
        
        # Get custom name or use default
        device_name = self.controller.get_device_name(device.address)
        name_label = Label(
            text=f"📡 {device_name}",
            size_hint_y=None,
            height='25dp',
            text_size=(None, None),
            font_size='13sp',
            bold=True
        )
        info_layout.add_widget(name_label)
        
        addr_label = Label(
            text=f"📍 {device.address[-8:]}",
            size_hint_y=None, 
            height='20dp',
            text_size=(None, None),
            font_size='10sp'
        )
        info_layout.add_widget(addr_label)
        
        # Connection status
        is_connected = device.address in self.connected_devices
        status_label = Label(
            text=f"🔌 Connected" if is_connected else "🔴 Disconnected",
            size_hint_y=None,
            height='20dp',
            text_size=(None, None),
            font_size='9sp',
            color=(0, 1, 0, 1) if is_connected else (1, 0.5, 0, 1)
        )
        info_layout.add_widget(status_label)
        
        layout.add_widget(info_layout)
        
        # Control buttons
        button_layout = BoxLayout(orientation='vertical', size_hint_x=0.5, spacing=2)
        
        # Top row: Connect/Control
        top_buttons = BoxLayout(orientation='horizontal', spacing=2, size_hint_y=0.5)
        
        connect_btn = Button(
            text='🔗' if not is_connected else '💡',
            size_hint_x=0.5,
            font_size='10sp'
        )
        if not is_connected:
            connect_btn.bind(on_press=lambda x: self.connect_device(device))
        else:
            connect_btn.bind(on_press=lambda x: self.show_device_controls(device))
        top_buttons.add_widget(connect_btn)
        
        name_btn = Button(
            text='🏷️',
            size_hint_x=0.5,
            font_size='10sp'
        )
        name_btn.bind(on_press=lambda x: self.rename_device(device))
        top_buttons.add_widget(name_btn)
        
        button_layout.add_widget(top_buttons)
        
        # Bottom row: Group assignment
        bottom_buttons = BoxLayout(orientation='horizontal', spacing=2, size_hint_y=0.5)
        
        group_btn = Button(
            text='📋 +',
            size_hint_x=1.0,
            font_size='10sp'
        )
        group_btn.bind(on_press=lambda x: self.assign_device_to_group(device))
        bottom_buttons.add_widget(group_btn)
        
        button_layout.add_widget(bottom_buttons)
        layout.add_widget(button_layout)
        
        return layout
    
    def connect_device(self, device):
        """
        Connect to a specific device
        """
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.connect_device_async(device),
                self.loop
            )
    
    async def connect_device_async(self, device):
        """
        Async method to connect to device
        """
        try:
            self.update_status(f"🔗 Connecting to {device.name or device.address}...")
            
            # Connect to device
            success = await self.controller.connect_to_device(device)
            
            if success:
                # Authenticate
                self.update_status("🔐 Authenticating...")
                auth_success = await self.controller.authenticate_with_mesh(device.address)
                
                if auth_success:
                    self.connected_devices[device.address] = device
                    self.update_status(f"✅ Connected and authenticated with {device.name or device.address}")
                else:
                    self.update_status(f"❌ Authentication failed for {device.name or device.address}")
            else:
                self.update_status(f"❌ Failed to connect to {device.name or device.address}")
                
        except Exception as e:
            self.update_status(f"❌ Connection error: {str(e)}")
            Logger.error(f"URBARN: Connection error: {e}")
    
    def show_device_controls(self, device):
        """
        Show control popup for device
        """
        if device.address not in self.connected_devices:
            self.show_popup("Device Not Connected", "Please connect to this device first.")
            return
        
        # Create control popup
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        title = Label(
            text=f"Control {device.name or device.address}",
            size_hint_y=None,
            height='40dp',
            font_size='16sp',
            bold=True
        )
        content.add_widget(title)
        
        # Light control buttons
        button_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height='50dp')
        
        on_btn = Button(text='💡 Turn ON', size_hint_x=0.5)
        on_btn.bind(on_press=lambda x: self.control_light(device, True))
        button_layout.add_widget(on_btn)
        
        off_btn = Button(text='⚫ Turn OFF', size_hint_x=0.5)
        off_btn.bind(on_press=lambda x: self.control_light(device, False))
        button_layout.add_widget(off_btn)
        
        content.add_widget(button_layout)
        
        # Close button
        close_btn = Button(text='Close', size_hint_y=None, height='40dp')
        content.add_widget(close_btn)
        
        popup = Popup(
            title="Device Controls",
            content=content,
            size_hint=(0.8, 0.6)
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def control_light(self, device, turn_on):
        """
        Control light on/off
        """
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.control_light_async(device, turn_on),
                self.loop
            )
    
    async def control_light_async(self, device, turn_on):
        """
        Async method to control light
        """
        try:
            action = "ON" if turn_on else "OFF"
            self.update_status(f"💡 Turning {action} {device.name or device.address}...")
            
            if turn_on:
                success = await self.controller.turn_on_light(device.address)
            else:
                success = await self.controller.turn_off_light(device.address)
            
            if success:
                self.update_status(f"✅ Successfully turned {action} {device.name or device.address}")
            else:
                self.update_status(f"❌ Failed to turn {action} {device.name or device.address}")
                
        except Exception as e:
            self.update_status(f"❌ Control error: {str(e)}")
            Logger.error(f"URBARN: Control error: {e}")
    
    def on_refresh_pressed(self, button):
        """
        Handle refresh button
        """
        self.update_status("🔄 Refreshing...")
        Clock.schedule_once(lambda dt: self.clear_device_list(), 0)
        self.discovered_devices = []
        self.connected_devices = {}
        self.update_status("Ready to scan for URBARN devices...")
    
    def show_about(self, button):
        """
        Show about popup
        """
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        about_text = """
🚀 FUBARN Light Controller

Custom Android app for controlling URBARN Bluetooth mesh lights using reverse-engineered credentials.

FUBARN = F*** URBARN - We don't need their app!

🔐 Discovered Mesh Credentials:
• Primary: URBARN / 15102
• Secondary: Fulife / 2846

✨ Features:
• Scan for nearby URBARN devices
• Connect and authenticate automatically
• Control lights (ON/OFF)
• Create and manage groups
• Custom device naming
• No official app required!

🛠️ Built with:
• Python + Kivy
• Bleak Bluetooth library
• Reverse engineering analysis

Author: Custom Development
Date: 2025-01-04
"""
        
        about_label = Label(
            text=about_text,
            text_size=(None, None),
            valign='top'
        )
        content.add_widget(about_label)
        
        close_btn = Button(text='Close', size_hint_y=None, height='40dp')
        content.add_widget(close_btn)
        
        popup = Popup(
            title="About FUBARN Controller",
            content=content,
            size_hint=(0.9, 0.8)
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    # Group Management Methods
    def show_groups(self, button):
        """
        Show groups management popup
        """
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Title
        title = Label(
            text="📋 Group Management",
            size_hint_y=None,
            height='30dp',
            font_size='16sp',
            bold=True
        )
        content.add_widget(title)
        
        # Groups list
        scroll = ScrollView()
        groups_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        groups_layout.bind(minimum_height=groups_layout.setter('height'))
        
        # Add existing groups
        groups = self.controller.get_groups()
        if groups:
            for group_id, group_info in groups.items():
                group_widget = self.create_group_widget(group_id, group_info)
                groups_layout.add_widget(group_widget)
        else:
            no_groups_label = Label(
                text="No groups created yet",
                size_hint_y=None,
                height='40dp'
            )
            groups_layout.add_widget(no_groups_label)
        
        scroll.add_widget(groups_layout)
        content.add_widget(scroll)
        
        # Buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=10)
        
        create_btn = Button(text='➕ Create Group')
        create_btn.bind(on_press=lambda x: self.create_new_group())
        button_layout.add_widget(create_btn)
        
        close_btn = Button(text='Close')
        button_layout.add_widget(close_btn)
        
        content.add_widget(button_layout)
        
        popup = Popup(
            title="Groups",
            content=content,
            size_hint=(0.9, 0.8)
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def create_group_widget(self, group_id, group_info):
        """
        Create a widget for a group
        """
        layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='60dp', spacing=5)
        
        # Group info
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.6)
        
        name_label = Label(
            text=f"📋 {group_info['name']}",
            size_hint_y=None,
            height='25dp',
            font_size='14sp',
            bold=True
        )
        info_layout.add_widget(name_label)
        
        device_count_label = Label(
            text=f"{group_info['device_count']} devices",
            size_hint_y=None,
            height='20dp',
            font_size='11sp'
        )
        info_layout.add_widget(device_count_label)
        
        layout.add_widget(info_layout)
        
        # Control buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_x=0.4, spacing=3)
        
        on_btn = Button(
            text='💡 ON',
            size_hint_x=0.33,
            font_size='10sp'
        )
        on_btn.bind(on_press=lambda x: self.control_group_lights(group_id, True))
        button_layout.add_widget(on_btn)
        
        off_btn = Button(
            text='⚫ OFF',
            size_hint_x=0.33,
            font_size='10sp'
        )
        off_btn.bind(on_press=lambda x: self.control_group_lights(group_id, False))
        button_layout.add_widget(off_btn)
        
        edit_btn = Button(
            text='✏️',
            size_hint_x=0.33,
            font_size='10sp'
        )
        edit_btn.bind(on_press=lambda x: self.edit_group(group_id, group_info))
        button_layout.add_widget(edit_btn)
        
        layout.add_widget(button_layout)
        
        return layout
    
    def create_new_group(self):
        """
        Show dialog to create a new group
        """
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        title = Label(
            text="Create New Group",
            size_hint_y=None,
            height='30dp',
            font_size='16sp'
        )
        content.add_widget(title)
        
        from kivy.uix.textinput import TextInput
        name_input = TextInput(
            hint_text='Enter group name (e.g., "Living Room")',
            size_hint_y=None,
            height='40dp',
            multiline=False
        )
        content.add_widget(name_input)
        
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=10)
        
        create_btn = Button(text='Create')
        cancel_btn = Button(text='Cancel')
        
        button_layout.add_widget(create_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        
        popup = Popup(
            title="New Group",
            content=content,
            size_hint=(0.8, 0.5)
        )
        
        def create_group(instance):
            group_name = name_input.text.strip()
            if group_name:
                group_id = self.controller.create_group(group_name)
                self.update_status(f"Created group '{group_name}'")
                popup.dismiss()
        
        create_btn.bind(on_press=create_group)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def rename_device(self, device):
        """
        Show dialog to rename a device
        """
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        title = Label(
            text=f"Rename Device\n{device.address[-8:]}",
            size_hint_y=None,
            height='50dp',
            font_size='14sp'
        )
        content.add_widget(title)
        
        from kivy.uix.textinput import TextInput
        current_name = self.controller.get_device_name(device.address)
        name_input = TextInput(
            text=current_name if current_name != device.address[-8:] else '',
            hint_text='Enter device name (e.g., "Kitchen Light")',
            size_hint_y=None,
            height='40dp',
            multiline=False
        )
        content.add_widget(name_input)
        
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=10)
        
        save_btn = Button(text='Save')
        cancel_btn = Button(text='Cancel')
        
        button_layout.add_widget(save_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        
        popup = Popup(
            title="Rename Device",
            content=content,
            size_hint=(0.8, 0.5)
        )
        
        def save_name(instance):
            new_name = name_input.text.strip()
            if new_name:
                self.controller.set_device_name(device.address, new_name)
                self.update_status(f"Renamed device to '{new_name}'")
                # Refresh device list
                Clock.schedule_once(lambda dt: self.populate_device_list(), 0)
            popup.dismiss()
        
        save_btn.bind(on_press=save_name)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def assign_device_to_group(self, device):
        """
        Show dialog to assign device to a group
        """
        groups = self.controller.get_groups()
        
        if not groups:
            self.show_popup("No Groups", "Create a group first before assigning devices.")
            return
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        title = Label(
            text=f"Add to Group\n{self.controller.get_device_name(device.address)}",
            size_hint_y=None,
            height='50dp',
            font_size='14sp'
        )
        content.add_widget(title)
        
        # Group buttons
        scroll = ScrollView()
        groups_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        groups_layout.bind(minimum_height=groups_layout.setter('height'))
        
        for group_id, group_info in groups.items():
            is_in_group = device.address in group_info['devices']
            group_btn = Button(
                text=f"{'✅' if is_in_group else '➕'} {group_info['name']}",
                size_hint_y=None,
                height='40dp'
            )
            
            def toggle_group(instance, gid=group_id, in_group=is_in_group):
                if in_group:
                    self.controller.remove_device_from_group(gid, device.address)
                    self.update_status(f"Removed from {self.controller.group_names[gid]}")
                else:
                    self.controller.add_device_to_group(gid, device.address)
                    self.update_status(f"Added to {self.controller.group_names[gid]}")
                popup.dismiss()
            
            group_btn.bind(on_press=toggle_group)
            groups_layout.add_widget(group_btn)
        
        scroll.add_widget(groups_layout)
        content.add_widget(scroll)
        
        close_btn = Button(text='Close', size_hint_y=None, height='40dp')
        content.add_widget(close_btn)
        
        popup = Popup(
            title="Assign to Group",
            content=content,
            size_hint=(0.8, 0.7)
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def control_group_lights(self, group_id, turn_on):
        """
        Control all lights in a group
        """
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.control_group_async(group_id, turn_on),
                self.loop
            )
    
    async def control_group_async(self, group_id, turn_on):
        """
        Async method to control group lights
        """
        try:
            results = await self.controller.control_group(group_id, turn_on)
            
            group_name = self.controller.group_names.get(group_id, group_id)
            action = "ON" if turn_on else "OFF"
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            
            self.update_status(f"Group '{group_name}' {action}: {successful}/{total} lights")
            
        except Exception as e:
            self.update_status(f"Group control error: {str(e)}")
            Logger.error(f"FUBARN: Group control error: {e}")
    
    def edit_group(self, group_id, group_info):
        """
        Show dialog to edit group (rename/delete)
        """
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        title = Label(
            text=f"Edit Group\n{group_info['name']}",
            size_hint_y=None,
            height='50dp',
            font_size='14sp'
        )
        content.add_widget(title)
        
        button_layout = BoxLayout(orientation='vertical', spacing=10)
        
        rename_btn = Button(
            text='✏️ Rename Group',
            size_hint_y=None,
            height='50dp'
        )
        button_layout.add_widget(rename_btn)
        
        delete_btn = Button(
            text='🗑️ Delete Group',
            size_hint_y=None,
            height='50dp'
        )
        button_layout.add_widget(delete_btn)
        
        close_btn = Button(
            text='Close',
            size_hint_y=None,
            height='40dp'
        )
        button_layout.add_widget(close_btn)
        
        content.add_widget(button_layout)
        
        popup = Popup(
            title="Edit Group",
            content=content,
            size_hint=(0.7, 0.6)
        )
        
        def rename_group(instance):
            popup.dismiss()
            self.rename_group_dialog(group_id, group_info['name'])
        
        def delete_group(instance):
            self.controller.delete_group(group_id)
            self.update_status(f"Deleted group '{group_info['name']}'")
            popup.dismiss()
        
        rename_btn.bind(on_press=rename_group)
        delete_btn.bind(on_press=delete_group)
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def rename_group_dialog(self, group_id, current_name):
        """
        Show dialog to rename a group
        """
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        title = Label(
            text="Rename Group",
            size_hint_y=None,
            height='30dp',
            font_size='16sp'
        )
        content.add_widget(title)
        
        from kivy.uix.textinput import TextInput
        name_input = TextInput(
            text=current_name,
            size_hint_y=None,
            height='40dp',
            multiline=False
        )
        content.add_widget(name_input)
        
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=10)
        
        save_btn = Button(text='Save')
        cancel_btn = Button(text='Cancel')
        
        button_layout.add_widget(save_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        
        popup = Popup(
            title="Rename Group",
            content=content,
            size_hint=(0.8, 0.5)
        )
        
        def save_name(instance):
            new_name = name_input.text.strip()
            if new_name and new_name != current_name:
                self.controller.rename_group(group_id, new_name)
                self.update_status(f"Renamed group to '{new_name}'")
            popup.dismiss()
        
        save_btn.bind(on_press=save_name)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def show_popup(self, title, message):
        """
        Show a simple popup message
        """
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        label = Label(text=message)
        content.add_widget(label)
        
        close_btn = Button(text='Close', size_hint_y=None, height='40dp')
        content.add_widget(close_btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.7, 0.4)
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def on_stop(self):
        """
        Clean up when app is closed
        """
        if self.loop and not self.loop.is_closed():
            # Disconnect all devices
            asyncio.run_coroutine_threadsafe(
                self.controller.disconnect_all(),
                self.loop
            )
            
            # Stop the loop
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        return True

if __name__ == '__main__':
    FubarnApp().run()

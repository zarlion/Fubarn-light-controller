# 🚀 FUBARN - Enhanced Light Controller

## 🎯 **What's FUBARN?**
**FUBARN = F*** URBARN** - We don't need their crappy app!

Our custom Android app **completely replaces** the official URBARN app with better features and full control.

---

## ✨ **New Features Added**

### 📋 **Group Management**
- **Create Groups:** "Living Room", "Bedroom", "Kitchen", etc.
- **Group Control:** Turn entire groups ON/OFF with one tap
- **Easy Assignment:** Add/remove lights from groups
- **Group Editing:** Rename or delete groups anytime

### 🏷️ **Device Naming** 
- **Custom Names:** "Kitchen Light", "Bedside Lamp", "Porch Light"
- **Easy Identification:** No more confusing MAC addresses
- **Quick Renaming:** Tap the 🏷️ button to rename any device

### 💾 **Persistent Storage**
- **Auto-Save:** Groups and names automatically saved
- **Android Storage:** Uses app-specific storage on device
- **Cross-Session:** Settings persist when you close/reopen app

### 🔧 **Enhanced UI**
- **Groups Button:** New 📋 Groups button in main interface
- **Device Status:** Visual connection status for each device  
- **Improved Layout:** Better organization of controls
- **Group Controls:** ON/OFF buttons for each group

---

## 🎮 **How to Use Groups**

### **Create a Group:**
1. Tap **📋 Groups** button
2. Tap **➕ Create Group**  
3. Enter name like "Living Room"
4. Tap **Create**

### **Add Lights to Group:**
1. After scanning, find your light
2. Tap **📋 +** button on the device
3. Select which group to add it to
4. Tap the group name

### **Control Groups:**
1. Open **📋 Groups**
2. Tap **💡 ON** or **⚫ OFF** for any group
3. All lights in that group will respond

### **Rename Devices:**
1. Find your device in the list
2. Tap **🏷️** button  
3. Enter custom name like "Kitchen Light"
4. Tap **Save**

---

## 🔄 **What Changed from Original**

### **Original URBARN Controller:**
- ✅ Scan and connect to devices
- ✅ Turn individual lights ON/OFF  
- ✅ Use reverse-engineered credentials

### **NEW FUBARN Features:**
- 🆕 **Group Management** - Control multiple lights at once
- 🆕 **Custom Device Names** - "Kitchen Light" instead of "FF:00:01:05:19:AA"
- 🆕 **Persistent Storage** - Settings saved between app sessions
- 🆕 **Enhanced UI** - Better layout and visual indicators
- 🆕 **Group Controls** - Bulk ON/OFF operations
- 🆕 **Device Assignment** - Easy drag-and-drop to groups

---

## 📱 **App Structure**

```
FUBARN Light Controller
├── 🔍 Scan for Devices
├── 📋 Groups Management  
├── 🔄 Refresh
└── ℹ️ About

Device List:
├── 📡 Device Name (custom)
├── 📍 Address (short)
├── 🔌 Connection Status
├── 🔗/💡 Connect/Control
├── 🏷️ Rename Device
└── 📋 + Add to Group

Group Management:
├── ➕ Create New Group
├── Group List:
│   ├── 💡 ON Button
│   ├── ⚫ OFF Button
│   └── ✏️ Edit (Rename/Delete)
```

---

## 💾 **Data Storage**

All your groups and device names are saved in:
- **Android:** `/data/data/com.fubarn.fubarnlights/files/fubarn_data.json`
- **Desktop:** `fubarn_data.json` (for testing)

**Example saved data:**
```json
{
  "device_groups": {
    "abc12345": ["FF:00:01:05:19:AA", "FF:00:01:05:19:BB"]
  },
  "group_names": {
    "abc12345": "Living Room"
  },
  "device_names": {
    "FF:00:01:05:19:AA": "Table Lamp",
    "FF:00:01:05:19:BB": "Floor Light"
  }
}
```

---

## 🚀 **Ready to Build!**

Your enhanced **FUBARN** controller is ready for GitHub Actions:

1. **Upload** all files to GitHub repository
2. **Run workflow** to build APK
3. **Install** on Android
4. **Create groups** like "Living Room", "Bedroom"
5. **Name your devices** with friendly names
6. **Control everything** with custom groups!

**FUBARN** - Because we're better than URBARN! 😎

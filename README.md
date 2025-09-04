# 🚀 FUBARN Light Controller

**Custom Android app for controlling URBARN Bluetooth mesh lights using reverse-engineered credentials.**

**FUBARN = F*** URBARN - We don't need their app!**

## ✨ Features

- 🔍 **Scan** for nearby URBARN mesh devices
- 🔗 **Connect** and authenticate automatically using discovered credentials
- 💡 **Control** lights individually (ON/OFF functionality)
- 📱 **Mobile-optimized** touch interface built with Kivy
- 🔐 **No official app required** - uses reverse-engineered mesh credentials!
- 📋 **Group management** - create named groups like "Living Room", "Kitchen"
- 🏷️ **Device naming** - give custom names to your lights
- 💾 **Persistent storage** - groups and names saved locally

## 🔐 Discovered Credentials

Through reverse engineering of the official URBARN app, we discovered:
- **Primary Mesh:** `URBARN` / `15102` 
- **Secondary Mesh:** `Fulife` / `2846`

## 🚀 Get Your APK

### Method 1: GitHub Actions (Automatic)
1. Push this code to your GitHub repository
2. Go to **Actions** tab
3. Click **"Build Urbarn APK (Fast)"**  
4. Click **"Run workflow"**
5. Wait 10-15 minutes
6. Download APK from **Artifacts**

### Method 2: AWS CodeBuild (Your Account)
1. Set up AWS CodeBuild project (see `buildspec.yml`)
2. Connect to this repository
3. Trigger build
4. Download APK from S3

## 📱 Installation

1. Transfer APK to Android device
2. Enable "Unknown Sources" in Android settings
3. Install APK
4. Grant Bluetooth permissions
5. **Control your URBARN lights!**

## 🎯 What This Does

This app **completely replaces** the official URBARN app by using the reverse-engineered Bluetooth mesh protocol. No internet connection or official servers required!

## ⚖️ Legal Notice

This project is for educational and personal use only. Created through reverse engineering for interoperability purposes.

---

**🎉 Successfully reverse-engineered and ready to control URBARN lighting systems!**

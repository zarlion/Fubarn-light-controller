# 📤 Upload Instructions - Build Your URBARN APK

You now have a clean folder ready for GitHub! Here are your **two options** to build the APK:

## 🚀 **OPTION 1: GitHub Actions (Recommended - FREE)**

### Step 1: Create GitHub Repository
1. Go to [GitHub.com](https://github.com) and log in
2. Click **"New Repository"**
3. Name it: `urbarn-light-controller`
4. Make it **Public** (required for free Actions)
5. **Don't** initialize with README (we have our own files)
6. Click **"Create repository"**

### Step 2: Upload All Files
**Drag and drop** the entire contents of this folder (`C:\Users\Brandon\Desktop\urbarn-apk-github\`) to GitHub:

**Files to upload:**
- ✅ `main.py` - Main Android app
- ✅ `urbarn_mesh_controller.py` - Bluetooth mesh controller
- ✅ `buildozer.spec` - Android build configuration  
- ✅ `requirements.txt` - Python dependencies
- ✅ `README.md` - Project documentation
- ✅ `.github/workflows/build-apk.yml` - GitHub Actions workflow
- ✅ `buildspec.yml` - AWS CodeBuild config (optional)

### Step 3: Trigger APK Build
1. Go to your repository on GitHub
2. Click **"Actions"** tab at the top
3. You should see **"Build Urbarn APK (Fast)"** workflow
4. Click **"Run workflow"** button
5. Click the green **"Run workflow"** button again
6. **Wait 10-15 minutes** for the build to complete ⏳

### Step 4: Download Your APK
1. When build is complete, click on the workflow run
2. Scroll down to **"Artifacts"** section  
3. Click **"urbarn-light-controller-apk"** to download
4. Extract the ZIP file
5. **Your APK is ready!** 🎉

---

## 🔶 **OPTION 2: AWS CodeBuild (Since You Have AWS Account)**

### Step 1: Upload to GitHub First
Follow steps 1-2 above to get your code on GitHub

### Step 2: Create AWS CodeBuild Project
1. Go to [AWS CodeBuild Console](https://console.aws.amazon.com/codesuite/codebuild)
2. Click **"Create build project"**
3. **Project name:** `urbarn-apk-builder`
4. **Source provider:** GitHub
5. **Repository:** Connect to your `urbarn-light-controller` repo
6. **Environment:**
   - **Environment image:** Managed image
   - **Operating system:** Ubuntu
   - **Runtime:** Standard
   - **Image:** `aws/codebuild/standard:5.0` (or latest)
   - **Service role:** Create new (or use existing)
7. **Buildspec:** Use buildspec file (`buildspec.yml` is already included)
8. **Artifacts:**
   - **Type:** S3
   - **Bucket name:** Create/choose an S3 bucket for APK storage
   - **Path:** `urbarn-apks/`

### Step 3: Build APK
1. Click **"Start build"** in your CodeBuild project
2. **Wait 15-20 minutes** for first build (downloads Android SDK)
3. **Download APK** from your S3 bucket when complete

### Step 4: Cost Estimate
- **Build time:** ~20 minutes
- **Instance:** `build.general1.medium`
- **Cost:** ~$0.10-0.20 per build
- **Free tier:** 100 build minutes/month (covers 5 builds)

---

## 📱 **Install APK on Android**

Once you have your APK file:

1. **Transfer** APK to your Android phone
2. **Settings** → Security → Enable **"Unknown Sources"**
3. **Tap** the APK file to install
4. **Grant** Bluetooth permissions when asked
5. **Open** the app and scan for URBARN devices
6. **Connect** and control your lights! ⚡

---

## 🎯 **What You'll Get**

Your custom APK will have:
- ✅ **Device scanner** - Finds URBARN lights automatically
- ✅ **Auto-authentication** - Uses discovered credentials `URBARN/15102`
- ✅ **Light controls** - ON/OFF buttons for each device
- ✅ **No official app needed** - Complete replacement!
- ✅ **Works offline** - Direct Bluetooth mesh communication

---

## 🆘 **Troubleshooting**

**GitHub Actions build fails?**
- Make sure repository is **public**
- Check that all files uploaded correctly
- View build logs in Actions tab for errors

**AWS CodeBuild fails?**
- Check IAM permissions for CodeBuild service role
- Verify S3 bucket permissions
- Check build logs in CodeBuild console

**APK won't install?**
- Enable "Unknown Sources" in Android settings
- Try "Install from Unknown Apps" permission
- Check Android version compatibility (8.0+)

---

## 🎉 **Ready to Build!**

Your URBARN light controller is ready to become a real Android app!

**Recommended:** Start with **GitHub Actions** (free and automatic)

**Questions?** Check the build logs for detailed error messages.

🚀 **Let's turn your reverse-engineered URBARN protocol into a working Android APK!**

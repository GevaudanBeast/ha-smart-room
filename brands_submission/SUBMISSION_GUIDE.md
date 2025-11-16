# Home Assistant Brands Repository Submission Guide

## Overview
This directory contains the icon for the Smart Room Manager integration ready to be submitted to the Home Assistant Brands repository.

## What's Included
```
brands_submission/
└── custom_integrations/
    └── smart_room_manager/
        └── icon.png (256x256 PNG)
```

## Submission Steps

### 1. Fork the Brands Repository
1. Go to https://github.com/home-assistant/brands
2. Click the "Fork" button in the top right
3. Select your GitHub account as the destination

### 2. Clone Your Fork
```bash
git clone https://github.com/YOUR_USERNAME/brands.git
cd brands
```

### 3. Create a New Branch
```bash
git checkout -b add-smart-room-manager
```

### 4. Copy the Icon Files
```bash
# Copy from this repository to the brands repository
cp -r /path/to/ha-smart-room/brands_submission/custom_integrations/smart_room_manager custom_integrations/
```

Or manually:
- Copy `brands_submission/custom_integrations/smart_room_manager/icon.png`
- To `brands/custom_integrations/smart_room_manager/icon.png` in your forked repository

### 5. Commit and Push
```bash
git add custom_integrations/smart_room_manager/
git commit -m "Add Smart Room Manager integration icon"
git push origin add-smart-room-manager
```

### 6. Create a Pull Request
1. Go to https://github.com/YOUR_USERNAME/brands
2. Click "Pull requests" > "New pull request"
3. Select your branch `add-smart-room-manager`
4. Click "Create pull request"
5. Fill in the title: "Add Smart Room Manager integration"
6. Fill in the description:
   ```
   Adding icon for Smart Room Manager custom integration.

   Integration repository: https://github.com/GevaudanBeast/ha-smart-room
   Domain: smart_room_manager
   ```
7. Submit the pull request

## After Submission

Once your PR is merged:
1. The HACS validation check will pass
2. Your integration icon will be available at:
   - `https://brands.home-assistant.io/smart_room_manager/icon.png`

## Icon Specifications

The icon meets the following requirements:
- Format: PNG
- Size: 256x256 pixels (1:1 aspect ratio)
- Optimized for web use
- Design: Simple house/room icon representing smart home automation

## Need Help?

- Brands repository: https://github.com/home-assistant/brands
- HACS documentation: https://hacs.xyz/docs/publish/integration

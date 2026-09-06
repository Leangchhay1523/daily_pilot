# DailyPilot — Deployment Guide

Deploy DailyPilot to a free cloud VM so it runs 24/7 and delivers scheduled reminders reliably.

Two options are covered:

| Option                                                                 | Cost         | Difficulty |
| ---------------------------------------------------------------------- | ------------ | ---------- |
| [Option A — Oracle Cloud](#option-a--oracle-cloud-free-tier)           | Free forever | Medium     |
| [Option B — Google Cloud (GCP)](#option-b--google-cloud-gcp-free-tier) | Free forever | Easy       |

> Both use the same steps for deploying the bot itself (Steps 4–8).
> Only the VM creation steps differ.

---

## Common Prerequisites

Before starting either option:

- Your Telegram bot token from [@BotFather](https://t.me/BotFather)
- Your Telegram chat ID (send `/start` to your bot first, or use [@userinfobot](https://t.me/userinfobot))
- An SSH key pair — see [SSH Key Guide](#ssh-key-guide) at the bottom if you don't have one

---

---

# Option A — Oracle Cloud Free Tier

**Best if:** You want maximum free resources (up to 4 OCPUs, 24 GB RAM across VMs).

**Catch:** The free Ampere (A1) shape is often out of capacity. You may need to retry several times.

👉 Sign up at [cloud.oracle.com](https://cloud.oracle.com)

---

## A1 — Create the VM

1. Log in to [cloud.oracle.com](https://cloud.oracle.com)
2. Open the menu (☰) → **Compute** → **Instances**
3. Click **Create Instance**

---

### 📌 Name and Placement

| Field               | Value                                           |
| ------------------- | ----------------------------------------------- |
| Name                | `daily-pilot`                                   |
| Compartment         | Leave as root (default)                         |
| Availability domain | `AD-1` (try `AD-2` / `AD-3` if out of capacity) |

---

### 🖼️ Image and Shape

**Change the Image:**

1. Click **Change image**
2. Select **Canonical Ubuntu**
3. Pick **Ubuntu 22.04**
4. Click **Select image**

**Change the Shape:**

1. Click **Change shape**
2. Select **Virtual machine** → **Ampere**
3. Pick **VM.Standard.A1.Flex**
4. Set **OCPUs: 1**, **Memory: 6 GB**
5. Click **Select shape**

> ✅ Always Free: up to 4 OCPUs + 24 GB RAM total across Ampere VMs.

---

### 🌐 Networking

1. Select **"Create new virtual cloud network"**
2. VCN name: `daily-pilot-vcn` (auto-filled)
3. Subnet name: `daily-pilot-subnet` (auto-filled)
4. **Subnet type: Public subnet** ← important
5. ✅ Check **"Assign a public IPv4 address"** ← required

---

### 🔑 Add SSH Keys

**Upload the file:**

1. Select **"Upload public key files (.pub)"**
2. Browse to `C:\Users\MSI\.ssh\id_rsa.pub` and select it

**Or paste it:**

```bash
# Run this in PowerShell, then copy the output
cat ~/.ssh/id_rsa.pub
```

Select **"Paste public keys"** and paste the output.

---

### 💾 Boot Volume

1. Check **"Specify a custom boot volume size"**
2. Set size: **50 GB**
3. Leave everything else as default

---

### 🛡️ Security (if shown)

Leave everything off — defaults are fine.

---

### ✅ Review and Create

Verify before clicking Create:

- ✅ Image: Ubuntu 22.04
- ✅ Shape: VM.Standard.A1.Flex — 1 OCPU, 6 GB
- ✅ Network: public subnet, public IPv4 assigned
- ✅ SSH key: uploaded/pasted
- ✅ Boot volume: 50 GB

Click **Create**. Wait ~2 minutes for status to become `RUNNING`.

Copy the **Public IP address** from the instance page.

---

### 🔓 Open SSH Port in Oracle Firewall

Oracle blocks all inbound traffic by default. Do this once after VM creation:

1. Instance page → scroll to **"Primary VNIC"**
2. Click the **subnet link** (e.g. `daily-pilot-subnet`)
3. Click **"Default Security List for daily-pilot-vcn"**
4. Click **"Add Ingress Rules"**

| Field                  | Value       |
| ---------------------- | ----------- |
| Source CIDR            | `0.0.0.0/0` |
| IP Protocol            | TCP         |
| Destination Port Range | `22`        |
| Description            | `SSH`       |

Click **Add Ingress Rules**.

> The bot only makes outbound connections to Telegram — no extra rules needed for the bot.

---

**→ Now jump to [Step 2 — Connect to the VM](#step-2--connect-to-the-vm)**

---

---

# Option B — Google Cloud (GCP) Free Tier

**Best if:** Oracle is out of capacity, or you want a simpler setup process.

**Free tier:** The `e2-micro` VM in 3 US regions is **always free forever** (even after the 12-month $300 trial ends).

👉 Sign up at [cloud.google.com/free](https://cloud.google.com/free)

---

## B1 — Safety First: Set a Billing Budget Alert

Do this **before** creating anything. It protects you from accidental charges.

1. In GCP Console → open the menu (☰) → **Billing**
2. Click **Budgets & Alerts** → **Create Budget**
3. Set:
   - Scope: All projects
   - Amount: **$1**
   - Alerts at: 50%, 90%, 100%
   - Add your email
4. Click **Save**

You'll get an email if anything costs even $0.50 — giving you time to fix it.

---

## B2 — Create the VM

1. Log in to [console.cloud.google.com](https://console.cloud.google.com)
2. Open the menu (☰) → **Compute Engine** → **VM Instances**
3. If prompted, click **Enable** to enable the Compute Engine API (takes ~1 min)
4. Click **Create Instance**

---

### 📌 Name and Region

| Field  | Value                                                        |
| ------ | ------------------------------------------------------------ |
| Name   | `daily-pilot`                                                |
| Region | **`us-central1` (Iowa)** ← must be one of the 3 free regions |
| Zone   | `us-central1-a`                                              |

> ⚠️ **Only these 3 regions are free:** `us-east1`, `us-west1`, `us-central1`. Any other region will charge you.

---

### 🖥️ Machine Configuration

| Field        | Value                               |
| ------------ | ----------------------------------- |
| Series       | **E2**                              |
| Machine type | **e2-micro** ← must be exactly this |

> ⚠️ Only `e2-micro` is free. `e2-small`, `e2-medium`, etc. will charge you.

---

### 🌐 Networking (important — change the tier)

1. Click **"Networking, Disks, Security, Management"** to expand advanced options
2. Click the **Networking** tab
3. Under **Network interfaces** → click the pencil ✏️ on `default`
4. Set **Network Service Tier** to **Standard** ← saves money on egress

Leave everything else as default. A public IP (ephemeral) will be assigned automatically.

> ⚠️ Do NOT reserve a Static IP — a reserved static IP on a stopped VM costs ~$7/month. Ephemeral (default) is free.

---

### 💾 Boot Disk

1. Click **Change** next to the boot disk
2. Set:

| Field            | Value                                                  |
| ---------------- | ------------------------------------------------------ |
| Operating system | **Ubuntu**                                             |
| Version          | **Ubuntu 22.04 LTS**                                   |
| Boot disk type   | **Standard persistent disk** (`pd-standard`) ← not SSD |
| Size             | **30 GB** ← the free limit                             |

3. Click **Select**

> ⚠️ SSD (`pd-ssd`) and anything over 30 GB costs money.

---

### 🔑 SSH Keys

GCP manages SSH differently from Oracle — it injects your key automatically via metadata.

1. Still in the advanced options, click the **Security** tab
2. Under **Manage SSH keys** → click **Add item**
3. Paste your public key:
   ```bash
   # Run in PowerShell, copy the output
   cat ~/.ssh/id_rsa.pub
   ```
4. Paste it into the field

GCP will auto-fill your username from the key.

---

### ✅ Review and Create

Verify:

- ✅ Region: `us-central1` (or `us-east1` / `us-west1`)
- ✅ Machine type: `e2-micro`
- ✅ Boot disk: Ubuntu 22.04, 30 GB, Standard persistent
- ✅ Network tier: Standard
- ✅ SSH key: added

Click **Create**.

The VM appears in the list in ~30 seconds. Copy the **External IP** address.

---

## B3 — Open SSH Port in GCP Firewall

GCP has its own firewall. Allow SSH:

1. Menu (☰) → **VPC Network** → **Firewall**
2. Click **Create Firewall Rule**

| Field               | Value                        |
| ------------------- | ---------------------------- |
| Name                | `allow-ssh`                  |
| Network             | `default`                    |
| Direction           | Ingress                      |
| Action              | Allow                        |
| Targets             | All instances in the network |
| Source filter       | IPv4 ranges                  |
| Source IPv4 ranges  | `0.0.0.0/0`                  |
| Protocols and ports | **TCP: 22**                  |

Click **Create**.

> Alternatively: GCP often creates a default `default-allow-ssh` rule already. Check if it exists before creating a new one.

---

**→ Continue to [Step 2 — Connect to the VM](#step-2--connect-to-the-vm)**

---

---

# Shared Steps (Both Oracle and GCP)

---

## Step 2 — Connect to the VM

Open **PowerShell** on your local machine:

```bash
ssh ubuntu@<YOUR_PUBLIC_IP>
```

> On GCP the default username matches your SSH key username (usually your Google account username, not `ubuntu`). If `ubuntu` doesn't work, check the SSH key field — GCP shows the username next to the key.

First time it asks `"Are you sure you want to continue connecting?"` → type `yes` and press Enter.

If your key isn't the default name:

```bash
ssh -i ~/.ssh/your_key_name ubuntu@<YOUR_PUBLIC_IP>
```

---

## Step 3 — Set Up the Server

### Update packages

```bash
sudo apt update && sudo apt upgrade -y
```

### Install Python 3.11

```bash
sudo apt install -y python3.11 python3.11-venv python3-pip git
```

Verify:

```bash
python3.11 --version
```

---

## Step 4 — Deploy the Bot

### Upload your code

**Option A — scp from your Windows machine** (run in local PowerShell):

```bash
scp -r "d:/Documents/GitHub/Projects/daily_pilot" ubuntu@<YOUR_PUBLIC_IP>:~/daily_pilot
```

**Option B — clone from GitHub** (run on the server):

```bash
cd ~
git clone https://github.com/<YOUR_USERNAME>/daily_pilot.git
cd daily_pilot
```

### Create the virtual environment

```bash
cd ~/daily_pilot
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Create the `.env` file

```bash
nano .env
```

Paste (no quotes around values):

```
BOT_TOKEN=8858439420:AAFzBdxarF7XG8x4sQr4v1PCIDqkcODeAiA
CHAT_ID=<YOUR_TELEGRAM_CHAT_ID>
```

Save: `Ctrl+O` → `Enter` → `Ctrl+X`

Lock down permissions:

```bash
chmod 600 .env
```

### Test the bot manually

```bash
source .venv/bin/activate
python -m app.bot
```

Send `/start` to your bot on Telegram. If it replies — everything works.

Stop it with `Ctrl+C` and continue.

---

## Step 5 — Run as a systemd Service

This keeps the bot running permanently — starts on boot, restarts on crash.

### Create the service file

```bash
sudo nano /etc/systemd/system/daily-pilot.service
```

Paste exactly:

```ini
[Unit]
Description=DailyPilot Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/daily_pilot
EnvironmentFile=/home/ubuntu/daily_pilot/.env
ExecStart=/home/ubuntu/daily_pilot/.venv/bin/python -m app.bot
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Save: `Ctrl+O` → `Enter` → `Ctrl+X`

### Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable daily-pilot
sudo systemctl start daily-pilot
```

### Verify it's running

```bash
sudo systemctl status daily-pilot
```

You should see `Active: active (running)` in green.

---

## Step 6 — Check Logs

```bash
# Live log stream (Ctrl+C to exit)
sudo journalctl -u daily-pilot -f

# Last 50 lines
sudo journalctl -u daily-pilot -n 50
```

---

## Step 7 — Set the Correct Timezone

The scheduler fires based on the VM's system clock. Set it to your local timezone so the 9 AM reminder fires at the right time, not at UTC.

```bash
# Set to ICT (Indochina Time, UTC+7)
sudo timedatectl set-timezone Asia/Bangkok

# Restart the bot to apply
sudo systemctl restart daily-pilot

# Verify
timedatectl
```

Look for `Time zone: Asia/Bangkok (ICT, +0700)`.

> Find your timezone string:
>
> ```bash
> timedatectl list-timezones | grep Asia
> ```

---

## Step 8 — Set Up Automatic Database Backup

The SQLite database is at `~/daily_pilot/data/daily_pilot.db`.

```bash
# Create backup folder
mkdir -p ~/backups

# Open crontab
crontab -e
```

Add this line (backs up every night at 11 PM):

```
0 23 * * * cp /home/ubuntu/daily_pilot/data/daily_pilot.db /home/ubuntu/backups/daily_pilot_$(date +\%Y\%m\%d).db
```

Save and exit.

---

## Updating the Bot

**If using scp:**

```bash
# Run on your local machine
scp -r "d:/Documents/GitHub/Projects/daily_pilot" ubuntu@<YOUR_PUBLIC_IP>:~/daily_pilot

# Then on the server
sudo systemctl restart daily-pilot
```

**If using git:**

```bash
cd ~/daily_pilot
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart daily-pilot
sudo systemctl status daily-pilot
```

---

## Quick Reference

| Task             | Command                                                                    |
| ---------------- | -------------------------------------------------------------------------- |
| Start bot        | `sudo systemctl start daily-pilot`                                         |
| Stop bot         | `sudo systemctl stop daily-pilot`                                          |
| Restart bot      | `sudo systemctl restart daily-pilot`                                       |
| View status      | `sudo systemctl status daily-pilot`                                        |
| Live logs        | `sudo journalctl -u daily-pilot -f`                                        |
| Edit `.env`      | `nano ~/daily_pilot/.env`                                                  |
| Update & restart | `git pull && sudo systemctl restart daily-pilot`                           |
| Manual DB backup | `cp ~/daily_pilot/data/daily_pilot.db ~/backups/backup_$(date +%Y%m%d).db` |

---

## Troubleshooting

| Problem                     | Fix                                                                    |
| --------------------------- | ---------------------------------------------------------------------- |
| Can't SSH in (Oracle)       | Add port 22 ingress rule to the Security List                          |
| Can't SSH in (GCP)          | Check `default-allow-ssh` firewall rule exists                         |
| Wrong SSH username (GCP)    | Use the username shown next to your key in GCP console, not `ubuntu`   |
| Bot not responding          | Check logs: `sudo journalctl -u daily-pilot -n 50`                     |
| Wrong reminder time         | Set timezone: `sudo timedatectl set-timezone Asia/Bangkok`             |
| `ModuleNotFoundError`       | Re-run: `source .venv/bin/activate && pip install -r requirements.txt` |
| Permission denied on `.env` | Run: `chmod 600 .env`                                                  |
| Service won't start         | Check `.env` has no quotes: `BOT_TOKEN=abc` not `BOT_TOKEN="abc"`      |
| Bot token invalid           | Regenerate via [@BotFather](https://t.me/BotFather)                    |
| Oracle: out of capacity     | Try AD-2 / AD-3, or retry later. See Option B (GCP) as alternative     |
| GCP: accidentally charged   | Check region is `us-central1/east1/west1` and machine is `e2-micro`    |

---

## SSH Key Guide

### Check if you already have one

```bash
ls ~/.ssh/
```

If you see `id_rsa` and `id_rsa.pub` — you already have one. Skip to the upload step.

### Generate a new SSH key

```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

Press Enter for all prompts (use defaults, no passphrase).

This creates:

```
C:\Users\MSI\.ssh\id_rsa      ← private key (never share this)
C:\Users\MSI\.ssh\id_rsa.pub  ← public key  (upload this to cloud provider)
```

### View your public key

```bash
cat ~/.ssh/id_rsa.pub
```

Copy the full output and paste it into Oracle or GCP during VM creation.

# Target Server Setup Guide

**Project:** D-stress DDoS Simulation  
**Purpose:** Setting up old laptop as attack target  
**Date:** February 15, 2026

---

## 🎯 Setting Up Old Laptop as Target Server

---

## 📡 The Big Picture

```
[Old Laptop - Target]          [Main Laptop - Attackers]
   i3, 8GB RAM                    i5 10-core, 16GB
   IP: 192.168.1.100              IP: 192.168.1.50
        ↑                              ↓
        └──────── WiFi Network ────────┘
           (HTTP requests flood)
```

---

## 🔧 Step-by-Step Concept

### **Step 1: Prepare the Old Laptop**

**Install a lightweight OS:**
- **Option A:** Ubuntu Server (no GUI, minimal resources)
- **Option B:** Linux Mint/Ubuntu Desktop (if you want GUI for monitoring)

**Why?** A server OS uses less RAM/CPU, leaving more for your test server to handle load.

---

### **Step 2: Install Target Server Software**

You'll run a **web server** that can handle HTTP requests. Three choices:

**Option A: Nginx** (simplest)
- Pure web server
- Serves static pages
- Very lightweight
- Good for basic HTTP flood testing

**Option B: Flask** (more control)
- Python web app
- Can add custom endpoints
- Monitor incoming requests in code
- Log request details

**Option C: Both!** (recommended)
- Nginx as reverse proxy (frontend)
- Flask behind it (backend)
- More realistic production setup

---

### **Step 3: Network Configuration**

**Goal:** Make old laptop accessible from main laptop

**What you'll do:**
1. Connect both laptops to **same WiFi/router**
2. Find old laptop's local IP (something like `192.168.1.100`)
3. Make sure firewall allows incoming HTTP (port 80)
4. Test connection with simple ping

**Key concept:** Your Docker containers will send requests to this IP address.

---

### **Step 4: Target Server Features**

Your target should do these things:

**A. Accept Connections**
- Listen on port 80 (HTTP) or 443 (HTTPS)
- Respond to GET/POST requests
- Handle multiple connections simultaneously

**B. Log Everything**
- Request count per second
- Response times
- Connection states
- Error rates

**C. Report Metrics**
- CPU usage
- RAM usage
- Network bandwidth
- Active connections

**D. Stay Alive**
- Don't crash under load
- Handle errors gracefully
- Keep serving (even slowly)

---

### **Step 5: Monitoring Setup**

**On the target (old laptop):**
- **htop** - See CPU/RAM in real-time
- **iftop** - See network traffic
- **Server logs** - Count requests

**On attacker (main laptop):**
- **Dashboard** - Display target metrics remotely
- **Docker stats** - Monitor container resource usage

---

## 🔐 Safety Measures

**Network Isolation:**
- Use **private network** only (192.168.x.x)
- No internet exposure
- Router stays disconnected from outside (optional extra safety)

**Resource Limits:**
- Set max requests/second per container
- Prevent accidental overload
- Emergency stop scripts

**Testing Steps:**
1. Start with **1 attacker container**
2. Verify target responds correctly
3. Scale to **5 containers**
4. Measure impact
5. Gradually increase

---

## 📊 What Success Looks Like

**Phase 1 (5 containers):**
- Old laptop handles easily
- Response times stay low (<100ms)
- CPU maybe 20-30%

**Phase 2 (15 containers):**
- Old laptop struggles a bit
- Response times increase (200-500ms)
- CPU 60-70%

**Phase 3 (25+ containers):**
- Old laptop maxed out
- Response times spike (1000ms+)
- CPU 90%+ or server stops responding

**This teaches you:** Where the breaking point is!

---

## 🛠️ What You'll Actually Do (When We Code)

**On old laptop:**
1. Install Ubuntu/Nginx
2. Create simple test page
3. Start monitoring tools
4. Note its IP address

**On main laptop:**
1. Create Dockerfile for attacker
2. Python script to send HTTP requests
3. Docker Compose to spawn 20 containers
4. Point all containers at old laptop's IP
5. Dashboard to watch everything

---

## 💡 Key Concepts

**Why this setup is perfect:**
- You're simulating a **distributed attack** (many sources → one target)
- You see **real bottlenecks** (network, CPU, memory)
- It's **safe** (private network only)
- It's **scalable** (1 to 30+ containers)

---

## ❓ Understanding Checklist

Before proceeding, make sure you understand:
1. ✅ **Why** we're using the old laptop as target
2. ✅ **What** the target server needs to do
3. ✅ **How** the network connection works
4. ✅ **What** we'll monitor during attacks

---

## 📝 Next Topics to Cover

- Attacker Docker container architecture
- Python scripts for generating load
- Docker Compose orchestration
- Dashboard for real-time monitoring
- Different attack types (HTTP flood, slowloris, etc.)

---

**Status:** Concept explanation complete  
**Next Step:** Discuss attacker architecture

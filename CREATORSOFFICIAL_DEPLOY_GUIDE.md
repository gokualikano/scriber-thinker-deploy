# 🚀 Deploy to creatorsofficial.co - FREE Setup

## 🌐 **Your Professional URLs:**
- **Scriber:** `https://scriber.creatorsofficial.co`
- **Thinker:** `https://thinker.creatorsofficial.co`
- **Cost:** $0 (using existing domain)

---

## 🚀 **DEPLOYMENT STEPS:**

### **Step 1: Deploy to Railway (Web Dashboard)**

1. **Go to:** `railway.app`
2. **Login** with GitHub/Google
3. **Click "New Project"** → **"Deploy from GitHub"**
4. **Connect/Import this repository**

### **Step 2: Configure Scriber App**
1. **Select Scriber folder** for deployment
2. **Add Environment Variables:**
   ```
   ACCESS_PASSWORD=scriber2024
   SECRET_KEY=super-secret-scriber-production-key-2026
   PORT=8586
   ```
3. **Deploy** → Get Railway URL (like `scriber-xyz.railway.app`)

### **Step 3: Configure Thinker App**  
1. **Create second project** → Deploy Thinker folder
2. **Add Environment Variables:**
   ```
   ACCESS_PASSWORD=thinker2024
   SECRET_KEY=super-secret-thinker-production-key-2026
   PORT=8585
   ```
3. **Deploy** → Get Railway URL (like `thinker-abc.railway.app`)

### **Step 4: Add Custom Domains in Railway**
1. **Scriber Project** → Settings → Domains → Add `scriber.creatorsofficial.co`
2. **Thinker Project** → Settings → Domains → Add `thinker.creatorsofficial.co`
3. **Railway shows DNS targets** (like `xyz.railway.app`)

---

## 🌐 **DNS SETUP (GoDaddy):**

### **Login to GoDaddy DNS Management:**
1. Go to `godaddy.com` → My Products → DNS
2. **Add these CNAME records:**

```
Type: CNAME
Name: scriber
Value: [Railway-provided-URL] (without https://)
TTL: 1 Hour

Type: CNAME  
Name: thinker
Value: [Railway-provided-URL] (without https://)
TTL: 1 Hour
```

**Example:**
```
CNAME | scriber | scriber-xyz.railway.app | 1 Hour
CNAME | thinker  | thinker-abc.railway.app | 1 Hour
```

---

## ⚡ **QUICK START:**

1. **Deploy:** railway.app → New Project → GitHub
2. **Get Railway URLs** from both deployments  
3. **Add custom domains** in Railway dashboard
4. **Update DNS** in GoDaddy with Railway targets
5. **Wait 5-10 minutes** for DNS propagation

---

## 🔒 **FINAL RESULT:**

✅ **Live URLs with SSL:**
- `https://scriber.creatorsofficial.co` (password: scriber2024)
- `https://thinker.creatorsofficial.co` (password: thinker2024)

✅ **Professional branded URLs**
✅ **Free SSL certificates** 
✅ **Password protected**
✅ **$0/month hosting cost**

---

## 📱 **Team Access:**

Share these with your team:
- **Scriber:** https://scriber.creatorsofficial.co (password: scriber2024)
- **Thinker:** https://thinker.creatorsofficial.co (password: thinker2024)

They can access from any device - no setup needed!

---

## 🔧 **Change Passwords Later:**

In Railway dashboard → Your Project → Variables:
```
ACCESS_PASSWORD=your-new-secure-password
```

**Total setup time: 10 minutes** ⏱️
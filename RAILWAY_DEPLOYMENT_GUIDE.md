# 🚀 Railway Deployment Guide - FREE Hosting

## ✅ READY TO DEPLOY

Both **Scriber** and **Thinker** apps are now **password-protected** and ready for FREE Railway hosting!

### 🔒 **CURRENT SECURITY:**
- **Scriber password:** `scriber2024`
- **Thinker password:** `thinker2024`
- Login page protects all routes
- Session-based authentication

---

## 🚀 **OPTION 1: Auto Deploy (Easy)**

Run the deployment script I created:

```bash
./deploy-to-railway.sh
```

Follow the prompts and you'll be live in 5 minutes!

---

## 🛠️ **OPTION 2: Manual Deploy (Step by Step)**

### **Step 1: Login to Railway**
```bash
railway login
```
- This opens your browser to login with GitHub/Google
- Authorize Railway access

### **Step 2: Deploy Scriber**
```bash
cd scriber
railway init
# Enter project name: scriber-app
railway variables set ACCESS_PASSWORD=scriber2024
railway variables set SECRET_KEY=production-secret-$(date +%s)
railway deploy
```

### **Step 3: Deploy Thinker**
```bash
cd ../thinker
railway init  
# Enter project name: thinker-app
railway variables set ACCESS_PASSWORD=thinker2024
railway variables set SECRET_KEY=production-secret-$(date +%s)
railway deploy
```

### **Step 4: Get Your URLs**
```bash
railway status
```
- Copy the live URLs Railway gives you
- Test both apps with the passwords above

---

## 🌐 **CUSTOM DOMAIN SETUP (Optional)**

### **Option A: Railway Subdomain (Free)**
- Railway automatically gives you: `yourapp.railway.app`
- No additional setup needed

### **Option B: Your Domain (Free)**
1. Go to Railway Dashboard → Your Project → Settings → Domains
2. Add custom domain: `scriber.yourdomain.com`
3. Point your DNS CNAME to Railway's domain
4. SSL certificate auto-generated

---

## 🔐 **CHANGE PASSWORDS (Recommended)**

After deployment, update passwords:

```bash
# For Scriber
cd scriber
railway variables set ACCESS_PASSWORD=your-new-secure-password

# For Thinker  
cd thinker
railway variables set ACCESS_PASSWORD=your-new-secure-password
```

Redeploy after changing:
```bash
railway deploy
```

---

## 📊 **COST: $0/month**

- **Railway Free Tier:** $0
- **SSL Certificates:** Free (auto)
- **Custom Domain:** Free (if you own domain)
- **Total Monthly Cost:** **$0**

---

## 🎯 **FINAL RESULT**

After deployment you'll have:

- **🔒 https://scriber-app.railway.app** (password: `scriber2024`)
- **🔒 https://thinker-app.railway.app** (password: `thinker2024`)

Or with custom domain:
- **🔒 https://scriber.yourdomain.com** 
- **🔒 https://thinker.yourdomain.com**

**Perfect for client tools - professional, secure, and FREE!** 🎉

---

## ⚡ **QUICK START**

1. Run: `./deploy-to-railway.sh`
2. Follow prompts
3. Get URLs from Railway dashboard  
4. Share URLs + passwords with team
5. Done! 

**Total time: 5 minutes** ⏱️
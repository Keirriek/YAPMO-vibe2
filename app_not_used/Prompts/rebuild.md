# YAPMO Dev Container Rebuild Procedure

## 🔄 **Veilige Rebuild met NFS Ondersteuning**

Dit document beschrijft hoe je een Dev Container rebuild kunt doen terwijl NFS mount configuratie behouden blijft.

---

## 📋 **Rebuild Procedure**

### **Stap 1: Voorbereiding**
- **Cursor NIET sluiten** (blijf in container)
- **Open Windows PowerShell** (niet in container/WSL)
- **Navigate naar project directory:**
  ```powershell
  cd D:\Python-Mars\YAPMO-dev\YAPMO-V5
  ```

### **Stap 2: Rebuild Script Starten**
```powershell
.\rebuild-devcontainer.ps1
```

### **Stap 3: Script Automatisering**
Het script voert automatisch uit:

1. ✅ **NFS mount uitschakelen** (plaatst `#` in docker-compose.yml)
2. ✅ **Instructies geven** voor rebuild
3. ✅ **Wachten op rebuild** voltooiing
4. ✅ **NFS mount inschakelen** (verwijdert `#` uit docker-compose.yml)

### **Stap 4: Rebuild Uitvoeren** 
**Wanneer script daarom vraagt:**

1. **In Cursor:** `Ctrl+Shift+P`
2. **Type:** "Dev Containers: Rebuild Container"
3. **Selecteer:** "Dev Containers: Rebuild Container"
4. **Wacht tot build voltooid**
5. **Druk Enter in PowerShell** om door te gaan

### **Stap 5: Container Herstart voor NFS**
**Na script voltooiing:**

1. **Cursor sluiten**
2. **Container stopt automatisch**
3. **Cursor openen**
4. **Container start automatisch met NFS**

---

## ⚠️ **Belangrijke Opmerkingen**

### **✅ DO's:**
- Gebruik altijd het script voor rebuilds
- Wacht tot script compleet is voordat je Cursor sluit
- Check `/mnt/nas_test/` na herstart voor NFS werking

### **❌ DON'Ts:**
- Geen handmatige `#` plaatsing nodig - script doet dit
- Niet rebuilden zonder script (NFS mount errors)
- Niet container forceren tijdens script uitvoering

---

## 🛠️ **Troubleshooting**

### **Script niet gevonden:**
```powershell
# Check of je in juiste directory bent
pwd
# Moet zijn: D:\Python-Mars\YAPMO-dev\YAPMO-V5

# Check of script bestaat
ls rebuild-devcontainer.ps1
```

### **Script execution policy error:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### **NFS werkt niet na rebuild:**
1. Check container logs: `docker logs yapmo-development`
2. Controleer NFS mount: `ls -la /mnt/` (in container)
3. Handmatig container restart indien nodig

### **Build errors:**
1. Check Docker Desktop status
2. Restart Docker Desktop indien nodig  
3. Clean Docker cache: `docker system prune -f`

---

## 📁 **Bestand Locaties**

- **Rebuild Script:** `rebuild-devcontainer.ps1`
- **Docker Compose:** `.devcontainer/docker-compose.yml`
- **Dev Container Config:** `.devcontainer/devcontainer.json`
- **Dockerfile:** `.devcontainer/Dockerfile`

---

## 🎯 **Resultaat na Succesvolle Rebuild**

✅ **Dev Container** - Volledig herbouwd  
✅ **Poetry Dependencies** - Geïnstalleerd  
✅ **NFS Mount** - Actief in `/mnt/nas_test/`  
✅ **Workspace** - Correct in `/workspaces`  
✅ **YAPMO App** - Klaar voor ontwikkeling  

---

*Laatst bijgewerkt: Augustus 2025*

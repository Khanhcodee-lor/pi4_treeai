# GitHub Auto Deploy to Pi4

Muc tieu cua flow nay la: ban code tren laptop, `git push` len GitHub, va chinh Pi4 tu keo code moi ve roi restart service. Cach nay khong can SSH inbound vao Pi moi lan deploy.

## 1. Chuan bi Pi4 mot lan

```bash
sudo apt update
sudo apt install -y git rsync python3-venv python3-pip
mkdir -p /home/khanhpi/project
cd /home/khanhpi/project
git clone <repo-github-cua-ban> pi4_treeai
cd pi4_treeai
```

Tao file bien moi truong cho service AI:

```bash
sudo cp deploy/pi4-tree-ai.env.example /etc/pi4-tree-ai.env
sudo nano /etc/pi4-tree-ai.env
```

Neu user chay GitHub runner la `khanhpi`, tao sudoers de workflow duoc quyen cap nhat service:

```bash
sudo cp deploy/pi4-github-runner.sudoers.example /etc/sudoers.d/pi4-github-runner
sudo chmod 440 /etc/sudoers.d/pi4-github-runner
sudo visudo -cf /etc/sudoers.d/pi4-github-runner
```

## 2. Cai service tren Pi4

```bash
chmod +x setup_tree_ai_autostart.sh setup_bt_autostart.sh
./setup_tree_ai_autostart.sh
./setup_bt_autostart.sh
```

Tree AI service dung file `deploy/pi4-tree-ai.service` va provisioning Bluetooth dung `deploy/pi4-bt-provision.service`.

## 3. Cai GitHub Actions self-hosted runner tren chinh Pi4

Trong repo GitHub cua ban:

1. Vao `Settings` -> `Actions` -> `Runners`
2. Chon `New self-hosted runner`
3. Chon Linux ARM/ARM64 dung voi Pi cua ban
4. Chay cac lenh GitHub cung cap ngay tren Pi
5. Khi cau hinh runner, them label `pi4`

Workflow trong repo la `.github/workflows/deploy-pi.yml` va chi chay khi runner co label `pi4`.

## 4. Co che deploy

Moi lan ban push len branch `main`, GitHub Actions se chay `deploy/deploy_pi.sh` ngay tren Pi. Script nay se:

- `rsync` code moi vao `/home/khanhpi/project/pi4_treeai`
- giu lai `myenv`, `.env`, `firebase_key.json`, `detections/`, `snapshots/`
- cai lai dependency tu `requirements.txt`
- cap nhat file service da cai trong `/etc/systemd/system`
- restart `pi4-tree-ai.service`
- restart `pi4-bt-provision.service` neu service do dang duoc quan ly tren Pi

## 5. Cach dung hang ngay

Tren laptop:

```bash
git add .
git commit -m "your change"
git push origin main
```

Sau do vao tab `Actions` tren GitHub de xem log deploy.

## 6. Luu y van hanh

- Neu Pi khong thay job, kiem tra runner con online khong
- Neu workflow bao loi `sudo: a password is required`, kiem tra lai file sudoers
- Neu ban khong muon deploy tu `main`, sua branch trong `.github/workflows/deploy-pi.yml`
- Neu project directory tren Pi khong phai `/home/khanhpi/project/pi4_treeai`, sua bien `PROJECT_DIR` trong workflow

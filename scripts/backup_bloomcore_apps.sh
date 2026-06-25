#!/bin/bash
# backup_bloomcore_apps.sh
# run with: bash ~/SkyCorePi/scripts/backup_bloomcore_apps.sh
# description: Copy live BloomCore bench apps into SkyCorePi and commit them.

set -e

cd ~/SkyCorePi

mkdir -p apps

cp -r ~/SkyCam apps/
cp -r ~/HarnessMap apps/
cp -r ~/BloomRestore apps/

git add apps docs hardware scripts README.md .gitignore
git commit -m "Backup BloomCore bench apps" || echo "No changes to commit."
git push

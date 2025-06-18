#!/bin/bash

echo "🚀 準備部署到 Zeabur..."

# 檢查是否有未提交的變更
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 發現未提交的變更，正在提交..."
    git add .
    git commit -m "Update for Zeabur deployment"
fi

# 推送到 GitHub
echo "📤 推送到 GitHub..."
git push origin main

echo "✅ 部署準備完成！"
echo ""
echo "📋 下一步："
echo "1. 前往 https://zeabur.com"
echo "2. 註冊/登入帳號"
echo "3. 點擊 'New Project'"
echo "4. 選擇 'GitHub' 並連接您的 GitHub 帳號"
echo "5. 選擇此專案 (car4)"
echo "6. 點擊 'Deploy'"
echo ""
echo "🌐 部署完成後，您就可以透過 Zeabur 提供的網址訪問應用程式了！" 
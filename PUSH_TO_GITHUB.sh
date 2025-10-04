#!/bin/bash

echo "🚀 GitHub Push Helper Script"
echo "=============================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "❌ Git not initialized. Run: git init"
    exit 1
fi

# Check if there are commits
if ! git log -1 > /dev/null 2>&1; then
    echo "❌ No commits found. Run: git commit -m 'Initial commit'"
    exit 1
fi

echo "✅ Git repository is ready"
echo ""

# Ask for GitHub username
read -p "Enter your GitHub username: " username

if [ -z "$username" ]; then
    echo "❌ Username cannot be empty"
    exit 1
fi

repo_name="unified-ai-chat-system"
echo ""
echo "Repository will be created at:"
echo "https://github.com/$username/$repo_name"
echo ""

# Check if gh CLI is available
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI detected"
    echo ""
    read -p "Create repository using GitHub CLI? (y/n): " use_gh
    
    if [ "$use_gh" = "y" ] || [ "$use_gh" = "Y" ]; then
        echo ""
        echo "Creating repository..."
        gh repo create $repo_name --public --source=. --remote=origin --description "AI-powered chat system for absence management and SOW generation using Gemini 2.0 Flash"
        
        echo ""
        echo "Pushing code..."
        git push -u origin master
        
        echo ""
        echo "✅ Done! Your repository is live at:"
        echo "https://github.com/$username/$repo_name"
        exit 0
    fi
fi

# Manual setup
echo "Manual Setup Instructions:"
echo "=========================="
echo ""
echo "1. Go to: https://github.com/new"
echo "2. Repository name: $repo_name"
echo "3. Description: AI-powered chat system for absence management and SOW generation"
echo "4. Choose Public or Private"
echo "5. DO NOT initialize with README"
echo "6. Click 'Create repository'"
echo ""
echo "Then run these commands:"
echo ""
echo "git remote add origin https://github.com/$username/$repo_name.git"
echo "git branch -M main"
echo "git push -u origin main"
echo ""
echo "Or with SSH:"
echo "git remote add origin git@github.com:$username/$repo_name.git"
echo "git branch -M main"
echo "git push -u origin main"
echo ""

# Offer to copy commands
read -p "Copy HTTPS commands to clipboard? (y/n): " copy_cmd

if [ "$copy_cmd" = "y" ] || [ "$copy_cmd" = "Y" ]; then
    if command -v pbcopy &> /dev/null; then
        echo "git remote add origin https://github.com/$username/$repo_name.git
git branch -M main
git push -u origin main" | pbcopy
        echo "✅ Commands copied to clipboard!"
    elif command -v xclip &> /dev/null; then
        echo "git remote add origin https://github.com/$username/$repo_name.git
git branch -M main
git push -u origin main" | xclip -selection clipboard
        echo "✅ Commands copied to clipboard!"
    else
        echo "⚠️  Clipboard tool not found. Copy commands manually."
    fi
fi

echo ""
echo "📖 For detailed instructions, see: GITHUB_SETUP.md"

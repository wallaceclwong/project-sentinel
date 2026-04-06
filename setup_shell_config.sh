#!/bin/bash
# PROJECT SENTINEL - Shell Configuration Setup Script
# Optimizes remote development environment for Windsurf

set -e

echo "🚀 Setting up PROJECT SENTINEL shell configuration..."

# Copy custom bash profile
echo "📋 Installing custom bash profile..."
cp .bash_profile_sentinel /home/ubuntu/project-sentinel/
chown ubuntu:ubuntu /home/ubuntu/project-sentinel/.bash_profile_sentinel

# Update Windsurf remote configuration
echo "🔧 Updating Windsurf remote configuration..."
cp .windsurf/remote.json /home/ubuntu/project-sentinel/.windsurf/

# Install git completion if not present
if [ ! -f /etc/bash_completion.d/git ]; then
    echo "📦 Installing git completion..."
    apt-get update && apt-get install -y git bash-completion
fi

# Create sentinel command shortcuts
echo "⚡ Creating system-wide sentinel commands..."
cat > /usr/local/bin/sentinel-info << 'EOF'
#!/bin/bash
cd /home/ubuntu/project-sentinel && source .bash_profile_sentinel && sentinel-info
EOF

cat > /usr/local/bin/sentinel-dev << 'EOF'
#!/bin/bash
cd /home/ubuntu/project-sentinel && source .bash_profile_sentinel && sentinel-dev
EOF

cat > /usr/local/bin/test-sentinel << 'EOF'
#!/bin/bash
cd /home/ubuntu/project-sentinel && source .bash_profile_sentinel && test-sentinel
EOF

chmod +x /usr/local/bin/sentinel-info /usr/local/bin/sentinel-dev /usr/local/bin/test-sentinel

echo "✅ Shell configuration setup complete!"
echo ""
echo "🎯 New features available:"
echo "  • Enhanced colored prompt with git status"
echo "  • Project-specific aliases (sentinel, logs, venv, etc.)"
echo "  • System-wide commands (sentinel-info, sentinel-dev, test-sentinel)"
echo "  • Auto virtual environment activation"
echo "  • Improved history management"
echo ""
echo "🔄 Restart your Windsurf connection to apply changes."

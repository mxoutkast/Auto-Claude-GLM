#!/bin/bash
# Auto-Claude GLM Setup Script
# Configures GLM as the default AI provider

echo "========================================"
echo "  Auto-Claude GLM Setup"
echo "  100x cheaper than Claude!"
echo "========================================"
echo ""

# Check if .env exists
ENV_FILE="apps/backend/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file..."
    touch "$ENV_FILE"
fi

# Check current configuration
if grep -q "^AI_PROVIDER=" "$ENV_FILE" && grep -q "^ZHIPUAI_API_KEY=" "$ENV_FILE"; then
    echo "✓ GLM is already configured!"
    echo ""
    echo "Current settings:"
    grep "^AI_PROVIDER=" "$ENV_FILE" | sed 's/^/  /'
    echo "  ZHIPUAI_API_KEY=***"
    echo ""
    
    read -p "Do you want to reconfigure? (y/N): " reconfigure
    if [[ ! "$reconfigure" =~ ^[Yy]$ ]]; then
        echo ""
        echo "Setup cancelled."
        exit 0
    fi
fi

# Get API key
echo "Get your GLM API key from:"
echo "  • Z.AI: https://api.z.ai"
echo "  • ZhipuAI: https://open.bigmodel.cn"
echo ""

read -p "Enter your GLM API key: " apiKey

if [ -z "$apiKey" ]; then
    echo ""
    echo "✗ API key is required!"
    exit 1
fi

# Update or add AI_PROVIDER
echo ""
echo "Configuring GLM..."

if grep -q "^AI_PROVIDER=" "$ENV_FILE"; then
    sed -i.bak 's/^AI_PROVIDER=.*/AI_PROVIDER=glm/' "$ENV_FILE"
else
    echo "AI_PROVIDER=glm" >> "$ENV_FILE"
fi

# Update or add ZHIPUAI_API_KEY
if grep -q "^ZHIPUAI_API_KEY=" "$ENV_FILE"; then
    sed -i.bak "s/^ZHIPUAI_API_KEY=.*/ZHIPUAI_API_KEY=$apiKey/" "$ENV_FILE"
else
    echo "ZHIPUAI_API_KEY=$apiKey" >> "$ENV_FILE"
fi

# Remove backup file
rm -f "$ENV_FILE.bak"

echo ""
echo "========================================"
echo "  ✓ GLM Configuration Complete!"
echo "========================================"
echo ""
echo "Configuration saved to: $ENV_FILE"
echo ""
echo "Next steps:"
echo "  1. Install ZhipuAI SDK:"
echo "     cd apps/backend"
echo "     source .venv/bin/activate"
echo "     pip install zhipuai"
echo ""
echo "  2. Start the app:"
echo "     npm run dev"
echo ""
echo "  3. Select GLM-4.7 profile in agent settings"
echo ""
echo "Cost savings: ~100x cheaper than Claude!"
echo ""

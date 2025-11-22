#!/bin/bash
# Juice ShopからJWTトークンを取得するヘルパースクリプト

set -e

# 色の定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# デフォルト値
JUICE_SHOP_URL="${JUICE_SHOP_URL:-http://localhost:3000}"
EMAIL="${1:-admin@juice-sh.op}"
PASSWORD="${2:-admin123}"

echo -e "${BLUE}=== Juice Shop JWT Token Retrieval ===${NC}"
echo -e "${YELLOW}URL: ${JUICE_SHOP_URL}${NC}"
echo -e "${YELLOW}Email: ${EMAIL}${NC}"
echo ""

# Juice Shopの起動確認
echo -e "${BLUE}Checking if Juice Shop is running...${NC}"
if ! curl -s -f "${JUICE_SHOP_URL}/api/version" > /dev/null; then
    echo -e "${YELLOW}⚠ Juice Shop is not running or not accessible at ${JUICE_SHOP_URL}${NC}"
    echo -e "${YELLOW}Please start it with: docker compose up -d juice-shop${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Juice Shop is running${NC}"
echo ""

# ログインしてトークンを取得
echo -e "${BLUE}Attempting to login and retrieve JWT token...${NC}"
RESPONSE=$(curl -s -X POST "${JUICE_SHOP_URL}/rest/user/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}")

# トークンを抽出
TOKEN=$(echo "$RESPONSE" | jq -r '.authentication.token // empty')

if [ -z "$TOKEN" ]; then
    echo -e "${YELLOW}⚠ Failed to retrieve token. Response:${NC}"
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
    echo ""
    echo -e "${YELLOW}Note: Default credentials might not work. Try registering a new user first:${NC}"
    echo -e "  1. Visit ${JUICE_SHOP_URL}/#/register"
    echo -e "  2. Create a new account"
    echo -e "  3. Run this script with your credentials: $0 your-email@example.com your-password"
    exit 1
fi

echo -e "${GREEN}✓ Successfully retrieved JWT token${NC}"
echo ""
echo -e "${BLUE}JWT Token:${NC}"
echo "$TOKEN"
echo ""
echo -e "${BLUE}Token Details:${NC}"
# JWTをデコード（ヘッダーとペイロードのみ）
HEADER=$(echo "$TOKEN" | cut -d. -f1)
PAYLOAD=$(echo "$TOKEN" | cut -d. -f2)

echo -e "${YELLOW}Header:${NC}"
echo "$HEADER" | base64 -d 2>/dev/null | jq '.' 2>/dev/null || echo "(Failed to decode)"

echo -e "${YELLOW}Payload:${NC}"
echo "$PAYLOAD" | base64 -d 2>/dev/null | jq '.' 2>/dev/null || echo "(Failed to decode)"

echo ""
echo -e "${GREEN}=== Usage Examples ===${NC}"
echo ""
echo -e "${BLUE}1. Run full scan with Bearer authentication:${NC}"
echo "PYTHONPATH=src uv run python -m scanner.main full http://juice-shop:3000 \\"
echo "  --auth-type bearer \\"
echo "  --auth-token \"${TOKEN}\" \\"
echo "  --network web-sec-scanner_default \\"
echo "  --ajax-spider \\"
echo "  --max-duration 10"
echo ""
echo -e "${BLUE}2. Run automation scan with Bearer authentication:${NC}"
echo "PYTHONPATH=src uv run python -m scanner.main automation http://juice-shop:3000 \\"
echo "  --auth-type bearer \\"
echo "  --auth-token \"${TOKEN}\" \\"
echo "  --network web-sec-scanner_default \\"
echo "  --max-duration 5"
echo ""
echo -e "${BLUE}3. Test with curl:${NC}"
echo "curl -H \"Authorization: Bearer ${TOKEN}\" \\"
echo "  ${JUICE_SHOP_URL}/rest/basket/1"
echo ""
echo -e "${YELLOW}Note: The token might expire after some time. Re-run this script to get a fresh token.${NC}"

#!/usr/bin/env bash
# ============================================================================
# AIU Church Bulletin API — One-Click VPS Deploy Script
# Tested on: Ubuntu 22.04 / 24.04 (Hostinger VPS)
#
# Usage:
#   1. SSH into your VPS:  ssh root@your-vps-ip
#   2. Upload this repo:   scp -r church_bulletin/ root@your-vps-ip:/root/
#   3. Run the script:     cd /root/church_bulletin && bash deploy.sh
#
# What this script does:
#   - Installs Docker & Docker Compose
#   - Configures firewall (UFW)
#   - Generates secure database password and JWT secret
#   - Sets up Nginx reverse proxy with free SSL (Let's Encrypt)
#   - Starts the API + PostgreSQL + Nginx
#   - Runs database migrations and seeds data
#   - Creates student accounts
#   - Prints the URL and credentials
# ============================================================================

set -euo pipefail

# ---- Colors ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }
ask()  { echo -en "${CYAN}[?]${NC} $1"; }

# ---- Must be root ----
if [[ $EUID -ne 0 ]]; then
    err "Run this script as root: sudo bash deploy.sh"
fi

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

echo ""
echo "============================================="
echo "  AIU Church Bulletin API — VPS Deployment"
echo "============================================="
echo ""

# ============================================================================
# Step 1: Collect configuration
# ============================================================================

# Domain
ask "Enter your domain name (e.g. bulletin.apiu.edu) or press Enter for IP-only: "
read -r DOMAIN
DOMAIN="${DOMAIN:-}"

# Student count
ask "How many student accounts to create? [30]: "
read -r STUDENT_COUNT
STUDENT_COUNT="${STUDENT_COUNT:-30}"

# Email for SSL
if [[ -n "$DOMAIN" ]]; then
    ask "Email for Let's Encrypt SSL certificate: "
    read -r SSL_EMAIL
    SSL_EMAIL="${SSL_EMAIL:-admin@${DOMAIN}}"
fi

# Generate secrets
DB_USER="bulletin"
DB_PASSWORD="$(openssl rand -hex 16)"
DB_NAME="church_bulletin"
SECRET_KEY="$(openssl rand -hex 32)"

SERVER_IP="$(curl -4 -s ifconfig.me || hostname -I | awk '{print $1}')"

echo ""
log "Configuration:"
echo "    Server IP:       $SERVER_IP"
echo "    Domain:          ${DOMAIN:-none (IP-only mode)}"
echo "    Student count:   $STUDENT_COUNT"
echo "    DB user:         $DB_USER"
echo "    DB name:         $DB_NAME"
echo ""

ask "Continue? (yes/no): "
read -r CONFIRM
[[ "$CONFIRM" == "yes" ]] || { echo "Cancelled."; exit 0; }

echo ""

# ============================================================================
# Step 2: Install system dependencies
# ============================================================================

log "Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

# Install Docker if not present
if ! command -v docker &>/dev/null; then
    log "Installing Docker..."
    apt-get install -y -qq ca-certificates curl gnupg lsb-release
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
      https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
      > /etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    log "Docker installed."
else
    log "Docker already installed."
fi

# ============================================================================
# Step 3: Configure firewall
# ============================================================================

log "Configuring firewall (UFW)..."
apt-get install -y -qq ufw
ufw --force reset >/dev/null 2>&1
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
log "Firewall configured (SSH, HTTP, HTTPS allowed)."

# ============================================================================
# Step 4: Write environment file
# ============================================================================

log "Writing .env file..."
cat > "$APP_DIR/.env" <<EOF
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME
SECRET_KEY=$SECRET_KEY
DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@db:5432/$DB_NAME
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
EOF
chmod 600 "$APP_DIR/.env"
log ".env file created."

# ============================================================================
# Step 5: Configure Nginx
# ============================================================================

if [[ -n "$DOMAIN" ]]; then
    log "Configuring Nginx for domain: $DOMAIN"
    sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" "$APP_DIR/nginx.conf"
else
    log "Configuring Nginx for IP-only access (no SSL)..."
    cat > "$APP_DIR/nginx.conf" <<'NGINX'
server {
    listen 80;
    server_name _;

    client_max_body_size 10M;

    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX
fi

# ============================================================================
# Step 6: Get SSL certificate (if domain provided)
# ============================================================================

if [[ -n "$DOMAIN" ]]; then
    log "Obtaining SSL certificate for $DOMAIN..."

    # Start with HTTP-only nginx first for the ACME challenge
    cat > "$APP_DIR/nginx.conf.temp" <<NGINX_TEMP
server {
    listen 80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/lib/letsencrypt;
    }

    location / {
        return 200 'Setting up...';
        add_header Content-Type text/plain;
    }
}
NGINX_TEMP

    # Start only nginx temporarily for cert
    docker compose -f docker-compose.prod.yml run -d --rm \
        -v "$APP_DIR/nginx.conf.temp:/etc/nginx/conf.d/default.conf:ro" \
        -p 80:80 \
        nginx 2>/dev/null || true

    # Get the certificate
    docker run --rm \
        -v certbot-etc:/etc/letsencrypt \
        -v certbot-var:/var/lib/letsencrypt \
        -p 80:80 \
        certbot/certbot certonly \
        --standalone \
        --preferred-challenges http \
        --email "$SSL_EMAIL" \
        --agree-tos \
        --no-eff-email \
        -d "$DOMAIN" 2>&1 || {
            warn "SSL certificate failed. Falling back to HTTP-only."
            DOMAIN=""
            cat > "$APP_DIR/nginx.conf" <<'NGINX_FALLBACK'
server {
    listen 80;
    server_name _;
    client_max_body_size 10M;
    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_FALLBACK
        }

    # Stop temporary nginx
    docker stop $(docker ps -q --filter "ancestor=nginx:alpine") 2>/dev/null || true
    rm -f "$APP_DIR/nginx.conf.temp"

    if [[ -n "$DOMAIN" ]]; then
        log "SSL certificate obtained for $DOMAIN."
    fi
else
    # Remove SSL-related services from compose for IP-only mode
    log "IP-only mode: removing certbot from compose..."
fi

# ============================================================================
# Step 7: Build and start services
# ============================================================================

log "Building and starting services..."

# Use production compose, but remove certbot block if no domain
COMPOSE_FILE="docker-compose.prod.yml"

if [[ -z "$DOMAIN" ]]; then
    # For IP-only, strip SSL from nginx config and remove certbot
    # Create a simplified compose without certbot and SSL volumes
    cat > "$APP_DIR/docker-compose.deploy.yml" <<DEPLOY
services:
  db:
    image: postgres:16
    restart: always
    env_file: .env
    environment:
      POSTGRES_USER: \${DB_USER:-bulletin}
      POSTGRES_PASSWORD: \${DB_PASSWORD}
      POSTGRES_DB: \${DB_NAME:-church_bulletin}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \${DB_USER:-bulletin} -d \${DB_NAME:-church_bulletin}"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - internal

  api:
    build: .
    restart: always
    env_file: .env
    environment:
      DATABASE_URL: postgresql+asyncpg://\${DB_USER:-bulletin}:\${DB_PASSWORD}@db:5432/\${DB_NAME:-church_bulletin}
      SECRET_KEY: \${SECRET_KEY}
      ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: "60"
      REFRESH_TOKEN_EXPIRE_DAYS: "7"
    depends_on:
      db:
        condition: service_healthy
    networks:
      - internal
      - web

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - api
    networks:
      - web

volumes:
  pgdata:

networks:
  internal:
  web:
DEPLOY
    COMPOSE_FILE="docker-compose.deploy.yml"
fi

docker compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
docker compose -f "$COMPOSE_FILE" up -d --build

log "Services started. Waiting for database to be ready..."
sleep 5

# ============================================================================
# Step 8: Run migrations and seed
# ============================================================================

log "Running database migrations..."
docker compose -f "$COMPOSE_FILE" exec -T api alembic upgrade head

log "Seeding database with bulletin data..."
docker compose -f "$COMPOSE_FILE" exec -T api python seed.py

# ============================================================================
# Step 9: Create student accounts
# ============================================================================

if [[ "$STUDENT_COUNT" -gt 0 ]]; then
    log "Creating $STUDENT_COUNT student accounts..."
    docker compose -f "$COMPOSE_FILE" exec -T api \
        python admin_tools.py create-students --count "$STUDENT_COUNT" --prefix student

    # Copy the generated CSV out of the container
    CONTAINER_ID=$(docker compose -f "$COMPOSE_FILE" ps -q api)
    docker cp "$CONTAINER_ID:/app/student_accounts.csv" "$APP_DIR/student_accounts.csv" 2>/dev/null || true
    log "Student accounts saved to $APP_DIR/student_accounts.csv"
fi

# ============================================================================
# Step 10: Set up auto-renewal for SSL
# ============================================================================

if [[ -n "$DOMAIN" ]]; then
    log "Setting up SSL auto-renewal cron job..."
    (crontab -l 2>/dev/null; echo "0 3 * * * cd $APP_DIR && docker compose -f $COMPOSE_FILE run --rm certbot renew --quiet && docker compose -f $COMPOSE_FILE exec -T nginx nginx -s reload") | crontab -
    log "SSL will auto-renew daily at 3 AM."
fi

# ============================================================================
# Step 11: Create management shortcuts
# ============================================================================

cat > /usr/local/bin/bulletin <<'SHORTCUT'
#!/usr/bin/env bash
APP_DIR="APP_DIR_PLACEHOLDER"
COMPOSE_FILE="COMPOSE_FILE_PLACEHOLDER"
cd "$APP_DIR"

case "${1:-help}" in
    status)   docker compose -f "$COMPOSE_FILE" ps ;;
    logs)     docker compose -f "$COMPOSE_FILE" logs -f --tail=50 "${2:-api}" ;;
    restart)  docker compose -f "$COMPOSE_FILE" restart ;;
    stop)     docker compose -f "$COMPOSE_FILE" down ;;
    start)    docker compose -f "$COMPOSE_FILE" up -d ;;
    reset)    docker compose -f "$COMPOSE_FILE" exec -T api python seed.py && \
              echo "Database reset to seed data." ;;
    users)    docker compose -f "$COMPOSE_FILE" exec -T api python admin_tools.py list-users ;;
    add-students)
              COUNT="${2:-10}"
              docker compose -f "$COMPOSE_FILE" exec -T api \
                  python admin_tools.py create-students --count "$COUNT" --prefix student
              CONTAINER_ID=$(docker compose -f "$COMPOSE_FILE" ps -q api)
              docker cp "$CONTAINER_ID:/app/student_accounts.csv" "$APP_DIR/student_accounts.csv"
              echo "Accounts saved to $APP_DIR/student_accounts.csv"
              ;;
    *)
        echo "AIU Church Bulletin API Management"
        echo ""
        echo "Usage: bulletin <command>"
        echo ""
        echo "  status          Show running services"
        echo "  logs [service]  Follow logs (default: api)"
        echo "  restart         Restart all services"
        echo "  stop            Stop all services"
        echo "  start           Start all services"
        echo "  reset           Reset database to seed data"
        echo "  users           List all user accounts"
        echo "  add-students N  Create N more student accounts"
        ;;
esac
SHORTCUT

sed -i "s|APP_DIR_PLACEHOLDER|$APP_DIR|g" /usr/local/bin/bulletin
sed -i "s|COMPOSE_FILE_PLACEHOLDER|$COMPOSE_FILE|g" /usr/local/bin/bulletin
chmod +x /usr/local/bin/bulletin

# ============================================================================
# Done!
# ============================================================================

if [[ -n "$DOMAIN" ]]; then
    BASE_URL="https://$DOMAIN"
else
    BASE_URL="http://$SERVER_IP"
fi

echo ""
echo "============================================="
echo -e "${GREEN}  Deployment Complete!${NC}"
echo "============================================="
echo ""
echo "  API URL:       $BASE_URL"
echo "  Swagger Docs:  $BASE_URL/docs"
echo "  ReDoc:         $BASE_URL/redoc"
echo "  API Base:      $BASE_URL/api/v1"
echo ""
echo "  Admin login:   admin / admin123"
echo "  Editor login:  editor / editor123"
echo "  Students:      see $APP_DIR/student_accounts.csv"
echo ""
echo "  Management commands:"
echo "    bulletin status        — check services"
echo "    bulletin logs          — follow API logs"
echo "    bulletin restart       — restart everything"
echo "    bulletin reset         — reset DB to seed data"
echo "    bulletin users         — list all accounts"
echo "    bulletin add-students 10 — create 10 more accounts"
echo ""
echo "  Share with students:"
echo "    1. $BASE_URL/docs  (interactive API explorer)"
echo "    2. Their login from student_accounts.csv"
echo "    3. The API_GUIDE.md tutorial"
echo ""
echo -e "${YELLOW}  IMPORTANT: Change the admin password after first login!${NC}"
echo ""

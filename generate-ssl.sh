#!/bin/bash
# =============================================================================
# SSL CERTIFICATE GENERATION SCRIPT FOR SYNTHIA STYLE
# =============================================================================
# Generates self-signed certificates for development and testing

set -e

SSL_DIR="/etc/nginx/ssl"
DOMAIN="synthia.style"
COUNTRY="PE"
STATE="Lima"
CITY="Lima"
ORGANIZATION="Synthia Style"
UNIT="Development"
EMAIL="dev@synthia.style"

echo "🔐 Generating SSL certificates for Synthia Style..."

# Create SSL directory if it doesn't exist
mkdir -p "$SSL_DIR"

# Generate Diffie-Hellman parameters
echo "📋 Generating Diffie-Hellman parameters..."
openssl dhparam -out "$SSL_DIR/dhparam.pem" 2048

# Generate private key
echo "🔑 Generating private key..."
openssl genrsa -out "$SSL_DIR/synthia.key" 4096

# Set proper permissions on private key
chmod 600 "$SSL_DIR/synthia.key"

# Generate certificate signing request
echo "📝 Generating certificate signing request..."
openssl req -new \
    -key "$SSL_DIR/synthia.key" \
    -out "$SSL_DIR/synthia.csr" \
    -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORGANIZATION/OU=$UNIT/CN=$DOMAIN/emailAddress=$EMAIL"

# Generate self-signed certificate
echo "📜 Generating self-signed certificate..."
openssl x509 -req \
    -in "$SSL_DIR/synthia.csr" \
    -signkey "$SSL_DIR/synthia.key" \
    -out "$SSL_DIR/synthia.crt" \
    -days 365 \
    -extensions v3_req \
    -extfile <(cat <<EOF
[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = www.$DOMAIN
DNS.3 = localhost
DNS.4 = *.synthia.style
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
)

# Set proper permissions
chmod 644 "$SSL_DIR/synthia.crt"
chmod 644 "$SSL_DIR/dhparam.pem"

# Clean up CSR file
rm -f "$SSL_DIR/synthia.csr"

echo "✅ SSL certificates generated successfully!"
echo "📂 Certificate location: $SSL_DIR/synthia.crt"
echo "🔑 Private key location: $SSL_DIR/synthia.key"
echo "🔐 DH parameters location: $SSL_DIR/dhparam.pem"
echo ""
echo "⚠️  Note: These are self-signed certificates for development only."
echo "   For production, use Let's Encrypt or purchase certificates from a CA."
echo ""
echo "🚀 You can now start the Nginx proxy with SSL support!"

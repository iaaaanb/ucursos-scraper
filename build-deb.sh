#!/bin/bash
set -e

# Build script for ucursito .deb package

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Building ucursito .deb package"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf debian/
rm -f ucursito_*.deb

# Create debian package structure
echo "📁 Creating debian package structure..."
mkdir -p debian/DEBIAN
mkdir -p debian/opt/ucursito
mkdir -p debian/usr/local/bin

# Copy DEBIAN control files
echo "📋 Copying DEBIAN control files..."
cp debian-template/DEBIAN/* debian/DEBIAN/
chmod +x debian/DEBIAN/postinst
chmod +x debian/DEBIAN/prerm

# Copy application files to /opt/ucursito/
echo "📦 Copying application files..."
cp -r src debian/opt/ucursito/
cp config.py requirements.txt .env.example README.md ucursito debian/opt/ucursito/

# Make sure ucursito wrapper is executable
chmod +x debian/opt/ucursito/ucursito

# Make sure main.py is executable
chmod +x debian/opt/ucursito/src/main.py

# Clean up Python cache files
echo "🧹 Cleaning up cache files..."
find debian/opt/ucursito -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find debian/opt/ucursito -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find debian/opt/ucursito -type f -name "*.pyc" -delete 2>/dev/null || true
find debian/opt/ucursito -type f -name "*.pyo" -delete 2>/dev/null || true

# Get package version from control file
VERSION=$(grep "^Version:" debian/DEBIAN/control | awk '{print $2}')

# Build the .deb package
echo "🔨 Building .deb package..."
dpkg-deb --build --root-owner-group debian ucursito_${VERSION}_all.deb

# Clean up build directory
echo "🧹 Cleaning up build directory..."
rm -rf debian/

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Package built successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 Package: ucursito_${VERSION}_all.deb"
echo "📊 Size: $(du -h ucursito_${VERSION}_all.deb | cut -f1)"
echo ""
echo "📥 To install:"
echo "   sudo dpkg -i ucursito_${VERSION}_all.deb"
echo ""
echo "🔍 To inspect:"
echo "   dpkg -c ucursito_${VERSION}_all.deb      # List contents"
echo "   dpkg -I ucursito_${VERSION}_all.deb      # Show package info"
echo ""
echo "🗑️  To remove:"
echo "   sudo dpkg -r ucursito                    # Remove package"
echo "   sudo dpkg --purge ucursito               # Remove package + config"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

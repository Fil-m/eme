#!/bin/bash
echo ">>> EME NODE INSTALLER <<<"
echo "Target: $1"

# 1. Update package manager
echo "Updating packages..."
pkg update -y && pkg upgrade -y

# 2. Install Python and Git
echo "Installing Python and Git..."
pkg install python git -y

# 3. Install system dependencies for Pillow (CRITICAL for Termux)
echo "Installing image processing libraries..."
pkg install libjpeg-turbo zlib libpng freetype clang make libwebp -y

# 4. Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip wheel

# 5. Setup directory
mkdir -p eme
cd eme

# 6. Download Bundle (Source + DB)
echo "Downloading EME Bundle..."
curl -o bundle.zip $1/bundle.zip

# 7. Unzip
echo "Unzipping..."
unzip -o bundle.zip
rm bundle.zip

# 8. Install Python dependencies with proper flags for Pillow
echo "Installing Python dependencies..."
LDFLAGS="-L$PREFIX/lib" CFLAGS="-I$PREFIX/include" pip install flask flask-sqlalchemy requests qrcode[pil] markdown || echo "Warning: Some packages may need internet connection"

# 9. Verify installation
echo "Verifying dependencies..."
python -c "from PIL import Image; import flask, qrcode, markdown; print('All dependencies OK!')" || {
    echo "ERROR: Dependencies missing. Please connect to internet and run:"
    echo '  LDFLAGS="-L$PREFIX/lib" CFLAGS="-I$PREFIX/include" pip install -r requirements.txt'
    exit 1
}

# 10. Start
echo ""
echo "Installation Complete!"
echo "Starting EME Node..."
python app.py

#!/bin/bash

# Define variables
APP_NAME="pardus-temizleyici"
VERSION="1.0.0"
BUILD_DIR="build_deb"
OPT_DIR="${BUILD_DIR}/opt/${APP_NAME}"
APP_DIR="${BUILD_DIR}/usr/share/applications"
PIX_DIR="${BUILD_DIR}/usr/share/pixmaps"
BIN_DIR="${BUILD_DIR}/usr/bin"
META_DIR="${BUILD_DIR}/usr/share/metainfo"
DOC_DIR="${BUILD_DIR}/usr/share/doc/${APP_NAME}"
echo "Cleaning previous build..."
rm -rf ${BUILD_DIR}/opt ${BUILD_DIR}/usr

echo "Creating directories..."
mkdir -p ${OPT_DIR}
mkdir -p ${APP_DIR}
mkdir -p ${PIX_DIR}
mkdir -p ${BIN_DIR}
mkdir -p ${META_DIR}
mkdir -p ${DOC_DIR}
mkdir -p ${BUILD_DIR}/DEBIAN

echo "Generating control file..."
cat <<EOF > ${BUILD_DIR}/DEBIAN/control
Package: pardus-temizleyici
Version: 1.0.0
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1
Maintainer: İnoTürk <inoturkteknolojitakimi@gmail.com>
Homepage: https://inoturk.netlify.app/
License: GPL-3.0-or-later
Description: Pardus Sistem Temizleyici
 Modern and safe system cleaning tool for Pardus Linux.
 Modern ve güvenli sistem temizleme aracı.
EOF
echo "Copying application files..."
cp -r core data locales utils views widgets application.py main.py window.py LICENSE README.md README_EN.md ${OPT_DIR}/

echo "Copying desktop file, icon, metadata and copyright..."
cp ${APP_NAME}.desktop ${APP_DIR}/
cp ${APP_NAME}.png ${PIX_DIR}/
cp com.pardus.temizleyici.metainfo.xml ${META_DIR}/
cp copyright ${DOC_DIR}/

echo "Creating launcher script..."
cat <<EOF > ${BIN_DIR}/${APP_NAME}
#!/bin/bash
python3 /opt/${APP_NAME}/main.py "\$@"
EOF
chmod 755 ${BIN_DIR}/${APP_NAME}

echo "Setting permissions..."
chmod 755 ${OPT_DIR}/main.py
chmod -R 755 ${OPT_DIR}

echo "Building Debian package..."
dpkg-deb --root-owner-group --build ${BUILD_DIR} ${APP_NAME}_${VERSION}_all.deb

echo "Build complete: ${APP_NAME}_${VERSION}_all.deb"

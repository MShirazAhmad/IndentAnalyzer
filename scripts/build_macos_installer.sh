#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
export COPYFILE_DISABLE=1

VERSION="${VERSION:-1.0.1}"
APP_NAME="IndentAnalyzer"
APP_BUNDLE="$PROJECT_ROOT/dist/$APP_NAME.app"
INSTALLER_ROOT="$PROJECT_ROOT/build/macos-installer"
SCRIPTS_ROOT="$INSTALLER_ROOT/scripts"
PACKAGE_ROOT="$INSTALLER_ROOT/packages"
RESOURCES_ROOT="$INSTALLER_ROOT/resources"
COMPONENT_PKG="$PACKAGE_ROOT/$APP_NAME-component.pkg"
DISTRIBUTION_XML="$INSTALLER_ROOT/Distribution.xml"
OUTPUT_PKG="$PROJECT_ROOT/dist/$APP_NAME-$VERSION-macOS.pkg"

if ! command -v pkgbuild >/dev/null 2>&1; then
  echo "pkgbuild is required and is included with Xcode Command Line Tools."
  echo "Install them with: xcode-select --install"
  exit 1
fi

if ! command -v productbuild >/dev/null 2>&1; then
  echo "productbuild is required and is included with Xcode Command Line Tools."
  echo "Install them with: xcode-select --install"
  exit 1
fi

"$PROJECT_ROOT/scripts/build_macos_app.sh"

if [ ! -d "$APP_BUNDLE" ]; then
  echo "Expected app bundle was not created: $APP_BUNDLE"
  exit 1
fi

find "$APP_BUNDLE" -name ".DS_Store" -delete
find "$APP_BUNDLE" -name "._*" -delete
xattr -cr "$APP_BUNDLE" 2>/dev/null || true

if command -v codesign >/dev/null 2>&1; then
  if [ -n "${CODESIGN_IDENTITY:-}" ]; then
    echo "Signing app with identity: $CODESIGN_IDENTITY"
    codesign --force --deep --options runtime --timestamp --sign "$CODESIGN_IDENTITY" "$APP_BUNDLE"
  elif [ "${ADHOC_SIGN:-1}" = "1" ]; then
    echo "Applying ad-hoc signature to local app build."
    codesign --force --deep --sign - "$APP_BUNDLE"
  fi
fi

rm -rf "$INSTALLER_ROOT"
mkdir -p "$SCRIPTS_ROOT" "$PACKAGE_ROOT" "$RESOURCES_ROOT"

install -m 0755 "$PROJECT_ROOT/installer/macos/scripts/postinstall" "$SCRIPTS_ROOT/postinstall"
cp "$PROJECT_ROOT/installer/macos/resources/Welcome.txt" "$RESOURCES_ROOT/Welcome.txt"
cp "$PROJECT_ROOT/installer/macos/resources/ReadMe.txt" "$RESOURCES_ROOT/ReadMe.txt"
cp "$PROJECT_ROOT/LICENSE" "$RESOURCES_ROOT/LICENSE.txt"
sed "s/@VERSION@/$VERSION/g" "$PROJECT_ROOT/installer/macos/Distribution.xml.in" > "$DISTRIBUTION_XML"

pkgbuild \
  --component "$APP_BUNDLE" \
  --identifier "com.indentanalyzer.app.pkg" \
  --version "$VERSION" \
  --install-location "/Applications" \
  --scripts "$SCRIPTS_ROOT" \
  --filter '(^|/)\._[^/]*$' \
  --filter '(^|/)\.DS_Store$' \
  "$COMPONENT_PKG"

PRODUCTBUILD_ARGS=(
  --distribution "$DISTRIBUTION_XML"
  --resources "$RESOURCES_ROOT"
  --package-path "$PACKAGE_ROOT"
)

if [ -n "${INSTALLER_SIGN_IDENTITY:-}" ]; then
  PRODUCTBUILD_ARGS+=(--sign "$INSTALLER_SIGN_IDENTITY")
fi

productbuild "${PRODUCTBUILD_ARGS[@]}" "$OUTPUT_PKG"

echo "Built installer: $OUTPUT_PKG"
echo
echo "To build a notarization-ready installer, set CODESIGN_IDENTITY and INSTALLER_SIGN_IDENTITY."

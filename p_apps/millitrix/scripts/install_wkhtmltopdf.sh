#!/usr/bin/env bash
# Install patched wkhtmltopdf for Frappe PDF print (required — without it PDFs fail).
#
# Usage (from ANY directory):
#   bash ~/mill_erp/erp_mill/frappe-bench/apps/millitrix/scripts/install_wkhtmltopdf.sh
#
# With sudo (system-wide):
#   bash install_wkhtmltopdf.sh --system
#
# Without sudo (user ~/.local/bin — add to PATH if needed):
#   bash install_wkhtmltopdf.sh --user
set -euo pipefail

MODE="${1:---user}"
INSTALL_DIR="${HOME}/.local/bin"

_is_valid() {
	command -v wkhtmltopdf >/dev/null 2>&1 && wkhtmltopdf --version 2>&1 | grep -qi qt
}

if _is_valid; then
	echo "wkhtmltopdf already installed (patched qt build)."
	wkhtmltopdf --version
	exit 0
fi

ARCH="$(uname -m)"
case "$ARCH" in
	x86_64) DEB_ARCH=amd64 ;;
	aarch64|arm64) DEB_ARCH=arm64 ;;
	*)
		echo "Unsupported arch: $ARCH"
		echo "Download manually: https://github.com/wkhtmltopdf/packaging/releases"
		exit 1
		;;
esac

URL="https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_${DEB_ARCH}.deb"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Downloading $URL"
if command -v curl >/dev/null 2>&1; then
	curl -fsSL "$URL" -o "$TMP/wkhtmltox.deb"
elif command -v wget >/dev/null 2>&1; then
	wget -q "$URL" -O "$TMP/wkhtmltox.deb"
else
	echo "Install curl or wget first: sudo apt-get install -y curl"
	exit 1
fi

dpkg-deb -x "$TMP/wkhtmltox.deb" "$TMP/extract"

if [[ "$MODE" == "--system" ]]; then
	echo "Installing system-wide (requires sudo)..."
	sudo dpkg -i "$TMP/wkhtmltox.deb" || sudo apt-get install -f -y
else
	echo "Installing to $INSTALL_DIR (no sudo)..."
	mkdir -p "$INSTALL_DIR"
	cp "$TMP/extract/usr/local/bin/wkhtmltopdf" "$INSTALL_DIR/wkhtmltopdf"
	chmod +x "$INSTALL_DIR/wkhtmltopdf"
	if ! echo ":$PATH:" | grep -q ":${INSTALL_DIR}:"; then
		echo ""
		echo "Add to PATH (once):"
		echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
		echo "  source ~/.bashrc"
		echo ""
	fi
	export PATH="${INSTALL_DIR}:$PATH"
fi

if _is_valid; then
	wkhtmltopdf --version
	echo ""
	echo "Done. Verify in bench:"
	echo "  cd ~/mill_erp/erp_mill/frappe-bench"
	echo "  bench --site local.millitrix execute millitrix.utils.pdf_setup.run"
else
	echo "Install finished but wkhtmltopdf not found in PATH."
	echo "Try: export PATH=\"\$HOME/.local/bin:\$PATH\""
	exit 1
fi

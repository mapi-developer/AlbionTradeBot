import os
import shutil
import PyInstaller.__main__

def clean_build():
    """Removes previous build artifacts."""
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')

def run_pyinstaller():
    """Runs the spec file."""
    print(">>> Running PyInstaller...")
    PyInstaller.__main__.run([
        'bot.spec',
        '--noconfirm',
        '--clean'
    ])

def copy_external_assets():
    """Copies config and other required files to the dist folder."""
    print(">>> Copying external assets...")
    
    source_dist = os.path.join('dist', 'MarketTrader')

    # 1. Copy Config Folder (This makes it editable)
    src_config = os.path.join('bot', 'config')
    
    dst_config = os.path.join(source_dist, 'config')
    
    # Ignore internal python cache files
    if os.path.exists(src_config):
        shutil.copytree(src_config, dst_config, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
        print(f"   [+] Copied config folder to {dst_config}")
    else:
        print(f"   [!] ERROR: Config source not found at {src_config}")

    # 2. Copy .env file (Critical for Database)
    if os.path.exists('.env'):
        shutil.copy('.env', os.path.join(source_dist, '.env'))
        print("   [+] Copied .env file")
    else:
        print("   [!] WARNING: .env file not found. User will need to create one.")

    # 3. Create a README instruction
    # with open(os.path.join(source_dist, 'README.txt'), 'w') as f:
    #     f.write("Albion Trade Bot\n")
    #     f.write("----------------\n")
    #     f.write("1. Edit settings in the 'config' folder.\n")
    #     f.write("2. Ensure 'Npcap' is installed on your machine (needed for sniffer).\n")
    #     f.write("3. Ensure 'Tesseract OCR' is installed or configured.\n")
    
    print(">>> Build Complete! Output is in 'dist/AlbionTradeBot'")

if __name__ == "__main__":
    clean_build()
    run_pyinstaller()
    copy_external_assets()
import os
import sys
from pathlib import Path
import sys
from pathlib import Path

# Tambahkan path utama ke sys PATH
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# ===============================================
# FIX 1: Tambahkan root project ke Python path
# ===============================================
root_dir = Path(__file__).parent.absolute()
sys.path.append(str(root_dir))

# ===============================================
# FIX 2: Import setelah set path
# ===============================================
from Bot-Store-Telegram.modules.payment_handler import payment_gateway
# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def main():
    # Inisialisasi payment handler
    payment = PaymentHandler(
        api_key=os.getenv("VIOLET_API_KEY"),
        secret_key=os.getenv("VIOLET_SECRET_KEY")
    )
    
    print("✅ Bot berhasil diinisialisasi!")
    # ... kode bot lainnya ...

if __name__ == "__main__":
    main()

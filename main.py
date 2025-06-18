import json
import os
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, CallbackQuery
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, CallbackContext
)
from datetime import datetime

OWNER_ID = 1160642744
produk_file = "produk.json"
saldo_file = "saldo.json"
deposit_file = "pending_deposit.json"
riwayat_file = "riwayat.json"
statistik_file = "statistik.json"

def load_json(file):
    if not os.path.exists(file):
        return {} if file.endswith(".json") else []
    with open(file, "r") as f:
        content = f.read().strip()
        if not content:
            return {} if file.endswith(".json") else []
        return json.loads(content)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

def update_statistik(uid, nominal):
    statistik = load_json(statistik_file)
    uid = str(uid)
    if uid not in statistik:
        statistik[uid] = {"jumlah": 0, "nominal": 0}
    statistik[uid]["jumlah"] += 1
    statistik[uid]["nominal"] += nominal
    save_json(statistik_file, statistik)

def add_riwayat(uid, tipe, keterangan, jumlah):
    riwayat = load_json(riwayat_file)
    if str(uid) not in riwayat:
        riwayat[str(uid)] = []
    riwayat[str(uid)].append({
        "tipe": tipe,
        "keterangan": keterangan,
        "jumlah": jumlah,
        "waktu": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    })
    save_json(riwayat_file, riwayat)
    if tipe == "BELI":
        update_statistik(uid, jumlah)

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    saldo = load_json(saldo_file)
    statistik = load_json(statistik_file)
    s = saldo.get(str(user.id), 0)
    jumlah = statistik.get(str(user.id), {}).get("jumlah", 0)
    total = statistik.get(str(user.id), {}).get("nominal", 0)

    text = (
        f"👋 Selamat datang di *Store Ekha*!\n\n"
        f"🧑 Nama: {user.full_name}\n"
        f"🆔 ID: {user.id}\n"
        f"💰 Total Saldo Kamu: Rp{s:,}\n"
        f"📦 Total Transaksi: {jumlah}\n"
        f"💸 Total Nominal Transaksi: Rp{total:,}"
    )

    keyboard = [
        [InlineKeyboardButton("📋 List Produk", callback_data="list_produk"),
         InlineKeyboardButton("🛒 Stock", callback_data="cek_stok")],
        [InlineKeyboardButton("💰 Deposit Saldo", callback_data="deposit")],
    ]
    if user.id == OWNER_ID:
        keyboard.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_panel")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = str(query.from_user.id)
    produk = load_json(produk_file)
    saldo = load_json(saldo_file)

    if data == "list_produk":
        msg = "*LIST PRODUK*\n"
        keyboard = []
        row = []

        for i, (pid, item) in enumerate(produk.items(), start=1):
            msg += f"{pid} {item['nama']} - Rp{item.get('harga', 0):,}\n"
            if item["stok"] > 0:
                row.append(KeyboardButton(pid))
            else:
                row.append(KeyboardButton(f"{pid} SOLDOUT ❌"))
            if len(row) == 3:
                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)

        keyboard.append([KeyboardButton("🔙 Kembali")])

        reply_keyboard = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

        await query.message.delete()
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=msg + "\nSilahkan pilih Nomor produk yang ingin dibeli.",
            reply_markup=reply_keyboard,
            parse_mode="Markdown"
        )

    elif data == "cek_stok":
        now = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
        msg = f"*Informasi Stok*\n- {now}\n\n"
        keyboard = []
        row = []

        for pid, item in produk.items():
            msg += f"{pid}. {item['nama']} ➔ {item['stok']}x\n"
            if item["stok"] > 0:
                row.append(KeyboardButton(pid))
            else:
                row.append(KeyboardButton(f"{pid} SOLDOUT ❌"))
            if len(row) == 3:
                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)

        keyboard.append([KeyboardButton("🔙 Kembali")])

        reply_keyboard = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

        await query.message.delete()
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=msg,
            reply_markup=reply_keyboard,
            parse_mode="Markdown"
        )


    elif data == "deposit":
        nominals = [10000, 15000, 20000, 25000]
        keyboard = [[InlineKeyboardButton(f"Rp{n:,}", callback_data=f"deposit_{n}") for n in nominals]]
        keyboard.append([InlineKeyboardButton("🔧 Custom Nominal", callback_data="deposit_custom")])
        await query.edit_message_text("💰 Pilih nominal deposit kamu:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("deposit_"):
        if data == "deposit_custom":
            context.user_data["awaiting_custom"] = True
            await query.edit_message_text("Ketik jumlah deposit yang kamu inginkan (angka saja):")
        else:
            nominal = int(data.split("_")[1])
            context.user_data["nominal_asli"] = nominal
            context.user_data["total_transfer"] = nominal + 23

            reply_keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton("❌ Batalkan Deposit")]],
                resize_keyboard=True, one_time_keyboard=True
            )
            await query.message.delete()
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text=f"💳 Transfer *Rp{nominal + 23:,}* ke:\n"
                     "`DANA 0812-XXXX-XXXX a.n. Store Ekha`\nSetelah transfer, kirim bukti ke bot ini.",
                parse_mode="Markdown",
                reply_markup=reply_keyboard
            )

    elif data == "admin_panel" and query.from_user.id == OWNER_ID:
        text = "*📊 Data User:*\n"
        for u, s in saldo.items():
            text += f"• ID {u}: Rp{s:,}\n"
        pending = load_json(deposit_file)
        text += "\n*⏳ Pending Deposit:*\n"
        if pending:
            for p in pending:
                text += f"- @{p['username']} ({p['user_id']}) Rp{p['nominal']:,}\n"
        else:
            text += "Tidak ada."
        await query.edit_message_text(text, parse_mode="Markdown")

    elif data.startswith("confirm:"):
        user_id = int(data.split(":")[1])
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ YA", callback_data=f"final:{user_id}")],
            [InlineKeyboardButton("🔙 Batal", callback_data="back")]
        ])
        await query.edit_message_caption("Konfirmasi saldo ke user ini?", reply_markup=keyboard)

    elif data.startswith("final:"):
        user_id = int(data.split(":")[1])
        pending = load_json(deposit_file)
        item = next((p for p in pending if p["user_id"] == user_id), None)
        if item:
            nominal = item["nominal"]
            saldo[str(user_id)] = saldo.get(str(user_id), 0) + nominal
            save_json(saldo_file, saldo)
            pending = [p for p in pending if p["user_id"] != user_id]
            save_json(deposit_file, pending)
            add_riwayat(user_id, "DEPOSIT", "Konfirmasi Admin", nominal)
            await query.edit_message_caption(f"✅ Saldo Rp{nominal:,} ditambahkan.")
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Saldo Rp{nominal:,} berhasil ditambahkan!",
                reply_markup=ReplyKeyboardRemove()
            )
            await start(update, context)
        else:
            await query.edit_message_caption("❌ Data deposit tidak ditemukan.")

    elif data.startswith("reject:"):
        user_id = int(data.split(":")[1])
        await query.edit_message_caption("❌ Deposit ditolak.")
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Deposit kamu ditolak oleh admin.",
            reply_markup=ReplyKeyboardRemove()
        )

    elif data == "back":
        await query.edit_message_caption("✅ Dibatalkan.")

    elif data in produk:
        # Saat user klik ID produk
        item = produk[data]
        if item["stok"] <= 0:
            await query.answer("Produk habis", show_alert=True)
            return

        harga = item["harga"]
        tipe = item["akun_list"][0]["tipe"] if item["akun_list"] else "-"
        stok = item["stok"]

        context.user_data["konfirmasi"] = {
            "produk_id": data,
            "jumlah": 1
        }

        text = (
            "KONFIRMASI PESANAN 🛒\n"
            "╭ - - - - - - - - - - - - - - - - - - - - - ╮\n"
            f"┊・Produk: {item['nama']}\n"
            f"┊・Variasi: {tipe}\n"
            f"┊・Harga satuan: Rp. {harga:,}\n"
            f"┊・Stok tersedia: {stok}\n"
            "┊ - - - - - - - - - - - - - - - - - - - - -\n"
            f"┊・Jumlah Pesanan: x1\n"
            f"┊・Total Pembayaran: Rp. {harga:,}\n"
            "╰ - - - - - - - - - - - - - - - - - - - - - ╯"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➖", callback_data="qty_minus"),
                InlineKeyboardButton("Jumlah: 1", callback_data="ignore"),
                InlineKeyboardButton("➕", callback_data="qty_plus")
            ],
            [InlineKeyboardButton("Konfirmasi Order ✅", callback_data="confirm_order")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_produk")]
        ])
        await query.message.delete()
        await context.bot.send_message(
            chat_id=uid,
            text=text,
            reply_markup=keyboard
        )

    elif data == "qty_plus" or data == "qty_minus":
        info = context.user_data.get("konfirmasi")
        if not info:
            await query.answer("Data tidak tersedia")
            return

        produk_id = info["produk_id"]
        item = produk.get(produk_id)
        if not item:
            await query.answer("Produk tidak ditemukan")
            return

        jumlah = info["jumlah"]
        if data == "qty_plus" and jumlah < item["stok"]:
            jumlah += 1
        elif data == "qty_minus" and jumlah > 1:
            jumlah -= 1

        context.user_data["konfirmasi"]["jumlah"] = jumlah
        total = jumlah * item["harga"]
        tipe = item["akun_list"][0]["tipe"] if item["akun_list"] else "-"

        text = (
            "KONFIRMASI PESANAN 🛒\n"
            "╭ - - - - - - - - - - - - - - - - - - - - - ╮\n"
            f"┊・Produk: {item['nama']}\n"
            f"┊・Variasi: {tipe}\n"
            f"┊・Harga satuan: Rp. {item['harga']:,}\n"
            f"┊・Stok tersedia: {item['stok']}\n"
            "┊ - - - - - - - - - - - - - - - - - - - - -\n"
            f"┊・Jumlah Pesanan: x{jumlah}\n"
            f"┊・Total Pembayaran: Rp. {total:,}\n"
            "╰ - - - - - - - - - - - - - - - - - - - - - ╯"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➖", callback_data="qty_minus"),
                InlineKeyboardButton(f"Jumlah: {jumlah}", callback_data="ignore"),
                InlineKeyboardButton("➕", callback_data="qty_plus")
            ],
            [InlineKeyboardButton("Konfirmasi Order ✅", callback_data="confirm_order")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_produk")]
        ])
        await query.edit_message_text(text, reply_markup=keyboard)

    elif data == "back_to_produk":
        await start(update, context)

    elif data == "confirm_order":
        info = context.user_data.get("konfirmasi")
        if not info:
            await query.answer("❌ Data pesanan tidak ditemukan", show_alert=True)
            return

        produk_id = info["produk_id"]
        jumlah = info["jumlah"]
        uid = str(query.from_user.id)

        produk = load_json(produk_file)
        saldo = load_json(saldo_file)

        item = produk.get(produk_id)
        if not item:
            await query.edit_message_text("❌ Produk tidak ditemukan.")
            return

        total = jumlah * item["harga"]

        if saldo.get(uid, 0) < total:
            await query.edit_message_text("❌ Saldo kamu tidak cukup untuk menyelesaikan pesanan.")
            await start(update, context)
            return

        if item["stok"] < jumlah or len(item["akun_list"]) < jumlah:
            await query.edit_message_text("❌ Stok atau akun tidak mencukupi.")
            return

        # Proses pemesanan
        saldo[uid] -= total
        produk[produk_id]["stok"] -= jumlah
        akun_terpakai = [item["akun_list"].pop(0) for _ in range(jumlah)]

        save_json(saldo_file, saldo)
        save_json(produk_file, produk)
        add_riwayat(uid, "BELI", f"{item['nama']} x{jumlah}", total)

        # Buat file txt
        os.makedirs("akun_dikirim", exist_ok=True)
        file_path = f"akun_dikirim/{uid}_{produk_id}_x{jumlah}.txt"
        with open(file_path, "w") as f:
            for i, akun in enumerate(akun_terpakai, start=1):
                f.write(
                    f"Akun #{i}\n"
                    f"Username: {akun['username']}\n"
                    f"Password: {akun['password']}\n"
                    f"Tipe: {akun['tipe']}\n"
                    "---------------------------\n"
                )

        with open(file_path, "rb") as f:
            await context.bot.send_document(
                chat_id=query.from_user.id,
                document=InputFile(f, filename=os.path.basename(file_path)),
                caption=f"📦 Pembelian *{item['nama']}* x{jumlah} berhasil!\nSisa saldo: Rp{saldo[uid]:,}",
                parse_mode="Markdown"
            )

        context.user_data.pop("konfirmasi", None)
        await start(update, context)

    elif data == "ignore":
        await query.answer()


async def handle_text(update: Update, context: CallbackContext):
    text = update.message.text.strip()

    # Normalisasi input jika tombol mengandung "SOLDOUT"
    if "SOLDOUT" in text:
        text = text.split()[0]

    uid = str(update.effective_user.id)

    # Batalkan deposit
    if text == "❌ Batalkan Deposit":
        pending = load_json(deposit_file)
        pending = [p for p in pending if str(p["user_id"]) != uid]
        save_json(deposit_file, pending)
        await update.message.reply_text("✅ Deposit kamu telah dibatalkan.", reply_markup=ReplyKeyboardRemove())
        await start(update, context)
        return

    # Mode custom deposit
    if context.user_data.get("awaiting_custom"):
        try:
            nominal = int(text)
            context.user_data["awaiting_custom"] = False
            context.user_data["nominal_asli"] = nominal
            context.user_data["total_transfer"] = nominal + 23
            reply_keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton("❌ Batalkan Deposit")]],
                resize_keyboard=True, one_time_keyboard=True
            )
            await update.message.reply_text(
                f"💳 Transfer *Rp{nominal + 23:,}* ke:\n"
                "`DANA 0812-XXXX-XXXX a.n. Store Ekha`\nSetelah transfer, kirim bukti ke bot ini.",
                parse_mode="Markdown",
                reply_markup=reply_keyboard
            )
        except:
            await update.message.reply_text("❌ Format salah.")
        return

    # Tangani angka produk → Arahkan manual ke fungsi konfirmasi
    produk = load_json(produk_file)
    if text in produk:
        item = produk[text]
        if item["stok"] <= 0:
            await update.message.reply_text("❌ Produk ini tidak bisa dibeli karena stok habis.")
            await start(update, context)
            return

        harga = item["harga"]
        tipe = item["akun_list"][0]["tipe"] if item["akun_list"] else "-"
        stok = item["stok"]

        context.user_data["konfirmasi"] = {
            "produk_id": text,
            "jumlah": 1
        }

        konfirmasi_text = (
            "KONFIRMASI PESANAN 🛒\n"
            "╭ - - - - - - - - - - - - - - - - - - - - - ╮\n"
            f"┊・Produk: {item['nama']}\n"
            f"┊・Variasi: {tipe}\n"
            f"┊・Harga satuan: Rp. {harga:,}\n"
            f"┊・Stok tersedia: {stok}\n"
            "┊ - - - - - - - - - - - - - - - - - - - - -\n"
            f"┊・Jumlah Pesanan: x1\n"
            f"┊・Total Pembayaran: Rp. {harga:,}\n"
            "╰ - - - - - - - - - - - - - - - - - - - - - ╯"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➖", callback_data="qty_minus"),
                InlineKeyboardButton("Jumlah: 1", callback_data="ignore"),
                InlineKeyboardButton("➕", callback_data="qty_plus")
            ],
            [InlineKeyboardButton("Konfirmasi Order ✅", callback_data="confirm_order")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_produk")]
        ])
        await update.message.reply_text(konfirmasi_text, reply_markup=keyboard)
        return

    # Tombol kembali
    if text == "🔙 Kembali":
        await start(update, context)
        return

    # Fallback ke menu utama
    await start(update, context)

async def handle_photo(update: Update, context: CallbackContext):
    user = update.effective_user
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    os.makedirs("bukti", exist_ok=True)
    path = f"bukti/{user.id}.jpg"
    await file.download_to_drive(path)

    nominal = context.user_data.get("nominal_asli", 0)
    total = context.user_data.get("total_transfer", nominal)

    pending = load_json(deposit_file)
    pending.append({
        "user_id": user.id,
        "username": user.username,
        "bukti_path": path,
        "nominal": nominal,
        "total_transfer": total
    })
    save_json(deposit_file, pending)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Konfirmasi", callback_data=f"confirm:{user.id}")],
        [InlineKeyboardButton("❌ Tolak", callback_data=f"reject:{user.id}")]
    ])
    with open(path, "rb") as f:
        await context.bot.send_photo(
            chat_id=OWNER_ID,
            photo=InputFile(f),
            caption=f"📥 Deposit dari @{user.username or user.id}\n"
                    f"Transfer: Rp{total:,}\nMasuk: Rp{nominal:,}",
            reply_markup=keyboard
        )
    await update.message.reply_text("✅ Bukti dikirim! Tunggu konfirmasi admin.")

def main():
    app = Application.builder().token("CHANGE_TO_YOUR_BOT_TOKEN").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()

"""Generate a real PromptPay EMV QR code (phone or bank account)."""
import qrcode, io

def _emv(id, value):
    return id + str(len(value)).zfill(2) + value

def promptpay_payload(target, amount=None):
    # target = phone "0941939686" or bank "0078468262" (KBank)
    t = "".join(c for c in str(target) if c.isdigit())
    if len(t) == 10 and t.startswith("0"):
        t = "66" + t[1:]  # 66941939686
    mcc = "0000001677000113" + str(len(t)).zfill(2) + t
    parts = [_emv("00", "01"), _emv("01", "12" if amount else "11"),
             _emv("29", _emv("00", "A000000677010111") + _emv("01", mcc[16:])),
             _emv("53", "764"), _emv("58", "TH")]
    if amount:
        parts.append(_emv("54", ("%.2f" % float(amount))))
    body = "".join(parts) + "6304"
    crc = 0xFFFF
    for ch in body.encode():
        crc ^= ch << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return body + ("%04X" % crc)

def make_png(target, amount=None, path=None):
    qr = qrcode.QRCode(box_size=10, border=3)
    qr.add_data(promptpay_payload(target, amount))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    if path:
        img.save(path)
        return path
    buf = io.BytesIO(); img.save(buf); return buf.getvalue()

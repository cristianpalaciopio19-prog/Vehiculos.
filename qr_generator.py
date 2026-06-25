"""Generador de códigos QR usando el encoder de ReportLab (ya incluido como dependencia)."""
from reportlab.graphics.barcode.qrencoder import QRCode, QRErrorCorrectLevel
from PIL import Image
import io


def generar_qr_imagen(data: str, scale: int = 10, border: int = 4) -> Image.Image:
    """Genera una imagen PIL de un código QR para el texto/URL dado."""
    qr = QRCode(None, QRErrorCorrectLevel.L)
    qr.addData(data)
    qr.make()
    size = qr.getModuleCount()
    total = (size + 2 * border) * scale
    img = Image.new('RGB', (total, total), (255, 255, 255))
    px = img.load()
    for r in range(size):
        for c in range(size):
            if qr.isDark(r, c):
                for dr in range(scale):
                    for dc in range(scale):
                        px[(c + border) * scale + dc, (r + border) * scale + dr] = (0, 0, 0)
    return img


def generar_qr_bytes(data: str, scale: int = 10, border: int = 4) -> bytes:
    img = generar_qr_imagen(data, scale, border)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

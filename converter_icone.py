"""
Converte a logo para formato .ico (ícone do Windows)
"""
from PIL import Image

# Abrir imagem
img = Image.open("logo.jpg")

# Redimensionar para tamanho de ícone (256x256 é ideal)
img = img.resize((256, 256), Image.Resampling.LANCZOS)

# Salvar como .ico
img.save("icon.ico", format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])

print("✅ Ícone criado: icon.ico")

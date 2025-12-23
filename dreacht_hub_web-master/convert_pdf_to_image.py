from PIL import Image
import os

# Convertir PDF a imagen
pdf_path = 'media/requiscion_template.pdf'
img_path = 'static/img/requisicion_template.png'

# Crear directorio si no existe
os.makedirs('static/img', exist_ok=True)

try:
    # Abrir PDF y convertir primera página a imagen
    with Image.open(pdf_path) as img:
        # Convertir a RGB si es necesario
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Guardar como PNG con alta calidad
        img.save(img_path, 'PNG', quality=95)
        print(f'PDF convertido a imagen: {img_path}')
        print(f'Dimensiones: {img.size}')
        
except Exception as e:
    print(f'Error convirtiendo PDF: {e}')
    print('Creando imagen en blanco como fallback...')
    
    # Crear imagen en blanco como fallback
    img = Image.new('RGB', (612, 792), 'white')
    img.save(img_path, 'PNG')
    print(f'Imagen en blanco creada: {img_path}')

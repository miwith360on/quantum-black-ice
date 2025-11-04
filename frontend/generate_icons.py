"""
Generate PWA Icons for Black Ice Alert Mobile App
Creates all required icon sizes for iOS and Android
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """Create a single icon with the specified size"""
    # Create image with dark background
    img = Image.new('RGB', (size, size), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    # Draw gradient circle background
    for i in range(size // 2):
        alpha = int(255 * (1 - i / (size / 2)))
        color = f'#{hex(26 + i // 4)[2:].zfill(2)}{hex(26 + i // 3)[2:].zfill(2)}{hex(46 + i // 2)[2:].zfill(2)}'
        draw.ellipse([i, i, size - i, size - i], fill=color)
    
    # Draw snowflake icon (simplified)
    center_x, center_y = size // 2, size // 2
    icon_size = size // 2
    
    # Draw snowflake lines
    line_width = max(size // 30, 2)
    line_color = '#FFFFFF'
    
    # Vertical line
    draw.line([(center_x, center_y - icon_size), (center_x, center_y + icon_size)], 
              fill=line_color, width=line_width)
    # Horizontal line
    draw.line([(center_x - icon_size, center_y), (center_x + icon_size, center_y)], 
              fill=line_color, width=line_width)
    # Diagonal lines
    offset = int(icon_size * 0.707)
    draw.line([(center_x - offset, center_y - offset), (center_x + offset, center_y + offset)], 
              fill=line_color, width=line_width)
    draw.line([(center_x - offset, center_y + offset), (center_x + offset, center_y - offset)], 
              fill=line_color, width=line_width)
    
    # Draw accent circle in center
    accent_radius = size // 8
    draw.ellipse([center_x - accent_radius, center_y - accent_radius, 
                  center_x + accent_radius, center_y + accent_radius],
                 fill='#007AFF')
    
    # Save the icon
    img.save(output_path, 'PNG')
    print(f"✅ Created {size}x{size} icon: {output_path}")

def create_all_icons():
    """Create all required icon sizes"""
    # Create icons directory
    icons_dir = 'icons'
    os.makedirs(icons_dir, exist_ok=True)
    
    # Icon sizes for iOS and Android
    sizes = [72, 96, 120, 128, 144, 152, 167, 180, 192, 512]
    
    print("🎨 Generating PWA icons...")
    print("=" * 50)
    
    for size in sizes:
        output_path = os.path.join(icons_dir, f'icon-{size}.png')
        create_icon(size, output_path)
    
    print("=" * 50)
    print("✅ All icons generated successfully!")
    print(f"📁 Icons saved to: {os.path.abspath(icons_dir)}")
    print("\n📱 iOS Installation Instructions:")
    print("1. Open mobile.html in Safari on your iPhone")
    print("2. Tap the Share button (square with arrow)")
    print("3. Scroll down and tap 'Add to Home Screen'")
    print("4. Tap 'Add' to install the app")
    print("\n✨ The app will appear on your home screen like a native app!")

def create_splash_screen():
    """Create splash screen for iOS"""
    splash_dir = 'splash'
    os.makedirs(splash_dir, exist_ok=True)
    
    # iPhone splash screen size (common size)
    width, height = 1170, 2532
    
    img = Image.new('RGB', (width, height), color='#000000')
    draw = ImageDraw.Draw(img)
    
    # Draw centered icon
    icon_size = 300
    icon_x = (width - icon_size) // 2
    icon_y = (height - icon_size) // 2 - 200
    
    # Create large snowflake
    center_x, center_y = icon_x + icon_size // 2, icon_y + icon_size // 2
    flake_size = icon_size // 2
    
    # Draw snowflake
    line_width = 8
    line_color = '#FFFFFF'
    
    draw.line([(center_x, center_y - flake_size), (center_x, center_y + flake_size)], 
              fill=line_color, width=line_width)
    draw.line([(center_x - flake_size, center_y), (center_x + flake_size, center_y)], 
              fill=line_color, width=line_width)
    offset = int(flake_size * 0.707)
    draw.line([(center_x - offset, center_y - offset), (center_x + offset, center_y + offset)], 
              fill=line_color, width=line_width)
    draw.line([(center_x - offset, center_y + offset), (center_x + offset, center_y - offset)], 
              fill=line_color, width=line_width)
    
    # Draw accent circle
    accent_radius = 40
    draw.ellipse([center_x - accent_radius, center_y - accent_radius, 
                  center_x + accent_radius, center_y + accent_radius],
                 fill='#007AFF')
    
    # Add app name
    try:
        # Try to use a nice font
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = ImageFont.load_default()
    
    text = "Black Ice Alert"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (width - text_width) // 2
    text_y = center_y + flake_size + 100
    
    draw.text((text_x, text_y), text, fill='#FFFFFF', font=font)
    
    # Save splash screen
    splash_path = os.path.join(splash_dir, 'iphone-splash.png')
    img.save(splash_path, 'PNG')
    print(f"✅ Created splash screen: {splash_path}")

if __name__ == '__main__':
    try:
        create_all_icons()
        create_splash_screen()
        
        print("\n" + "=" * 50)
        print("🎉 PWA assets generated successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error generating icons: {e}")
        print("\nPlease install Pillow if not already installed:")
        print("pip install Pillow")

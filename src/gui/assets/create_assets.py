from PIL import Image, ImageDraw, ImageFont
import os


def create_logo():
    """Create application logo"""
    # Create a 200x200 image with a white background
    img = Image.new("RGBA", (200, 200), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw a blue circle
    draw.ellipse((10, 10, 190, 190), fill=(33, 150, 243, 255))

    # Draw text
    try:
        font = ImageFont.truetype("Arial", 80)
    except:
        font = ImageFont.load_default()

    draw.text((50, 60), "TG", fill=(255, 255, 255, 255), font=font)

    # Save the logo
    img.save("logo.png")


def create_splash():
    """Create splash screen"""
    # Create a 600x400 image with a gradient background
    img = Image.new("RGBA", (600, 400), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw gradient background
    for y in range(400):
        r = int(33 + (y / 400) * 20)
        g = int(150 + (y / 400) * 20)
        b = int(243 + (y / 400) * 20)
        draw.line([(0, y), (600, y)], fill=(r, g, b, 255))

    # Draw logo
    try:
        logo = Image.open("logo.png")
        logo = logo.resize((100, 100), Image.Resampling.LANCZOS)
        img.paste(logo, (250, 50), logo)
    except:
        pass

    # Draw text
    try:
        title_font = ImageFont.truetype("Arial", 48)
        text_font = ImageFont.truetype("Arial", 24)
    except:
        title_font = text_font = ImageFont.load_default()

    draw.text((200, 180), "TikGen", fill=(255, 255, 255, 255), font=title_font)
    draw.text(
        (180, 250), "Content Automation", fill=(255, 255, 255, 255), font=text_font
    )
    draw.text((250, 350), "Loading...", fill=(255, 255, 255, 255), font=text_font)

    # Save the splash screen
    img.save("splash.png")


def create_app_icon():
    """Create application icon"""
    # Create a 256x256 image with a transparent background
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a blue circle
    draw.ellipse((10, 10, 246, 246), fill=(33, 150, 243, 255))

    # Draw text
    try:
        font = ImageFont.truetype("Arial", 120)
    except:
        font = ImageFont.load_default()

    draw.text((60, 60), "TG", fill=(255, 255, 255, 255), font=font)

    # Save the icon
    img.save("app_icon.png")


if __name__ == "__main__":
    # Change to the assets directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Create all assets
    create_logo()
    create_splash()
    create_app_icon()

    print("Asset files created successfully.")

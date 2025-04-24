from PIL import Image, ImageDraw, ImageFont
import os


def create_icon():
    """Create application icon"""
    # Create a 256x256 image with a blue background
    img = Image.new("RGBA", (256, 256), (52, 152, 219, 255))
    draw = ImageDraw.Draw(img)

    # Draw a white circle
    draw.ellipse((28, 28, 228, 228), fill=(255, 255, 255, 255))

    # Draw "AP" text
    try:
        font = ImageFont.truetype("Arial", 120)
    except:
        font = ImageFont.load_default()

    draw.text((80, 60), "AP", fill=(52, 152, 219, 255), font=font)

    # Save the icon
    img.save("assets/icon.png")


def create_logo():
    """Create application logo"""
    # Create a 400x400 image with a white background
    img = Image.new("RGBA", (400, 400), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw a blue circle
    draw.ellipse((50, 50, 350, 350), fill=(52, 152, 219, 255))

    # Draw "AutoPinner" text
    try:
        font = ImageFont.truetype("Arial", 60)
    except:
        font = ImageFont.load_default()

    draw.text((100, 170), "AutoPinner", fill=(255, 255, 255, 255), font=font)

    # Save the logo
    img.save("assets/logo.png")


def create_splash():
    """Create splash screen"""
    # Create a 600x400 image with a white background
    img = Image.new("RGBA", (600, 400), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw a blue rectangle at the top
    draw.rectangle((0, 0, 600, 100), fill=(52, 152, 219, 255))

    # Draw "AutoPinner" text
    try:
        font = ImageFont.truetype("Arial", 48)
    except:
        font = ImageFont.load_default()

    draw.text((200, 20), "AutoPinner", fill=(255, 255, 255, 255), font=font)

    # Draw "Loading..." text
    try:
        font = ImageFont.truetype("Arial", 24)
    except:
        font = ImageFont.load_default()

    draw.text((250, 200), "Loading...", fill=(52, 152, 219, 255), font=font)

    # Draw version and credits
    draw.text((200, 300), "Version 1.0.0", fill=(149, 165, 166, 255), font=font)
    draw.text(
        (150, 350), "Created by Semih Bugra Sezer", fill=(149, 165, 166, 255), font=font
    )

    # Save the splash screen
    img.save("assets/splash.png")


def main():
    """Create all asset files"""
    # Create assets directory if it doesn't exist
    os.makedirs("assets", exist_ok=True)

    # Create assets
    create_icon()
    create_logo()
    create_splash()

    print("Asset files created successfully!")


if __name__ == "__main__":
    main()

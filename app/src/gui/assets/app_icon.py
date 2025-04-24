from PIL import Image, ImageDraw, ImageFont
import os


def create_app_icon():
    """Create a custom application icon"""
    # Create a new image with a transparent background
    size = (512, 512)
    image = Image.new("RGBA", size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)

    # Draw a gradient background
    for y in range(size[1]):
        # Calculate gradient color
        r = int(33 + (y / size[1]) * 20)  # Start with Material Blue
        g = int(150 + (y / size[1]) * 20)
        b = int(243 + (y / size[1]) * 20)
        color = (r, g, b, 255)

        # Draw horizontal line
        draw.line([(0, y), (size[0], y)], fill=color)

    # Draw a circular mask
    mask = Image.new("RGBA", size, (0, 0, 0, 0))
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([(0, 0), size], fill=(255, 255, 255, 255))

    # Apply mask to create circular icon
    image = Image.alpha_composite(image, mask)

    # Draw the text "TG" in white
    text_color = (255, 255, 255, 255)
    try:
        font = ImageFont.truetype("Arial", 200)
    except:
        font = ImageFont.load_default()

    text = "TG"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)

    # Draw text with shadow
    shadow_offset = 5
    draw.text(
        (position[0] + shadow_offset, position[1] + shadow_offset),
        text,
        font=font,
        fill=(0, 0, 0, 128),
    )
    draw.text(position, text, font=font, fill=text_color)

    # Save the icon
    icon_path = os.path.join(os.path.dirname(__file__), "app_icon.png")
    image.save(icon_path, "PNG")
    return icon_path


if __name__ == "__main__":
    create_app_icon()

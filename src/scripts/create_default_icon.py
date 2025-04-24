from PIL import Image, ImageDraw

size = 1024
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw a simple icon - purple circle
circle_color = (142, 45, 197)  # Match the highlight color from the app
draw.ellipse([size // 4, size // 4, 3 * size // 4, 3 * size // 4], fill=circle_color)

img.save("icon.png")

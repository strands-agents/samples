"""
Image utilities for the LlamaCpp demo notebook.

This module contains functions for creating test images, converting images
to various formats, and analyzing images with the LlamaCpp model.
"""

import base64
import io
from typing import Tuple, Union

from PIL import Image, ImageDraw, ImageFont
from IPython.display import display

from strands import Agent  
from strands.models.llamacpp import LlamaCppModel


def create_test_image(size: Tuple[int, int] = (400, 300), 
                     background_color: str = 'lightblue') -> Image.Image:
    """
    Create a simple test image for demonstration purposes.
    
    This function creates an image with basic geometric shapes (rectangle,
    circle, triangle) and text for testing multimodal capabilities.
    
    Args:
        size: Tuple of (width, height) for the image
        background_color: Background color for the image
        
    Returns:
        PIL Image object with test shapes and text
    """
    width, height = size
    img = Image.new('RGB', size, color=background_color)
    draw = ImageDraw.Draw(img)
    
    # Calculate positions based on image size
    rect_size = min(width, height) // 4
    circle_size = rect_size
    
    # Draw rectangle (red)
    rect_x = width // 8
    rect_y = height // 6
    draw.rectangle([
        rect_x, rect_y, 
        rect_x + rect_size, rect_y + rect_size
    ], fill='red', outline='black', width=3)
    
    # Draw ellipse/circle (yellow)
    circle_x = width // 2
    circle_y = rect_y
    draw.ellipse([
        circle_x, circle_y,
        circle_x + circle_size * 1.5, circle_y + circle_size * 1.5
    ], fill='yellow', outline='black', width=3)
    
    # Draw triangle (green)
    triangle_base = width // 4
    triangle_height = height // 4
    triangle_x = rect_x + rect_size // 2
    triangle_y = height * 2 // 3
    
    draw.polygon([
        (triangle_x, triangle_y),
        (triangle_x + triangle_base // 2, triangle_y + triangle_height),
        (triangle_x - triangle_base // 2, triangle_y + triangle_height)
    ], fill='green', outline='black', width=3)
    
    # Add text
    try:
        # Try to use a default font
        font = ImageFont.load_default()
    except:
        font = None
    
    text_x = width // 2 - 40
    text_y = height - 40
    draw.text((text_x, text_y), "Test Image", fill='black', font=font)
    
    return img


def create_complex_test_image(size: Tuple[int, int] = (600, 400)) -> Image.Image:
    """
    Create a more complex test image with various elements.
    
    Args:
        size: Tuple of (width, height) for the image
        
    Returns:
        PIL Image with complex scene for advanced testing
    """
    width, height = size
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw gradient background
    for y in range(height):
        color_value = int(255 * (1 - y / height * 0.3))
        draw.line([(0, y), (width, y)], fill=(color_value, color_value + 20, 255))
    
    # Draw house
    house_width = width // 3
    house_height = height // 2
    house_x = width // 6
    house_y = height // 2
    
    # House base
    draw.rectangle([
        house_x, house_y,
        house_x + house_width, house_y + house_height
    ], fill='brown', outline='black', width=2)
    
    # Roof
    roof_points = [
        (house_x, house_y),
        (house_x + house_width // 2, house_y - house_height // 3),
        (house_x + house_width, house_y)
    ]
    draw.polygon(roof_points, fill='red', outline='black', width=2)
    
    # Door
    door_width = house_width // 4
    door_height = house_height // 2
    door_x = house_x + house_width // 2 - door_width // 2
    door_y = house_y + house_height - door_height
    draw.rectangle([
        door_x, door_y,
        door_x + door_width, door_y + door_height
    ], fill='darkred', outline='black', width=2)
    
    # Windows
    window_size = house_width // 6
    window_y = house_y + house_height // 4
    
    # Left window
    draw.rectangle([
        house_x + house_width // 6, window_y,
        house_x + house_width // 6 + window_size, window_y + window_size
    ], fill='lightblue', outline='black', width=2)
    
    # Right window
    draw.rectangle([
        house_x + house_width * 5 // 6 - window_size, window_y,
        house_x + house_width * 5 // 6, window_y + window_size
    ], fill='lightblue', outline='black', width=2)
    
    # Sun
    sun_x = width * 3 // 4
    sun_y = height // 4
    sun_radius = width // 12
    draw.ellipse([
        sun_x - sun_radius, sun_y - sun_radius,
        sun_x + sun_radius, sun_y + sun_radius
    ], fill='yellow', outline='orange', width=3)
    
    # Sun rays
    for angle in range(0, 360, 45):
        import math
        rad = math.radians(angle)
        start_x = sun_x + int(sun_radius * 1.2 * math.cos(rad))
        start_y = sun_y + int(sun_radius * 1.2 * math.sin(rad))
        end_x = sun_x + int(sun_radius * 1.6 * math.cos(rad))
        end_y = sun_y + int(sun_radius * 1.6 * math.sin(rad))
        draw.line([(start_x, start_y), (end_x, end_y)], fill='orange', width=3)
    
    # Clouds
    cloud_centers = [(width // 8, height // 8), (width * 7 // 8, height // 6)]
    for cx, cy in cloud_centers:
        for dx, dy, size in [(-20, 0, 15), (0, -5, 18), (20, 0, 15), (10, 5, 12)]:
            draw.ellipse([
                cx + dx - size, cy + dy - size,
                cx + dx + size, cy + dy + size
            ], fill='white', outline='lightgray')
    
    # Add title
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    draw.text((width // 2 - 60, height - 30), "Complex Scene", 
              fill='black', font=font)
    
    return img


def image_to_base64(img: Image.Image, format: str = 'PNG') -> str:
    """
    Convert PIL image to base64 string.
    
    Args:
        img: PIL Image object
        format: Image format for encoding ('PNG', 'JPEG', etc.)
        
    Returns:
        Base64 encoded image string
    """
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return img_base64


def image_to_bytes(img: Image.Image, format: str = 'PNG') -> bytes:
    """
    Convert PIL image to bytes for direct use with Strands SDK.
    
    Args:
        img: PIL Image object
        format: Image format for encoding ('PNG', 'JPEG', etc.')
        
    Returns:
        Image data as bytes
    """
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    return buffer.getvalue()


def analyze_image_with_llamacpp(image: Union[Image.Image, bytes], 
                               prompt: str = "Describe this image in detail.",
                               base_url: str = "http://localhost:8080",
                               temperature: float = 0.7,
                               max_tokens: int = 200) -> str:
    """
    Analyze an image using the LlamaCpp model with multimodal capabilities.
    
    Args:
        image: PIL Image object or image bytes
        prompt: Text prompt for the analysis
        base_url: Base URL for the LlamaCpp server
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        
    Returns:
        Analysis text from the model
        
    Raises:
        Exception: If analysis fails
    """
    # Convert image to bytes if needed
    if isinstance(image, Image.Image):
        img_bytes = image_to_bytes(image, 'PNG')
        img_format = 'png'
    else:
        img_bytes = image
        img_format = 'png'  # Assume PNG if bytes provided
    
    # Create LlamaCpp model
    # Ensure base_url doesn't have /v1 suffix to avoid double /v1 in URL
    clean_base_url = base_url.rstrip('/').replace('/v1', '')
    model = LlamaCppModel(
        base_url=clean_base_url,
        params={"temperature": temperature, "max_tokens": max_tokens}
    )
    agent = Agent(model=model)
    
    # Create message with mixed content (text + image)
    message_content = [
        {"text": prompt},
        {
            "image": {
                "source": {"bytes": img_bytes},
                "format": img_format
            }
        }
    ]
    
    # Get response
    response = agent(message_content)
    
    # Extract text content from AgentResult
    if hasattr(response, 'message') and 'content' in response.message:
        text_content = ""
        for content_block in response.message['content']:
            if 'text' in content_block:
                text_content += content_block['text']
        return text_content.strip()
    else:
        return str(response)


def create_image_analysis_demo(base_url: str = "http://localhost:8080") -> None:
    """
    Create and run a complete image analysis demonstration.
    
    Args:
        base_url: Base URL for the LlamaCpp server
    """
    print("🖼️ Image Analysis Demo")
    print("=" * 60)
    
    # Create and display test image
    test_image = create_test_image()
    print("Created simple test image:")
    display(test_image)
    
    # Analyze simple image
    print("-" * 40)
    try:
        analysis = analyze_image_with_llamacpp(
            test_image, 
            "Describe this image in detail. What shapes and colors do you see?",
            base_url=base_url
        )
        print(f"Analysis: {analysis}")
    except Exception as e:
        print(f"Error analyzing simple image: {e}")
    
    print("\n" + "=" * 60)
    
    # Create and display complex image
    complex_image = create_complex_test_image()
    print("Created complex test image:")
    display(complex_image)
    
    # Analyze complex image
    print("-" * 40)
    try:
        complex_analysis = analyze_image_with_llamacpp(
            complex_image,
            "Describe this scene in detail. What objects do you see and how are they arranged?",
            base_url=base_url,
            max_tokens=300
        )
        print(f"Analysis: {complex_analysis}")
    except Exception as e:
        print(f"Error analyzing complex image: {e}")
    
    print("=" * 60)


def load_external_image(image_path: str) -> Image.Image:
    """
    Load an external image file.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        PIL Image object
        
    Raises:
        FileNotFoundError: If image file doesn't exist
        Exception: If image cannot be loaded
    """
    try:
        return Image.open(image_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Image file not found: {image_path}")
    except Exception as e:
        raise Exception(f"Error loading image: {e}")


def resize_image(img: Image.Image, max_size: Tuple[int, int] = (800, 600)) -> Image.Image:
    """
    Resize image while maintaining aspect ratio.
    
    Args:
        img: PIL Image object
        max_size: Maximum size as (width, height)
        
    Returns:
        Resized PIL Image object
    """
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    return img
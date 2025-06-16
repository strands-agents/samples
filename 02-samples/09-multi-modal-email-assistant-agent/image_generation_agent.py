#!/usr/bin/env python3
"""
Image Generation Agent

A tool for generating and saving images using Amazon Bedrock Nova Canvas model.
"""

import os
import re
import base64
import json
import boto3
import argparse
from datetime import datetime
from typing import Any, Dict
from IPython.display import Image, display

from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import think


# Create directory for saved images if it doesn't exist
SAVE_DIR = "generated_images"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)


@tool
def generate_image_nova(
    prompt: str, model_id: str = "amazon.nova-canvas-v1:0", number_of_images: int = 1
) -> Dict[str, Any]:
    """
    Generate an images using Nova Canvas model based on a text prompt.

    Args:
        prompt: The text prompt for images generation
        model_id: Model ID for images model (default: amazon.nova-canvas-v1:0)
        number_of_images: Number of images to generate (default: 1)

    Returns:
        Dictionary containing the result and images path
    """
    try:
        # Create a Bedrock Runtime client
        client = boto3.client("bedrock-runtime", region_name="us-east-1")

        # Enhanced prompt
        enhanced_prompt = f"Generate a high resolution, photo realistic picture of {prompt} with vivid color and attending to details."

        # Format the request payload
        request_payload = {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {"text": enhanced_prompt},
            "imageGenerationConfig": {"numberOfImages": number_of_images},
        }

        # Invoke the model
        response = client.invoke_model(
            body=json.dumps(request_payload),
            modelId=model_id,
            accept="application/json",
            contentType="application/json",
        )

        # Parse the response
        response_body = json.loads(response["body"].read())
        base64_image = response_body.get("images")[0]

        # Decode the images
        image_bytes = base64.b64decode(base64_image.encode("ascii"))

        # Create filename with timestamp and sanitized prompt
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sanitize prompt for filename
        safe_prompt = re.sub(r"[^a-zA-Z0-9]", "_", prompt[:30])  # Take first 30 chars
        filename = f"{SAVE_DIR}/nova_{safe_prompt}_{timestamp}.png"

        # Save the images immediately
        with open(filename, "wb") as f:
            f.write(image_bytes)

        # Try to display the images if in a notebook environment
        try:
            display(Image(data=image_bytes))
        except:
            pass  # Not in a notebook environment

        # OPTION 1: Don't return the base64 images data
        return {
            "status": "success",
            "image_path": filename,
            "message": f"✨ Generated images for prompt: '{prompt}' and saved to {filename}",
            "prompt": prompt,
        }

    except Exception as e:
        return {"status": "error", "message": f"❌ Error generating images: {str(e)}"}


def create_image_agent() -> Agent:
    """Create and configure the images generation agent."""
    return Agent(
        system_prompt="""You are an AI assistant that can generate images and save them to files.
You can:
1. Generate images using the generate_image_nova tool
2. Save files using the file_write tool

When users want to:
- Generate an images: Use generate_image_nova with their description as the prompt
- Save the generated images: Use file_write with the images path from the previous generation
- Both: First generate, then save the images

Always confirm actions and provide clear feedback about what was done.""",
        model=BedrockModel(model_id="us.amazon.nova-pro-v1:0", region="us-east-1"),
        tools=[generate_image_nova, think],
    )


def run_image_agent(region: str = "us-east-1") -> None:
    """
    Run the images generation agent.

    Args:
        region: AWS region for Bedrock
    """
    # Create the images agent
    image_agent = create_image_agent()

    # Track the last generated images path
    last_image_path = None

    print("\n🎨 AI Image Generator and File Manager 🖼️\n")
    print("Commands:")
    print("- Generate images: describe what you want to see")
    print("- Save images: ask to save the last generated images")
    print("- Exit: type 'exit'\n")

    # Initialize the agent with the proper message format
    image_agent.messages = create_initial_messages()

    while True:
        user_input = input("\nCommand> ")

        if user_input.lower() == "exit":
            print("\nGoodbye! 👋")
            break

        print("\nProcessing...\n")

        try:
            # Add context about the last generated images if available
            message_text = user_input
            if last_image_path and "save" in user_input.lower():
                message_text += (
                    f"\n\nNote: The last generated images is at: {last_image_path}"
                )

            # Create the user message with proper format
            user_message = {"role": "user", "content": [{"text": message_text}]}

            # Reset conversation but keep the proper format
            image_agent.messages = create_initial_messages()
            image_agent.messages.append(user_message)

            # Get response
            response = image_agent(message_text)

            # Check if an images was generated in this interaction
            if isinstance(response, dict) and "toolResults" in response:
                for tool_result in response["toolResults"]:
                    if (
                        tool_result.get("name") == "generate_image_nova"
                        and tool_result.get("status") == "success"
                    ):
                        # Extract images path
                        result = tool_result.get("result", {})
                        last_image_path = result.get("image_path")

            # Print response
            if isinstance(response, dict) and "message" in response:
                print(response["message"]["content"][0]["text"])
            else:
                print("Done!\n")

        except Exception as e:
            print(f"Error: {str(e)}\n")


def create_initial_messages():
    """Create initial conversation messages with the proper format."""
    return [
        {
            "role": "user",
            "content": [{"text": "Hello, I need help generating images."}],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "text": "I'm ready to help you generate images. Please describe what you'd like to see, and I'll create it for you."
                }
            ],
        },
    ]


def main():
    """Command line interface for the images generation agent."""
    parser = argparse.ArgumentParser(description="Image Generation Agent")
    parser.add_argument(
        "--region", type=str, default="us-east-1", help="AWS region for Bedrock"
    )

    args = parser.parse_args()

    run_image_agent(args.region)


if __name__ == "__main__":
    main()

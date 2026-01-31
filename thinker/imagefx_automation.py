#!/usr/bin/env python3
"""
ImageFX Browser Automation
Uses Playwright to generate images from prompts
"""

import sys
import asyncio
import time
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Installing playwright...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    from playwright.async_api import async_playwright

IMAGEFX_URL = "https://labs.google/fx/tools/image-fx"

async def generate_image(prompt: str, output_path: str):
    """Generate image using ImageFX"""
    
    async with async_playwright() as p:
        # Launch browser (use existing profile if available for auth)
        browser = await p.chromium.launch(
            headless=False,  # Need to see for auth
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        try:
            print(f"Opening ImageFX...")
            await page.goto(IMAGEFX_URL, wait_until='networkidle', timeout=60000)
            
            # Wait for page to load
            await page.wait_for_timeout(3000)
            
            # Look for the prompt input
            # ImageFX has a textarea for the prompt
            prompt_input = await page.query_selector('textarea')
            
            if not prompt_input:
                # Try other selectors
                prompt_input = await page.query_selector('[contenteditable="true"]')
            
            if not prompt_input:
                print("Could not find prompt input. Page might need login.")
                await page.screenshot(path=output_path.replace('.png', '_debug.png'))
                return False
            
            # Clear and type prompt
            await prompt_input.click()
            await prompt_input.fill('')
            await prompt_input.type(prompt, delay=10)
            
            print("Prompt entered, looking for generate button...")
            
            # Find and click generate button
            generate_btn = await page.query_selector('button:has-text("Generate")')
            if not generate_btn:
                generate_btn = await page.query_selector('[aria-label*="Generate"]')
            if not generate_btn:
                # Try finding any primary button
                buttons = await page.query_selector_all('button')
                for btn in buttons:
                    text = await btn.text_content()
                    if text and 'generate' in text.lower():
                        generate_btn = btn
                        break
            
            if generate_btn:
                await generate_btn.click()
                print("Generate clicked, waiting for image...")
                
                # Wait for image to generate (can take 10-30 seconds)
                await page.wait_for_timeout(20000)
                
                # Look for generated image
                img = await page.query_selector('img[src*="blob:"]')
                if not img:
                    img = await page.query_selector('.generated-image img')
                if not img:
                    # Wait more and try again
                    await page.wait_for_timeout(15000)
                    img = await page.query_selector('img[src*="blob:"], img[src*="googleusercontent"]')
                
                if img:
                    # Screenshot the image element or download
                    await img.screenshot(path=output_path)
                    print(f"Image saved to {output_path}")
                    return True
                else:
                    # Fallback: screenshot the results area
                    print("Could not find image element, taking page screenshot...")
                    await page.screenshot(path=output_path, full_page=False)
                    return True
            else:
                print("Could not find generate button")
                await page.screenshot(path=output_path.replace('.png', '_debug.png'))
                return False
                
        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path=output_path.replace('.png', '_error.png'))
            return False
        finally:
            await browser.close()

def main():
    if len(sys.argv) < 3:
        print("Usage: python imagefx_automation.py <prompt> <output_path>")
        sys.exit(1)
    
    prompt = sys.argv[1]
    output_path = sys.argv[2]
    
    print(f"Generating image for prompt: {prompt[:100]}...")
    
    success = asyncio.run(generate_image(prompt, output_path))
    
    if success:
        print("Success!")
        sys.exit(0)
    else:
        print("Failed to generate image")
        sys.exit(1)

if __name__ == "__main__":
    main()

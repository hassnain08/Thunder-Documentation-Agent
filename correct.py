# custom_tool.py
import os, json, time, hashlib
from typing import Type, List
from PIL import Image
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import google.generativeai as genai
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess


load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))  # ✅ Don't duplicate configure
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

# Tool 1: Selenium Screenshot
class ScreenshotToolInput(BaseModel):
    url: str

class SeleniumScriptExecutor(BaseTool):
    name: str = "Selenium Script Executor"
    description: str = "Runs dynamic Selenium Python scripts"

    class Args(BaseModel):
        script_code: str
        folder: str

    def _run(self, script_code: str, folder: str) -> List[str]:
        script_path = os.path.join(folder, "script.py")
        os.makedirs(folder, exist_ok=True)

        with open(script_path, "w") as f:
            f.write(script_code)
        
        result = subprocess.run(["python", script_path], capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Script failed:\n{result.stderr}")

        image_paths = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.endswith(".png")
        ]

        if not image_paths:
            raise FileNotFoundError("❌ No screenshots were saved.")

        return image_paths



# Tool 2: Gemini Image Analyzer
class ImageAnalyzerInput(BaseModel):
    screenshot_paths: List[str] = Field(..., description="List of image paths")

class VisualAnalyzer(BaseTool):
    name: str = "Visual Analyzer"
    description: str = "Analyzes screenshots and saves results to insights.json"
    args_schema: Type[BaseModel] = ImageAnalyzerInput

    def _run(self, screenshot_paths: List[str]) -> List[dict]:
        insights = []
        os.makedirs("insights", exist_ok=True)

        print(f"[VisualAnalyzer] Total screenshots to process: {len(screenshot_paths)}")

        for path in screenshot_paths:
            try:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"{path} not found, skipping")

                print(f"[Analyzing] {path}")

                with Image.open(path) as img:
                    response = gemini_model.generate_content([
    img,
    """You're analyzing a cropped screenshot of a chart from the Our World in Data AI dataset page.
    Extract:
    - Title of the chart (from any text inside the image)
    - Type of chart (e.g. bar, line, scatter)
    - Summary of trends shown (e.g. upward, flat, cyclical)
    - Any axis labels or numbers shown

    If the image does not contain a chart, skip it."""
]
)

                    if not response or not response.text or "not a chart" in response.text.lower():
                        print(f"[Skipped]: Not a chart -> {path}")
                        continue

                    insights.append({
                        "image": path,
                        "analysis": response.text.strip()
                    })

                    print(f"[Saved insight] {path}")

                time.sleep(1)

            except Exception as e:
                print(f"[Error analyzing] {path}: {e}")
                insights.append({
                    "image": path,
                    "analysis": f"Error: {str(e)}"
                })

        if insights:
            with open("insights/insights.json", "w") as f:
                json.dump(insights, f, indent=2)
            print(f"[✅] Saved {len(insights)} insights -> insights/insights.json")
        else:
            print("[⚠️] No insights saved.")

        return insights
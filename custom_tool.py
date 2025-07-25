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

genai.configure(api_key=os.getenv("GOOGLE_API_KEY")) 
gemini_model = genai.GenerativeModel("gemini-2.5-flash")

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
        print("Running SCRIPT>>>>>>>>>")
        try:
            result = subprocess.run(["python", script_path], capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            raise RuntimeError("⏱️ Script took too long and was killed after 120 seconds.")
        print("ENDING SCRIPT>>>>>>>>>")

        if result.returncode != 0:
            raise RuntimeError(f"❌ Script failed:\n{result.stderr}")

        image_paths = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.endswith(".png")
        ]

        if not image_paths:
            raise FileNotFoundError("❌ No screenshots were saved.")

        return {
        "status": "success",
        "paths": image_paths  # image_paths must be a list of valid PNG paths
        }





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
                        """You’re analyzing a cropped screenshot of a chart from the Thunder Energy dashboard.
                        Extract:
                        - Title (from visible text in the chart)
                        - Type of graph
                        - Data trend (upward, flat, seasonal, etc.)
                        - OCR any key metrics or labels
                        If not a chart, skip."""
                        ])


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

        # Load existing insights if present
        insights_path = "insights/insights.json"
        existing = []
        if os.path.exists(insights_path):
            with open(insights_path, "r") as f:
                try:
                    existing = json.load(f)
                except Exception as e:
                    print(f"[Warning] Could not load existing insights: {e}")
                    existing = []

        # Merge and deduplicate by image path
        all_insights = {entry['image']: entry for entry in existing + insights}.values()

        if all_insights:
            with open(insights_path, "w") as f:
                json.dump(list(all_insights), f, indent=2)
            print(f"[✅] Saved {len(all_insights)} total insights -> {insights_path}")
        else:
            print("[⚠️] No insights saved.")

        return list(all_insights)

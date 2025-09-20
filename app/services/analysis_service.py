import os
from google import genai
from google.genai import types
from typing import List
from app.core.config import settings
from app.prompts.system_prompts import ANALYSIS_AGENT_PROMPT

class AnalysisService:
    """
    This service handles the AI-powered analysis of pre-scraped financial data.
    """
    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        print("AnalysisService initialized with Gemini client.")

    def upload_files_to_gemini(self, file_paths: List[str]) -> List[str]:
        """
        Upload local files to Gemini and return their remote names.
        """
        if not file_paths:
            return []
        print(f"Uploading {len(file_paths)} files to Gemini...")
        uploaded_names: List[str] = []
        for path in file_paths:
            if os.path.exists(path) and os.path.getsize(path) > 0:
                try:
                    uploaded_file = self.client.files.upload(file=path)
                    uploaded_names.append(uploaded_file.name)
                    print(f"Successfully uploaded: {os.path.basename(path)}")
                except Exception as e:
                    print(f"Failed to upload {path}: {e}")
            else:
                print(f"Skipping empty or non-existent file: {path}")
        return uploaded_names

    def generate_report_from_gemini_files(self, uploaded_file_names: List[str]) -> str:
        """
        Given Gemini file names (already uploaded), fetch them and generate the analysis report.
        """
        if not uploaded_file_names:
            return "Error: No uploaded Gemini files were provided for analysis."

        # Configure the model to use Google Search
        grounding_tool = types.Tool(google_search=types.GoogleSearch())
        config = types.GenerateContentConfig(
            tools=[grounding_tool],
        )

        # Retrieve File objects by name for inclusion in contents
        files = []
        for name in uploaded_file_names:
            try:
                files.append(self.client.files.get(name=name))
            except Exception as e:
                print(f"Warning: Could not fetch Gemini file by name {name}: {e}")

        if not files:
            return "Error: None of the referenced Gemini files could be retrieved."

        # Compose contents
        user_prompt = "Please analyze the provided data files."
        contents = [ANALYSIS_AGENT_PROMPT] + files + [user_prompt]

        print("Generating content with Gemini...")
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=config,
            )
            print("Successfully received response from Gemini.")
            return response.text
        except Exception as e:
            print(f"Error during Gemini content generation: {e}")
            return f"Error: The analysis could not be completed. Details: {str(e)}"

    def delete_gemini_files(self, uploaded_file_names: List[str]) -> None:
        """
        Delete a list of Gemini uploaded files by name.
        """
        if not uploaded_file_names:
            return
        print("Cleaning up uploaded files from Gemini...")
        for name in uploaded_file_names:
            try:
                self.client.files.delete(name=name)
            except Exception as e:
                print(f"Could not delete file {name}: {e}")
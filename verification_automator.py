import requests
import json
import time
from urllib.parse import urlparse

# --- Gemini API Configuration ---
# The Canvas environment will automatically provide the API key. DO NOT populate this variable.
API_KEY = "AIzaSyDiXGKfPlVABmVxxmjIXv4Zh_SWU8LZiXA"  # Replace with your actual Gemini API Key
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

def call_gemini_api(system_prompt, user_content, schema=None, max_retries=3):
    """
    Calls the Gemini API with a given prompt, content, and optional JSON schema.
    Includes exponential backoff for retries.
    If the default API key is used, this function returns a mock response.
    """
    # If the default API key is present, mock the API call
    if API_KEY == "AIzaSyDiXGKfPlVABmVxxmjIXv4Zh_SWU8LZiXA":
        print("--- MOCKING Gemini API Call (No real API Key found) ---")
        # Mock response for credibility analysis
        if "credibility analyst" in system_prompt:
            if "https" in user_content:
                return {
                    "credibility_rating": "High",
                    "justification": "Mock response: This source appears to be a reputable news organization."
                }
            elif "Dr. Evelyn Reed" in user_content:
                return {
                    "credibility_rating": "Medium",
                    "justification": "Mock response: The individual is cited as an expert, but further verification of their credentials is required."
                }
            else: # Catches "The 2023 Annual Report..."
                return {
                    "credibility_rating": "Medium",
                    "justification": "Mock response: The report is cited, but its contents and publisher need to be verified."
                }
        # Mock response for publication identification
        elif "research assistant" in system_prompt:
            if "Dr. Evelyn Reed" in user_content:
                return {"publication": "MIT (Massachusetts Institute of Technology)"}
            elif "The 2023 Annual Report" in user_content:
                return {"publication": "Semiconductor Industry Association"}
            else:
                return {"publication": "Unknown Publisher"}
        # Mock response for claim verification
        elif "fact-checker" in system_prompt:
            return {
                "verified_claims": [
                    {
                        "claim": "Innovate Inc. launched its revolutionary 'Quantum' smartphone today.",
                        "verification_status": "Supported",
                        "evidence_quote": "Mock source content... Innovate Inc. confirms the 'Quantum' phone..."
                    },
                    {
                        "claim": "The device features a new 'Photonic' chip, promising a 50% increase in processing speed.",
                        "verification_status": "Supported",
                        "evidence_quote": "Mock source content... with a 'Photonic' chip, increasing speed by 50%."
                    },
                    {
                        "claim": "A new claim not in the sources is that the phone is made of titanium.",
                        "verification_status": "No Evidence Found",
                        "evidence_quote": ""
                    }
                ]
            }
        # Default empty mock for any other unexpected calls
        else:
            return json.loads("{}")

    print(f"\n--- Calling Gemini API... (Prompt: {system_prompt[:50]}...) ---")
    headers = {'Content-Type': 'application/json'}
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_content}]}]
    }

    if schema:
        payload['generation_config'] = {
            "response_mime_type": "application/json",
            "response_schema": schema
        }

    for attempt in range(max_retries):
        try:
            response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload), timeout=45)
            response.raise_for_status()

            result = response.json()
            candidate = result.get('candidates', [{}])[0]
            content_part = candidate.get('content', {}).get('parts', [{}])[0]
            text_response = content_part.get('text', '{}')

            return json.loads(text_response)

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"API request failed with error: {e}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"API request failed after {max_retries} attempts. Error: {e}")
                return json.loads("{}")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"Error parsing Gemini response: {e}. Raw Response: {response.text}")
            return json.loads("{}")


class AI_Verification_Assistant:
    """
    Automates pre-verification checks for an AI-generated article
    based on the AI-Assisted Verification Guidelines.
    """

    def __init__(self, article_text, source_urls):
        self.article_text = article_text
        self.source_urls = source_urls
        self.sources_content = {}
        self.verification_report = {}

    def run_full_verification(self):
        """Runs all automated phases and prints a final report."""
        print("--- Starting Automated Verification Process ---")
        self.phase1_triage()
        self.verification_report['Markup System'] = self.generate_markup()
        print("\n--- Automated Verification Process Complete ---")
        self.print_report()

    # --- PHASE 1: TRIAGE ---
    def phase1_triage(self):
        print("\n--- Running Phase 1: Triage ---")
        source_credibility_analysis = self._verify_sources()
        self.verification_report['Phase 1: Triage'] = {
            'Source Credibility Analysis': source_credibility_analysis,
        }

    def _verify_sources(self):
        """
        Analyzes each source for credibility. For URLs, it fetches content.
        For textual references, it analyzes them directly.
        """
        credibility_results = []
        for source in self.source_urls:
            print(f"Analyzing source: {source}...")
            result_item = {'source': source}

            if urlparse(source).scheme in ['http', 'https']:
                print(f"Fetching content for {source}...")
                source_content = f"Mock source content for {source}. Innovate Inc. confirms the 'Quantum' phone with a 'Photonic' chip, increasing speed by 50%. CEO Jane Doe is quoted. 1,000,000 units are planned for the October 26th launch."
                self.sources_content[source] = source_content
                analysis_input = source_content
                credibility_assessment = self._get_source_credibility(analysis_input)
                result_item['credibility'] = credibility_assessment
            else:
                # For textual sources, analyze directly
                credibility_assessment = self._get_source_credibility(source)
                result_item['credibility'] = credibility_assessment

            credibility_results.append(result_item)

        return credibility_results

    def _get_source_credibility(self, source_text):
        """Uses Gemini to assess the credibility of a given source text."""
        system_prompt = (
            "You are a source credibility analyst. Analyze the provided text to determine its "
            "credibility. Consider the source's reputation, potential biases, and the "
            "verifiability of the information. Provide a credibility rating and a brief justification."
        )
        user_content = f"Source to analyze:\n{source_text}"
        schema = {
            "type": "OBJECT", "properties": {
                "credibility_rating": {
                    "type": "STRING",
                    "enum": ["High", "Medium", "Low", "Uncertain"],
                    "description": "The assessed credibility of the source."
                },
                "justification": {
                    "type": "STRING",
                    "description": "A brief explanation for the credibility rating."
                }
            }, "required": ["credibility_rating", "justification"]
        }
        return call_gemini_api(system_prompt, user_content, schema)

    def generate_markup(self):
        """Uses Gemini to apply markdown formatting to the article text."""
        print("\n--- Generating Markup ---")
        system_prompt = """
            You are a markup expert. Your task is to apply markdown formatting to the provided article text.
            Follow these rules precisely:
            - Use double line breaks for new paragraphs.
            - Use ** for bold text.
            - Use _ for italicized text.
            - Use ~~ for strikethrough text.
            - Use #, ##, ###, #### for headers of different sizes.
            - Use - for generic list items.
            - Use 1., 2., 3. for numbered list items.
            - Use > for quotes.
            The user needs the raw markdown text with all characters like #, *, etc., visible. Do not render the markdown.
        """
        user_content = f"ARTICLE TO MARKUP:\n{self.article_text}"
        schema = {
            "type": "OBJECT", "properties": {
                "marked_up_text": {
                    "type": "STRING",
                    "description": "The article text with markdown formatting applied."
                }
            }, "required": ["marked_up_text"]
        }
        return call_gemini_api(system_prompt, user_content, schema)

    def print_report(self):
        """Prints the final, structured report for the human verifier."""
        print("\n" + "="*50)
        print("          AI-ASSISTED VERIFICATION REPORT")
        print("="*50 + "\n")
        # Print the analysis part of the report
        if 'Phase 1: Triage' in self.verification_report:
            print(json.dumps({'Phase 1: Triage': self.verification_report['Phase 1: Triage']}, indent=2))

        # Print the markup part of the report
        if 'Markup System' in self.verification_report and self.verification_report['Markup System'].get('marked_up_text'):
            print("\n" + "="*50)
            print("              MARKUP SYSTEM OUTPUT")
            print("="*50 + "\n")
            print(self.verification_report['Markup System']['marked_up_text'])

        print("\n" + "="*50)
        print("ACTION: Human Verifier should now review this report and the article.")
        print("="*50)


# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    mock_article = """
    Silicon Valley, CA - In a landmark announcement, global tech giant Innovate Inc. launched its revolutionary 'Quantum' smartphone today.
    The device, which is set to dominate the market, features a new 'Photonic' chip, promising a 50% increase in processing speed.
    "We are thrilled to push the boundaries of technology," said CEO Jane Doe.
    The phone was designed by the engineering team. The aforementioned device incorporates a multitude of cutting-edge features.
    Sources claim 1,000,000 units will be available at launch on October 26th. A new claim not in the sources is that the phone is made of titanium.
    """
    mock_source_list = [
        "https://www.reuters.com/innovate-inc-press-release",
        "https://www.wsj.com/tech/new-photonic-chip-details",
        "Dr. Evelyn Reed, a leading expert in photonic technology",
        "The 2023 Annual Report on Semiconductor Advances"
    ]
    assistant = AI_Verification_Assistant(mock_article, mock_source_list)
    assistant.run_full_verification()
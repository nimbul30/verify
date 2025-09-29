import requests
import json
import time
from urllib.parse import urlparse

# --- Gemini API Configuration ---
# The Canvas environment will automatically provide the API key. DO NOT populate this variable.
API_KEY = "AIzaSyDiXGKfPlVABmVxxmjIXv4Zh_SWU8LZiXA"  # Replace with your actual Gemini API Key
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"

def call_gemini_api(system_prompt, user_content, schema=None, max_retries=3):
    """
    Calls the Gemini API with a given prompt, content, and optional JSON schema.
    Includes exponential backoff for retries.
    """
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
        print("\n--- Automated Verification Process Complete ---")
        self.print_report()

    # --- PHASE 1: TRIAGE ---
    def phase1_triage(self):
        print("\n--- Running Phase 1: Triage ---")
        source_check_results = self._check_source_links()
        # MODIFIED: Called the new deep verification function
        claim_verification = self._deep_claim_verification()
        self.verification_report['Phase 1: Triage'] = {
            'Source Link Check': source_check_results,
            'Deep Claim Verification': claim_verification # MODIFIED: Updated the report key
        }

    def _check_source_links(self):
        """Performs Link Validation and Domain Reputation Analysis for URLs and identifies non-URL sources."""
        results = []
        for source in self.source_urls:
            # Check if the source is a URL by attempting to parse it
            if source.startswith('http://') or source.startswith('https://'):
                try:
                    # In a real-world scenario, you would use a library like BeautifulSoup
                    # to scrape the actual content. For this example, we'll continue to mock it.
                    print(f"Fetching content for {source}...")
                    self.sources_content[source] = f"Mock source content for {source}. Innovate Inc. confirms the 'Quantum' phone with a 'Photonic' chip, increasing speed by 50%. CEO Jane Doe is quoted. 1,000,000 units are planned for the October 26th launch."
                    parsed_url = urlparse(source)
                    domain = parsed_url.netloc
                    tld = domain.split('.')[-1]

                    if tld in ['gov', 'edu']:
                        domain_type = "High-Reputation (Government/Education)"
                    elif any(news in domain for news in ['reuters', 'ap', 'bbc', 'wsj']):
                        domain_type = "Reputable News Source"
                    else:
                        domain_type = "General/Blog"

                    results.append({'url': source, 'status': 'URL', 'domain_type': domain_type})

                except requests.RequestException as e:
                    results.append({'url': source, 'status': 'Error', 'reason': str(e)})
            else:
                # If it's not a URL, treat it as a non-URL reference
                results.append({'url': source, 'status': 'Non-URL Reference', 'domain_type': 'Needs Manual Verification'})
        return results

    # MODIFIED: This function now performs deep verification.
    def _deep_claim_verification(self):
        """Uses Gemini to perform deep verification of article claims against source content."""
        system_prompt = (
            "You are a meticulous fact-checker. From the article, extract each key claim. "
            "For each claim, search the provided source texts for direct evidence. "
            "You must classify the evidence for each claim as either 'Supported', 'Contradicted', or 'No Evidence Found'. "
            "If evidence is found, you must provide the exact quote from the source text as 'evidence_quote'."
        )
        user_content = f"ARTICLE TO VERIFY:\n{self.article_text}\n\nSOURCE TEXTS:\n{''.join(self.sources_content.values())}"
        schema = {
            "type": "OBJECT", "properties": {
                "verified_claims": { "type": "ARRAY", "items": {
                    "type": "OBJECT", "properties": {
                        "claim": {"type": "STRING", "description": "The specific claim extracted from the article."},
                        "verification_status": {
                            "type": "STRING",
                            "enum": ["Supported", "Contradicted", "No Evidence Found"],
                            "description": "The verification status of the claim."
                        },
                        "evidence_quote": {"type": "STRING", "description": "The direct quote from the source text that supports or contradicts the claim. Should be empty if no evidence is found."}
                    }, "required": ["claim", "verification_status", "evidence_quote"]
                }}
            }
        }
        return call_gemini_api(system_prompt, user_content, schema)


    def print_report(self):
        """Prints the final, structured report for the human verifier."""
        print("\n" + "="*50)
        print("          AI-ASSISTED VERIFICATION REPORT")
        print("="*50 + "\n")
        print(json.dumps(self.verification_report, indent=2))
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
    ]
    assistant = AI_Verification_Assistant(mock_article, mock_source_list)
    assistant.run_full_verification()
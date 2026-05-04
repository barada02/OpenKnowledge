import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_openai_client():
    # Only initialize if API key is present
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        return None
        
    base_url = os.getenv("OPENAI_BASE_URL")
    if not base_url:
        base_url = None # Let the library use its default if it's empty string
        
    return OpenAI(
        api_key=api_key,
        base_url=base_url
    )

def extract_triples(text: str) -> list:
    """
    Extracts Subject-Predicate-Object triples from the text using an LLM.
    """
    client = get_openai_client()
    if not client:
        raise ValueError("OpenAI Client not initialized. Check your OPENAI_API_KEY in .env.")
        
    model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
    
    prompt = f"""
    You are an expert knowledge graph data extractor.
    Extract meaningful relationships from the text below.
    Return the result STRICTLY as a JSON array of objects. 
    Each object must have exactly three keys: 'source', 'relation', and 'target'.
    The 'relation' should be a short uppercase string with underscores instead of spaces (e.g., WORKED_AT, OWNS, IS_LOCATED_IN).
    DO NOT wrap your response in markdown code blocks. Output ONLY the JSON array.
    
    Text: {text}
    """
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You output only valid JSON arrays. No explanation, no markdown."},
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up possible markdown block if the model ignores the instruction
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        data = json.loads(content.strip())
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error calling LLM: {e}")
        raise e

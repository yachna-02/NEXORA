uploaded=""
import sys
import whisper

model = whisper.load_model("medium")
result = model.transcribe(list(uploaded.keys())[0])
print(result["text"])

# !pip install boto3 -q

import os

#  Set your AWS credentials (replace with your actual keys)


aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

import boto3

# Create a client for AWS Comprehend Medical
comprehend_medical = boto3.client("comprehendmedical")

# Pass the transcript to AWS Comprehend Medical
def analyze_medical_text(text):
    try:
        # Call the Comprehend Medical DetectEntities API
        response = comprehend_medical.detect_entities_v2(Text=text)

        # Extract medical information
        entities = response["Entities"]
        print("🔍 Medical Information Detected:")
        for entity in entities:
            print(f"Entity: {entity['Text']}, Type: {entity['Category']}, Confidence: {entity['Score']:.2f}")

        return entities
    except Exception as e:
        print("Error analyzing text:", e)

# Assuming 'result' is the output from Whisper transcription (from previous cell)
transcript = result["text"]  # Assign the transcribed text to 'transcript'


# Analyze the transcript
medical_entities = analyze_medical_text(transcript)

import boto3
import requests
from collections import defaultdict

# Initialize AWS Comprehend Medical client
comprehend = boto3.client('comprehendmedical')

def extract_medical_entities(text):
    """Extract medications and symptoms using AWS Comprehend Medical"""
    try:
        response = comprehend.detect_entities_v2(Text=text)
        entities = response['Entities']
    except Exception as e:
        print(f"Error from Comprehend Medical: {e}")
        return [], []

    medications = set()
    symptoms = set()

    for entity in entities:
        category = entity['Category']
        text = entity['Text'].strip().lower()

        if category == 'MEDICATION':
            medications.add(text)
        elif category == 'MEDICAL_CONDITION':
            symptoms.add(text)

    return sorted(medications), sorted(symptoms)

def fetch_adverse_events(drug_name, limit=10):
    """Query FAERS API for known adverse reactions of a given drug"""
    url = f"https://api.fda.gov/drug/event.json?search=patient.drug.medicinalproduct:{drug_name}&limit={limit}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        reactions = set()

        for event in data.get("results", []):
            for reaction in event.get("patient", {}).get("reaction", []):
                rxn = reaction.get("reactionmeddrapt", "").lower()
                if rxn:
                    reactions.add(rxn)
        return list(reactions)
    except Exception:
        return []

def compute_risk_score(reactions):
    """Assign basic risk score based on severity keywords"""
    score = 0
    for r in reactions:
        if "death" in r:
            score += 3
        elif "severe" in r or "shock" in r or "anaphylaxis" in r:
            score += 2
        else:
            score += 1
    return min(score, 10)

def generate_summary(transcript):
    """Generate a plain-text medical summary based on conversation"""
    if not transcript.strip():
        return "Transcript is empty or missing."

    meds, symptoms = extract_medical_entities(transcript)

    summary = "\n--- MEDICAL SUMMARY ---\n\n"
    summary += f"🗣 Transcript Analysis Complete.\n\n"
    summary += f"💊 Medications Detected:\n"
    summary += "\n".join(f"- {m.title()}" for m in meds) if meds else "- None Detected"
    summary += "\n\n🩺 Symptoms Mentioned:\n"
    summary += "\n".join(f"- {s.title()}" for s in symptoms) if symptoms else "- None Detected"

    summary += "\n\n⚠️ Adverse Events Predicted with respect to medications:\n"
    risk_scores = {}

    for med in meds:
        reactions = fetch_adverse_events(med)
        risk = compute_risk_score(reactions)
        risk_scores[med] = risk
        top_rxns = ", ".join(reactions[:5]) if reactions else "No known reactions found."
        summary += f"- {med.title()}: {top_rxns}\n"

    summary += "\n📊 Risk Scores:\n"
    for med, score in risk_scores.items():
        level = "Low" if score <= 3 else "Medium" if score <= 6 else "High"
        summary += f"- {med.title()}: {score}/10 ({level} Risk)\n"

    summary += "\n🧠 Clinical Insights:\n"
    if not meds and not symptoms:
        summary += "- No actionable data found.\n"
    else:
        if any("cough" in s for s in symptoms):
            summary += "- Persistent cough can be a side effect of several ACE inhibitors.\n"
        if any("dizziness" in s or "faint" in s for s in symptoms):
            summary += "- Dizziness may be due to low blood pressure or medication interaction.\n"
        if any("nausea" in s or "vomiting" in s for s in symptoms):
            summary += "- Monitor GI symptoms, especially if using NSAIDs or antibiotics.\n"

    return summary.strip()

# Example usage (replace this with input from Whisper or UI later)
if __name__ == "__main__":
    # sample = """
    # I've been taking metformin and atorvastatin for the past month.
    # Lately I've been feeling nauseous and sometimes dizzy.
    # Also noticed occasional stomach cramps and dry mouth.
    # Should I be worried about side effects?
    # """
    final_output = generate_summary(transcript)
    print(final_output)


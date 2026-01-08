import pandas as pd
import google.generativeai as genai
import time  
import PIL.Image, PIL.ImageDraw

# 1. Configuration
genai.configure(api_key="AIzaSyD3kNHJX1ROFh53NiI4Y0lYW-VU5_S2JQ0") 
model = genai.GenerativeModel('gemini-2.5-flash')

def draw_manual_overlay(image_path, box_coords):
    """Draws a red translucent box over the car part."""
    try:
        img = PIL.Image.open(image_path).convert("RGBA")
        overlay = PIL.Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = PIL.ImageDraw.Draw(overlay)
        # Red box with 50% transparency (255, 0, 0, 128)
        draw.rectangle(box_coords, outline="red", width=10, fill=(255, 0, 0, 80))
        return PIL.Image.alpha_composite(img, overlay).convert("RGB")
    except Exception as e:
        return None

def run_audit(ro_id, audio_path=None):
    leaks = []
    try:
        scanned = pd.read_csv('parts_scanned.csv')
        invoice = pd.read_csv('final_invoice.csv')
        notes = pd.read_csv('mechanic_notes.csv')
    except Exception as e:
        return [f"File Error: {e}"], "Could not load database."

    ro_id = str(ro_id)
    billed_list = invoice[invoice['ro_id'].astype(str) == ro_id]['item_id'].tolist()
    physical_list = scanned[scanned['ro_id'].astype(str) == ro_id]['part_id'].tolist()
    
    note_row = notes[notes['ro_id'].astype(str) == ro_id]
    tech_note = note_row['note_text'].iloc[0] if not note_row.empty else "No notes found."

    try:
        prompt = f"Identify car parts mentioned in this note: '{tech_note}'. Return a comma-separated list."
        ai_parts_response = model.generate_content(prompt)
        ai_parts = ai_parts_response.text.lower()
    except Exception as e:
        ai_parts = ""
        leaks.append(f"⚠️ AI Text Delay Error: {e}")

    diagnosis = ""
    # Inside your guard.py, update the audio section of run_audit:

    if audio_path:
        try:
            audio_file = genai.upload_file(path=audio_path)
            time.sleep(2) 
            
            # New specific prompt for parts identification
            sound_prompt = """
            Listen to this engine sound. 
            1. Provide a one-sentence diagnosis of the issue.
            2. Provide a comma-separated list of specific parts responsible for this sound.
            
            Format your response exactly like this:
            DIAGNOSIS: [Your diagnosis] | PARTS: [Part 1, Part 2]
            """
            
            diagnosis_response = model.generate_content([sound_prompt, audio_file])
            diagnosis = diagnosis_response.text
        except Exception as e:
            diagnosis = "DIAGNOSIS: Audio analysis skipped | PARTS: N/A"
            leaks.append(f"⚠️ AI Audio Delay Error: {e}")

    for part in physical_list:
        if part not in billed_list:
            leaks.append(f"Missing Charge: Part {part} was scanned but not billed.")
            
    if "clip" in ai_parts and "p103" not in str(billed_list).lower():
        leaks.append("Leak Found: Mechanic mentioned a 'clip' in notes, but it's not on the bill.")

    return leaks, diagnosis

def exterior_scan(before_img_path, after_img_path, filename=""):
    """Compares images or returns mock data for demo."""
    # MOCK MODE: If filename contains 'bumper', skip AI
    if "bumper" in filename.lower():
        # coordinates for a typical front bumper area: (left, top, right, bottom)
        mock_box = (150, 400, 850, 750) 
        mock_res = "PART: Front Bumper | COST: $1200 | REASON: Repaint and panel alignment."
        return mock_res, mock_box

    try:
        img_before = PIL.Image.open(before_img_path)
        img_after = PIL.Image.open(after_img_path)
        prompt = "Compare images. Return format: PART: [Name] | COST: [Price] | REASON: [Change]"
        response = model.generate_content([prompt, img_before, img_after])
        return response.text.strip(), None
    except Exception as e:
        return f"Error: {e}", None
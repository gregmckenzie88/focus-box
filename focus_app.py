import os
import re
import json
import random
import numpy as np
from datetime import datetime
from pydub import AudioSegment
from pydub.generators import Sine
from pydub.effects import low_pass_filter
from gtts import gTTS
import pytz

# NEW: import the spellchecker library
try:
    from spellchecker import SpellChecker
    spell = SpellChecker()
except ImportError:
    spell = None
    print("Warning: 'pyspellchecker' not found. Misspelled words will not be corrected.")

def generate_deep_layered_brown_noise(duration_ms=60000, sample_rate=44100, layer_count=3):
    """
    Generate a deeper, layered brown noise by:
      1) Generating multiple layers of brown noise
      2) Overlaying them
      3) Applying a low-pass filter
    """
    def single_brown_noise(duration_ms, sample_rate):
        num_samples = int(sample_rate * (duration_ms / 1000.0))
        brown_signal = np.zeros(num_samples, dtype=np.float64)
        last_out = 0.0
        
        for i in range(num_samples):
            white = random.uniform(-1.0, 1.0)
            brown_signal[i] = (last_out + (0.02 * white)) / 1.02
            last_out = brown_signal[i]
            brown_signal[i] *= 3.5
        
        brown_int16 = np.int16(brown_signal * 32767)
        
        brown_audio_mono = AudioSegment(
            data=brown_int16.tobytes(),
            sample_width=2,  # 16 bits
            frame_rate=sample_rate,
            channels=1
        )
        
        brown_audio_stereo = AudioSegment.from_mono_audiosegments(
            brown_audio_mono, brown_audio_mono
        )
        
        brown_audio_stereo = brown_audio_stereo.apply_gain(-10.0)
        return brown_audio_stereo

    layered_noise = None
    for _ in range(layer_count):
        layer = single_brown_noise(duration_ms, sample_rate)
        if layered_noise is None:
            layered_noise = layer
        else:
            layered_noise = layered_noise.overlay(layer)
    
    deep_brown_noise = low_pass_filter(layered_noise, cutoff=500)
    return deep_brown_noise

def text_to_speech(text, lang="en", slow=False):
    """
    Convert text to speech using gTTS.
    Steps:
      1) Replace non-alphanumeric chars with spaces
      2) Collapse extra spaces
      3) Spell-check each word (if pyspellchecker is installed)
      4) Send to gTTS
    """
    # Step 1 & 2: Sanitize text
    safe_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)  # Replace non-alphanumeric with space
    safe_text = re.sub(r'\s+', ' ', safe_text).strip() # Collapse spaces, trim ends
    
    # Step 3: Spell-check if spellchecker is available
    if spell is not None:
        words = safe_text.split()
        corrected_words = []
        for w in words:
            is_capitalized = (len(w) > 0 and w[0].isupper())
            lower_w = w.lower()
            
            corrected_w = spell.correction(lower_w)
            if corrected_w is None:
                corrected_w = lower_w
            
            if is_capitalized:
                corrected_w = corrected_w.capitalize()
            
            corrected_words.append(corrected_w)
        
        safe_text = " ".join(corrected_words)
    
    # Step 4: Pass safe_text to gTTS
    tts = gTTS(text=safe_text, lang=lang, slow=slow, tld="com")
    tts.save("temp_tts.mp3")
    spoken_audio = AudioSegment.from_file("temp_tts.mp3", format="mp3")
    os.remove("temp_tts.mp3")
    return spoken_audio

def generate_celebratory_sequence():
    """
    Generate a short celebratory *sequence* of notes (C, E, G, C up an octave).
    The last note is sustained twice as long to let it ring out.
    """
    note_frequencies = [523, 659, 783, 1046]  # C5, E5, G5, C6
    base_note_duration_ms = 400
    
    sequence = AudioSegment.silent(duration=0)
    
    for i, freq in enumerate(note_frequencies):
        if i == len(note_frequencies) - 1:
            note_duration = base_note_duration_ms * 2
        else:
            note_duration = base_note_duration_ms
        
        note = Sine(freq).to_audio_segment(duration=note_duration)
        
        if i == len(note_frequencies) - 1:
            note = note.apply_gain(-5.0).fade_in(50).fade_out(300)
        else:
            note = note.apply_gain(-5.0).fade_in(50).fade_out(50)
        
        sequence += note
    
    return sequence

def create_silence(duration_ms=5000):
    return AudioSegment.silent(duration=duration_ms)

def main():
    # Load tasks from JSON
    with open("tasks.json", "r") as f:
        tasks = json.load(f)

    final_audio = AudioSegment.silent(duration=0)
    
    one_minute_brown = generate_deep_layered_brown_noise(duration_ms=60000)
    
    for i, task in enumerate(tasks):
        task_name = task["name"]
        task_duration_minutes = task["duration_minutes"]
        
        introduction_text = f"{task_name} - {task_duration_minutes} minutes"
        tts_intro = text_to_speech(introduction_text)
        
        buffer_brown = one_minute_brown[: int(tts_intro.duration_seconds * 1000)]
        segment_introduction = buffer_brown.overlay(tts_intro)
        final_audio += segment_introduction
        
        for minute in range(task_duration_minutes):
            minute_segment = one_minute_brown
            
            # We only speak the reminder every 2 minutes (and skip minute 0 & final minute)
            # The final minute does the 10-second countdown, so skip the normal reminder there as well.
            if (minute != 0) and (minute != task_duration_minutes - 1) and (minute % 2 == 0):
                minutes_left = task_duration_minutes - minute
                reminder_text = f"{task_name}, {minutes_left} minutes left"
                tts_reminder = text_to_speech(reminder_text)
                minute_segment = minute_segment.overlay(tts_reminder, position=3000)
            
            # Final minute countdown
            if minute == task_duration_minutes - 1:
                countdown_words = [
                    "ten", "nine", "eight", "seven", "six",
                    "five", "four", "three", "two", "one"
                ]
                for idx, word in enumerate(countdown_words):
                    position_ms = 50000 + (idx * 1000)
                    tts_countdown = text_to_speech(word)
                    minute_segment = minute_segment.overlay(tts_countdown, position=position_ms)
            
            final_audio += minute_segment
            
            # One minute before next task => "coming up next, XYZ - N minutes"
            if (minute == task_duration_minutes - 2) and (i < len(tasks) - 1):
                next_task_name = tasks[i + 1]["name"]
                next_task_duration = tasks[i + 1]["duration_minutes"]
                coming_up_text = f"Coming up next, {next_task_name} - {next_task_duration} minutes."
                tts_coming_up = text_to_speech(coming_up_text)
                final_audio = final_audio.overlay(
                    tts_coming_up,
                    position=(len(final_audio) - tts_coming_up.duration_seconds * 1000)
                )
        
        # End of task
        celebration_sequence = generate_celebratory_sequence()
        final_audio += celebration_sequence
        final_audio += create_silence(duration_ms=5000)
    
    # Use Toronto time zone
    toronto_tz = pytz.timezone("America/Toronto")
    now_toronto = datetime.now(toronto_tz)
    timestamp = now_toronto.strftime("%Y%m%d_%H_%M_%S")

    # Ensure the 'dist' directory exists
    output_folder = "focus_box_dist"
    os.makedirs(output_folder, exist_ok=True)

    # Construct the filename inside 'dist'
    output_filename = os.path.join(output_folder, f"focus_box_{timestamp}.mp3")

    # Export the audio file
    final_audio.export(output_filename, format="mp3")
    print(f"Successfully generated {output_filename}")

if __name__ == "__main__":
    main()

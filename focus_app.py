import os
import json
import math
import numpy as np
from pydub import AudioSegment
from pydub.generators import Sine
from gtts import gTTS

# -----------------------------
# Utility Functions
# -----------------------------

def generate_binaural_beat(duration_ms=60000, base_freq=220, beat_freq=40):
    """
    Generate a stereo audio segment containing a binaural beat.
    
    :param duration_ms: Duration of the audio in milliseconds
    :param base_freq: Base frequency for the left channel
    :param beat_freq: Frequency difference for the right channel
    :return: pydub.AudioSegment (stereo)
    """
    # Left channel frequency is base_freq
    left_freq = base_freq
    # Right channel frequency is base_freq - beat_freq (to get a 40 Hz difference)
    right_freq = base_freq - beat_freq
    
    # Generate left channel
    left = Sine(left_freq).to_audio_segment(duration=duration_ms).apply_gain(-10.0)
    # Generate right channel
    right = Sine(right_freq).to_audio_segment(duration=duration_ms).apply_gain(-10.0)
    
    # Make the final stereo track
    stereo_segment = AudioSegment.from_mono_audiosegments(left, right)
    return stereo_segment

def text_to_speech(text, lang="en", slow=False):
    """
    Convert text to speech using gTTS.
    
    :param text: String to speak
    :param lang: Language code
    :param slow: Boolean for slow speech
    :return: pydub.AudioSegment
    """
    tts = gTTS(text=text, lang=lang, slow=slow, tld="com")
    # Save to a temporary file
    tts.save("temp_tts.mp3")
    spoken_audio = AudioSegment.from_file("temp_tts.mp3", format="mp3")
    os.remove("temp_tts.mp3")
    return spoken_audio

def generate_soft_tone(duration_ms=1000, freq=440):
    """
    Generate a soft tone of a given frequency and duration.
    
    :param duration_ms: Duration in milliseconds
    :param freq: Frequency in Hz
    :return: pydub.AudioSegment
    """
    tone = Sine(freq).to_audio_segment(duration=duration_ms).apply_gain(-15.0)
    return tone

def create_silence(duration_ms=5000):
    """
    Create silence for the given duration using pydub.
    """
    return AudioSegment.silent(duration=duration_ms)


# -----------------------------
# Main Application
# -----------------------------

def main():
    # Load tasks from JSON
    with open("tasks.json", "r") as f:
        tasks = json.load(f)
    
    # Total audio track to be built
    final_audio = AudioSegment.silent(duration=0)  # start with empty
    
    # This will be our background binaural beat chunk for 1 minute (60000 ms).
    # We'll layer it (overlay) with announcements and tones for each minute needed.
    one_minute_binaural = generate_binaural_beat(duration_ms=60000)
    
    # Loop over tasks
    for i, task in enumerate(tasks):
        task_name = task["name"]
        task_duration_minutes = task["duration_minutes"]
        
        # 1) Introduce the task
        introduction_text = f"{task_name} - {task_duration_minutes} minutes"
        tts_intro = text_to_speech(introduction_text)
        
        # 2) Append introduction to final audio (over a minute of binaural or at least some background)
        #    We'll fade in the background if you like, but let's keep it simple.
        buffer_binaural = one_minute_binaural[:tts_intro.duration_seconds * 1000]
        segment_introduction = buffer_binaural.overlay(tts_intro)
        final_audio += segment_introduction
        
        # 3) For each minute of the task
        for minute in range(task_duration_minutes):
            # Create a 1-minute segment of binaural
            minute_segment = one_minute_binaural
            # If it's not the final minute, we do a voice reminder in the overlay
            if minute < task_duration_minutes:
                reminder_text = f"{task_name}"
                tts_reminder = text_to_speech(reminder_text)
                # Overlay the reminder near the beginning of the minute
                # (for example, at 3 seconds into the minute)
                minute_segment = minute_segment.overlay(tts_reminder, position=3000)
            
            final_audio += minute_segment
            
            # One minute before next task => "coming up next, XYZ - N minutes"
            # This happens if we are at the second to last minute of the current task
            # and there IS a next task
            if (minute == task_duration_minutes - 2) and (i < len(tasks) - 1):
                next_task_name = tasks[i + 1]["name"]
                next_task_duration = tasks[i + 1]["duration_minutes"]
                coming_up_text = f"Coming up next, {next_task_name} - {next_task_duration} minutes."
                tts_coming_up = text_to_speech(coming_up_text)
                # Overlay on the next 1-minute segment or the remaining portion
                final_audio = final_audio.overlay(tts_coming_up, position=(len(final_audio) - tts_coming_up.duration_seconds * 1000))
        
        # 4) End of task soft tone and 5 second buffer
        soft_tone = generate_soft_tone(duration_ms=1000, freq=440)
        final_audio += soft_tone
        final_audio += create_silence(duration_ms=5000)
    
    # Export the final audio
    final_audio.export("focus_output.mp3", format="mp3")
    print("Successfully generated focus_output.mp3")


if __name__ == "__main__":
    main()

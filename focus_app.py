import os
import json
import math
import numpy as np
from datetime import datetime
from pydub import AudioSegment
from pydub.generators import Sine
from gtts import gTTS

def generate_binaural_beat(duration_ms=60000, base_freq=220, beat_freq=40):
    """
    Generate a stereo audio segment containing a binaural beat.
    
    :param duration_ms: Duration of the audio in milliseconds
    :param base_freq: Base frequency for the left channel
    :param beat_freq: Frequency difference for the right channel
    :return: pydub.AudioSegment (stereo)
    """
    left_freq = base_freq
    right_freq = base_freq - beat_freq
    
    left = Sine(left_freq).to_audio_segment(duration=duration_ms).apply_gain(-10.0)
    right = Sine(right_freq).to_audio_segment(duration=duration_ms).apply_gain(-10.0)
    
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

def main():
    # Load tasks from JSON
    with open("tasks.json", "r") as f:
        tasks = json.load(f)

    # Start building the final audio track
    final_audio = AudioSegment.silent(duration=0)
    
    # Generate a 1-minute binaural beat chunk for reuse
    one_minute_binaural = generate_binaural_beat(duration_ms=60000)
    
    for i, task in enumerate(tasks):
        task_name = task["name"]
        task_duration_minutes = task["duration_minutes"]
        
        # 1) Introduce the task
        introduction_text = f"{task_name} - {task_duration_minutes} minutes"
        tts_intro = text_to_speech(introduction_text)
        
        # Overlay TTS on a slice of the binaural track
        buffer_binaural = one_minute_binaural[:tts_intro.duration_seconds * 1000]
        segment_introduction = buffer_binaural.overlay(tts_intro)
        final_audio += segment_introduction
        
        # 2) Handle each minute of the task
        for minute in range(task_duration_minutes):
            # Copy 1-minute binaural
            minute_segment = one_minute_binaural
            
            # Create the reminder overlay
            # "Meditation, 3 minutes left" if 3 minutes remain in the current task
            minutes_left = task_duration_minutes - minute
            reminder_text = f"{task_name}, {minutes_left} minutes left"
            tts_reminder = text_to_speech(reminder_text)
            
            # Overlay the reminder a few seconds in
            minute_segment = minute_segment.overlay(tts_reminder, position=3000)
            
            final_audio += minute_segment
            
            # One minute before next task => "coming up next: XYZ - N minutes"
            # if there's a next task
            if (minute == task_duration_minutes - 2) and (i < len(tasks) - 1):
                next_task_name = tasks[i + 1]["name"]
                next_task_duration = tasks[i + 1]["duration_minutes"]
                coming_up_text = f"Coming up next, {next_task_name} - {next_task_duration} minutes."
                tts_coming_up = text_to_speech(coming_up_text)
                # Overlay near the end of the final_audio
                final_audio = final_audio.overlay(
                    tts_coming_up,
                    position=(len(final_audio) - tts_coming_up.duration_seconds * 1000)
                )
        
        # 3) End of task: soft tone + 5 seconds silence
        soft_tone = generate_soft_tone(duration_ms=1000, freq=440)
        final_audio += soft_tone
        final_audio += create_silence(duration_ms=5000)
    
    # 4) Export the final audio with timestamped filename
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H_%M_%S")
    output_filename = f"focus_box_{timestamp}.mp3"
    final_audio.export(output_filename, format="mp3")
    print(f"Successfully generated {output_filename}")

if __name__ == "__main__":
    main()

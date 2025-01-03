import os
import json
import random
import numpy as np
from datetime import datetime
from pydub import AudioSegment
from pydub.generators import Sine
from pydub.effects import low_pass_filter
from gtts import gTTS

def generate_deep_layered_brown_noise(duration_ms=60000, sample_rate=44100, layer_count=3):
    """
    Generate a deeper, layered brown noise by:
      1) Generating multiple layers of brown noise
      2) Overlaying them
      3) Applying a low-pass filter
    """
    def single_brown_noise(duration_ms, sample_rate):
        """
        Generate one layer of brown noise approximated by
        cumulatively integrating white noise. Returns a stereo segment.
        """
        num_samples = int(sample_rate * (duration_ms / 1000.0))
        
        brown_signal = np.zeros(num_samples, dtype=np.float64)
        last_out = 0.0
        
        for i in range(num_samples):
            white = random.uniform(-1.0, 1.0)
            brown_signal[i] = (last_out + (0.02 * white)) / 1.02
            last_out = brown_signal[i]
            # Optional deeper emphasis:
            brown_signal[i] *= 3.5
        
        brown_int16 = np.int16(brown_signal * 32767)
        
        # Create a mono pydub AudioSegment
        brown_audio_mono = AudioSegment(
            data=brown_int16.tobytes(),
            sample_width=2,  # 16 bits
            frame_rate=sample_rate,
            channels=1
        )
        
        # Convert to stereo by duplicating the mono channel
        brown_audio_stereo = AudioSegment.from_mono_audiosegments(
            brown_audio_mono, brown_audio_mono
        )
        
        # Reduce volume to avoid clipping when layers are stacked
        brown_audio_stereo = brown_audio_stereo.apply_gain(-10.0)
        return brown_audio_stereo

    # Overlay multiple brown noise layers
    layered_noise = None
    for _ in range(layer_count):
        layer = single_brown_noise(duration_ms, sample_rate)
        if layered_noise is None:
            layered_noise = layer
        else:
            layered_noise = layered_noise.overlay(layer)
    
    # Apply a low-pass filter to deepen the tone
    deep_brown_noise = low_pass_filter(layered_noise, cutoff=500)
    return deep_brown_noise

def text_to_speech(text, lang="en", slow=False):
    """
    Convert text to speech using gTTS.
    """
    tts = gTTS(text=text, lang=lang, slow=slow, tld="com")
    tts.save("temp_tts.mp3")
    spoken_audio = AudioSegment.from_file("temp_tts.mp3", format="mp3")
    os.remove("temp_tts.mp3")
    return spoken_audio

def generate_soft_tone(duration_ms=1000, freq=440):
    """
    Generate a soft tone of a given frequency and duration.
    """
    tone = Sine(freq).to_audio_segment(duration=duration_ms).apply_gain(-15.0)
    return tone

def create_silence(duration_ms=5000):
    """
    Create silence for the given duration.
    """
    return AudioSegment.silent(duration=duration_ms)

def main():
    # Load tasks from JSON
    with open("tasks.json", "r") as f:
        tasks = json.load(f)

    # Start building the final audio track
    final_audio = AudioSegment.silent(duration=0)
    
    # Generate 1 minute of deeper, layered brown noise
    one_minute_brown = generate_deep_layered_brown_noise(duration_ms=60000)
    
    for i, task in enumerate(tasks):
        task_name = task["name"]
        task_duration_minutes = task["duration_minutes"]
        
        # 1) Introduce the task
        introduction_text = f"{task_name} - {task_duration_minutes} minutes"
        tts_intro = text_to_speech(introduction_text)
        
        # Overlay TTS on a slice of the brown noise
        buffer_brown = one_minute_brown[: int(tts_intro.duration_seconds * 1000)]
        segment_introduction = buffer_brown.overlay(tts_intro)
        final_audio += segment_introduction
        
        # 2) Handle each minute of the task
        for minute in range(task_duration_minutes):
            # Copy the 1-minute brown noise segment
            minute_segment = one_minute_brown
            
            # "TaskName, X minutes left"
            minutes_left = task_duration_minutes - minute
            reminder_text = f"{task_name}, {minutes_left} minutes left"
            tts_reminder = text_to_speech(reminder_text)
            
            # Overlay the reminder at 3 seconds
            minute_segment = minute_segment.overlay(tts_reminder, position=3000)
            
            # If this is the final minute, overlay a last 10-second countdown
            if minute == task_duration_minutes - 1:
                # Create the countdown for "ten" down to "one"
                countdown_words = [
                    "ten", "nine", "eight", "seven", "six",
                    "five", "four", "three", "two", "one"
                ]
                # Each word goes from second 50 to 59
                for idx, word in enumerate(countdown_words):
                    position_ms = 50000 + (idx * 1000)  # 50s, 51s, ..., 59s
                    tts_countdown = text_to_speech(word)
                    minute_segment = minute_segment.overlay(tts_countdown, position=position_ms)
            
            # Append this finished minute to final_audio
            final_audio += minute_segment
            
            # One minute before next task => "coming up next, XYZ - N minutes"
            # if there is a next task
            if (minute == task_duration_minutes - 2) and (i < len(tasks) - 1):
                next_task_name = tasks[i + 1]["name"]
                next_task_duration = tasks[i + 1]["duration_minutes"]
                coming_up_text = f"Coming up next, {next_task_name} - {next_task_duration} minutes."
                tts_coming_up = text_to_speech(coming_up_text)
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

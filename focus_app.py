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
    
    :param duration_ms: Duration of the audio in milliseconds
    :param sample_rate: Sample rate in Hz (44100 is typical CD-quality)
    :param layer_count: Number of brown noise layers to overlay
    :return: pydub.AudioSegment (stereo) with a low-pass filter applied
    """
    
    def single_brown_noise(duration_ms, sample_rate):
        """
        Generate a single layer of brown noise approximated by
        cumulatively integrating white noise. Returns a stereo segment.
        """
        num_samples = int(sample_rate * (duration_ms / 1000.0))
        
        # Brown noise array
        brown_signal = np.zeros(num_samples, dtype=np.float64)
        last_out = 0.0
        
        # Generate brown noise by integrating white noise
        for i in range(num_samples):
            white = random.uniform(-1.0, 1.0)
            brown_signal[i] = (last_out + (0.02 * white)) / 1.02
            last_out = brown_signal[i]
            # Optional deeper emphasis:
            brown_signal[i] *= 3.5
        
        # Convert from -1..1 to int16
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
        
        # Reduce overall volume to avoid clipping when layers are stacked
        brown_audio_stereo = brown_audio_stereo.apply_gain(-10.0)
        return brown_audio_stereo

    # Generate and overlay multiple layers
    layered_noise = None
    for _ in range(layer_count):
        layer = single_brown_noise(duration_ms, sample_rate)
        if layered_noise is None:
            layered_noise = layer
        else:
            # Overlay the new layer on top of the existing
            layered_noise = layered_noise.overlay(layer)
    
    # Apply a low-pass filter to deepen the tone
    # Lower cutoff => more bass emphasis
    # Try values between 200-800 Hz; adjust to taste
    deep_brown_noise = low_pass_filter(layered_noise, cutoff=500)
    
    return deep_brown_noise

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
    
    :param duration_ms: Duration in milliseconds
    :return: pydub.AudioSegment
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
            minute_segment = one_minute_brown
            
            # "Meditation, 3 minutes left"
            minutes_left = task_duration_minutes - minute
            reminder_text = f"{task_name}, {minutes_left} minutes left"
            tts_reminder = text_to_speech(reminder_text)
            
            # Overlay the reminder a few seconds in
            minute_segment = minute_segment.overlay(tts_reminder, position=3000)
            
            final_audio += minute_segment
            
            # One minute before next task => "coming up next, XYZ - N minutes."
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

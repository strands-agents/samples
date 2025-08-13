"""
Audio recording utilities for the LlamaCpp tutorial.

Provides audio recording and speech transcription functionality
for multimodal AI applications.
"""

import os
import base64
import tempfile
import threading
import time
from typing import Optional

import numpy as np
import sounddevice as sd
import soundfile as sf
import ipywidgets as widgets
from IPython.display import HTML, display

from strands import Agent
from strands.models.llamacpp import LlamaCppModel


class AudioRecorder:
    """Audio recorder for speech capture and processing."""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.recording: Optional[np.ndarray] = None
        self.is_recording = False
        
    def record(self, duration: int = 5) -> np.ndarray:
        """Record audio for specified duration."""
        self.recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        return self.recording
    
    def get_audio_bytes(self) -> bytes:
        """Get audio data as bytes for SDK."""
        if self.recording is None:
            raise ValueError("No recording available")
            
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            sf.write(tmp_file.name, self.recording, self.sample_rate, format='WAV')
            tmp_filename = tmp_file.name
        
        with open(tmp_filename, 'rb') as f:
            audio_bytes = f.read()
        
        os.unlink(tmp_filename)
        return audio_bytes
    
    def play(self) -> None:
        """Play the recorded audio."""
        if self.recording is None:
            raise ValueError("No recording available")
        sd.play(self.recording, self.sample_rate)
        sd.wait()


# Global widget cache to prevent duplication
_audio_interface_cache = {}

def create_audio_interface(recorder: AudioRecorder, base_url: str = "http://localhost:8080") -> dict:
    """
    Create an audio recording interface for speech transcription.
    
    Args:
        recorder: AudioRecorder instance
        base_url: LlamaCpp server URL
        
    Returns:
        Dictionary containing interface widgets and handlers
    """
    
    # Use cached widgets if they exist to prevent duplication
    cache_key = id(recorder)
    if cache_key in _audio_interface_cache:
        cached = _audio_interface_cache[cache_key]
        # Clear existing outputs
        cached['widgets']['recording_output'].clear_output()
        cached['widgets']['analysis_output'].clear_output()
        cached['widgets']['status_label'].value = "Ready to record"
        cached['widgets']['play_button'].disabled = True
        cached['widgets']['analyze_button'].disabled = True
        cached['widgets']['progress_bar'].value = 0
        cached['widgets']['progress_bar'].layout.visibility = 'hidden'
        return cached
    
    # Basic controls
    duration_slider = widgets.IntSlider(
        value=5,
        min=1,
        max=15,
        step=1,
        description='Duration (sec):',
        style={'description_width': '100px'}
    )

    record_button = widgets.Button(
        description='Record',
        button_style='info',
        layout=widgets.Layout(width='80px')
    )

    play_button = widgets.Button(
        description='Play',
        button_style='success',
        disabled=True,
        layout=widgets.Layout(width='80px')
    )

    analyze_button = widgets.Button(
        description='Transcribe',
        button_style='primary',
        disabled=True,
        layout=widgets.Layout(width='90px')
    )

    clear_button = widgets.Button(
        description='Clear',
        button_style='warning',
        layout=widgets.Layout(width='80px')
    )

    # Status label
    status_label = widgets.Label(value="Ready to record")
    
    # Output areas
    recording_output = widgets.Output(layout=widgets.Layout(height='50px'))
    analysis_output = widgets.Output(layout=widgets.Layout(height='200px', overflow='auto'))
    
    # Progress bar
    progress_bar = widgets.IntProgress(
        value=0,
        min=0,
        max=100,
        description='',
        bar_style='info',
        layout=widgets.Layout(width='100%', visibility='hidden')
    )

    def on_record_click(b):
        """Handle record button click."""
        recording_output.clear_output(wait=True)
        with recording_output:
            status_label.value = f"Recording for {duration_slider.value} seconds..."
            progress_bar.layout.visibility = 'visible'
            progress_bar.value = 0
            
            def update_progress():
                for i in range(duration_slider.value * 10):
                    time.sleep(0.1)
                    progress_bar.value = (i + 1) / (duration_slider.value * 10) * 100
            
            progress_thread = threading.Thread(target=update_progress)
            progress_thread.start()
            
            recorder.record(duration_slider.value)
            
            progress_thread.join()
            progress_bar.layout.visibility = 'hidden'
            
            status_label.value = "Recording ready"
            play_button.disabled = False
            analyze_button.disabled = False
            
    def on_play_click(b):
        """Handle play button click."""
        recording_output.clear_output(wait=True)
        with recording_output:
            status_label.value = "Playing audio..."
            recorder.play()
            status_label.value = "Recording ready"
            
    def on_analyze_click(b):
        """Handle analyze button click."""
        analysis_output.clear_output(wait=True)
        
        status_label.value = "Transcribing audio..."
        progress_bar.layout.visibility = 'visible'
        progress_bar.value = 20
        
        try:
            # Get audio bytes
            audio_bytes = recorder.get_audio_bytes()
            progress_bar.value = 40
            
            # Create LlamaCpp model
            clean_base_url = base_url.rstrip('/').replace('/v1', '')
            model = LlamaCppModel(
                base_url=clean_base_url,
                params={"temperature": 0.7, "max_tokens": 300}
            )
            agent = Agent(model=model)
            progress_bar.value = 60
            
            # Create message with audio content
            message_content = [
                {
                    "audio": {
                        "source": {"bytes": audio_bytes},
                        "format": "wav"
                    }
                },
                {
                    "text": "Please transcribe exactly what was said in this audio recording. If the speech is in a language other than English, first provide the exact transcription in the original language, then provide an English translation. Format your response as:\n1. Original transcription: [exact words spoken]\n2. Language detected: [language name]\n3. English translation: [translation if needed, or 'Already in English']"
                }
            ]
            
            progress_bar.value = 80
            response = agent(message_content)
            progress_bar.value = 100
            
            # Extract and display response
            with analysis_output:
                if hasattr(response, 'message') and 'content' in response.message:
                    full_response = ""
                    for content_block in response.message['content']:
                        if 'text' in content_block:
                            full_response += content_block['text']
                    display(HTML(f'<pre style="white-space: pre-wrap; padding: 10px; background: #f5f5f5; border-radius: 5px;">{full_response}</pre>'))
                else:
                    display(HTML(f'<pre style="white-space: pre-wrap; padding: 10px; background: #f5f5f5; border-radius: 5px;">{str(response)}</pre>'))
            
            status_label.value = "Transcription complete"
            
        except Exception as e:
            with analysis_output:
                display(HTML(f'<div style="color: red; padding: 10px;">Error: {str(e)}</div>'))
            status_label.value = "Error occurred"
        finally:
            progress_bar.layout.visibility = 'hidden'

    def on_clear_click(b):
        """Handle clear button click."""
        recording_output.clear_output(wait=True)
        analysis_output.clear_output(wait=True)
        progress_bar.layout.visibility = 'hidden'
        progress_bar.value = 0
        status_label.value = "Ready to record"
        play_button.disabled = True
        analyze_button.disabled = True

    # Register event handlers
    record_button.on_click(on_record_click)
    play_button.on_click(on_play_click)
    analyze_button.on_click(on_analyze_click)
    clear_button.on_click(on_clear_click)

    # Create interface dictionary
    interface = {
        'widgets': {
            'duration_slider': duration_slider,
            'record_button': record_button,
            'play_button': play_button,
            'analyze_button': analyze_button,
            'clear_button': clear_button,
            'status_label': status_label,
            'progress_bar': progress_bar,
            'recording_output': recording_output,
            'analysis_output': analysis_output,
        },
        'handlers': {
            'on_record_click': on_record_click,
            'on_play_click': on_play_click,
            'on_analyze_click': on_analyze_click,
            'on_clear_click': on_clear_click,
        }
    }
    
    # Cache the interface
    _audio_interface_cache[cache_key] = interface
    
    return interface


def clear_audio_interface_cache():
    """Clear the audio interface cache to force recreation of widgets."""
    global _audio_interface_cache
    _audio_interface_cache.clear()


def display_audio_interface(interface_components: dict) -> None:
    """
    Display the audio recording interface.
    
    Args:
        interface_components: Dictionary from create_audio_interface
    """
    widgets_dict = interface_components['widgets']
    
    # Clear any existing outputs first
    from IPython.display import clear_output
    clear_output(wait=True)
    
    # Header
    display(HTML('<h4>Speech Recognition & Translation</h4>'))

    # Controls in a simple layout
    display(widgets.HBox([
        widgets.VBox([
            widgets_dict['duration_slider'],
            widgets_dict['status_label']
        ]),
        widgets.VBox([
            widgets.HBox([
                widgets_dict['record_button'], 
                widgets_dict['play_button'], 
                widgets_dict['analyze_button'], 
                widgets_dict['clear_button']
            ])
        ])
    ]))
    
    display(widgets_dict['progress_bar'])
    
    # Output sections
    display(HTML('<h4>Recording Status</h4>'))
    display(widgets_dict['recording_output'])
    
    display(HTML('<h4>Analysis Results</h4>'))
    display(widgets_dict['analysis_output'])
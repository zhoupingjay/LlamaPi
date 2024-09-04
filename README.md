# LlamaPi Robot - Raspberry Pi Voice Chatbot backed by Llama-3.1 8B, with Robot Arm gestures

## Intro

An initial attempt for exploring the possibilities of **LLM + Robotics**,
this is a voice chatbot running on Raspberry Pi 5 backed by the latest Llama-3.1 8B model,
and with **robot arm gestures**.
It is somewhat similar to [my other project](https://github.com/zhoupingjay/llm_voice_chatbot_rpi),
but with multiple major enhancements:
- Use the latest Llama-3.1 8B model (instead of TinyLlama).
- Use faster_whisper for better ASR performance.
- A simple GUI (TkInter-based) showing the conversation and status of the push button.
- In addition to voice interaction, the chatbot can also respond with simple **robot arm gestures**
  based on the context of the conversation.

Also, everything runs locally!

NOTE: This project is still very preliminary and subject to major refactor/enhancements.

## Demo

To be added...

## Dependencies

Hardware:
- Raspberry Pi 5, 8GB RAM
- Toy robot arm using PWM servos
- PWM servo hat for Raspberry Pi ([example](https://www.waveshare.net/wiki/Servo_Driver_HAT))
- Push button (similar to [my other project](https://github.com/zhoupingjay/llm_voice_chatbot_rpi))

Software:
- Raspbian OS (Debian 12) desktop

## Installation

Create a virtual environment.
```
mkdir ~/.virtualenvs/
python3 -m venv ~/.virtualenvs/llamapi
source ~/.virtualenvs/llamapi/bin/activate
```

Install system packages:
```
sudo apt install portaudio19-dev
sudo apt install libopenblas-dev libopenblas-pthread-dev libopenblas-openmp-dev libopenblas0 libopenblas0-pthread libopenblas0-openmp
sudo apt install libopenblas64-0 libopenblas64-dev libopenblas64-pthread-dev libopenblas64-openmp-dev
sudo apt install ccache build-essential cmake
```

Install Python modules:
```
pip install pyaudio wave soundfile
pip install faster_whisper numpy

# RPi.GPIO doesn't work, use rpi-lgpio as a drop-in replacement
pip uninstall RPi.GPIO
pip install rpi-lgpio

pip install opencc
pip install smbus

# For use with OpenBLAS:
CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS" pip install llama-cpp-python
CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS" pip install 'llama-cpp-python[server]'
pip install openai
```

Checkout the LlamaPi code:
```
git clone https://github.com/zhoupingjay/LlamaPi.git
```

Language model ([Llama-3.1 8B Instruct](https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct)):
- Quantize the model to 4-bit so it can fit in the 8GB RAM on Raspberry Pi.
  You may use the quantization tool from [llama.cpp](https://github.com/ggerganov/llama.cpp),
  or use the [GGUF-my-repo](https://huggingface.co/spaces/ggml-org/gguf-my-repo) space on Hugging Face.
- Create a `llm` folder under `LlamaPi`, and download the 4-bit quantized model (`.gguf` file) under this folder.
  E.g. `llm/meta-llama-3.1-8b-instruct-q4_k_m.gguf`.

ASR model:
- Use [faster_whisper](https://github.com/SYSTRAN/faster-whisper) installed from pip.
  It will download the ASR model to local on the first run.

TTS model:
- Use [piper](https://github.com/rhasspy/piper) for TTS.
- Create a `tts` folder under `LlamaPi`, download and extract piper in this folder.
```
cd tts
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz
tar zxf piper_arm64.tar.gz
```
- Download voice file: https://github.com/rhasspy/piper/blob/master/VOICES.md
  You need the `.onnx` file and `.json` file for each voice.
  For example: `en_US-amy-medium.onnx` and `en_US-amy-medium.onnx.json`.
  Create a `voices` folder under `LlamaPi/tts`, and put voice files under this folder.

The directory structure should look like this:
```
LlamaPi
├── llm
|   └── meta-llama-3.1-8b-instruct-q4_k_m.gguf
└── tts
    ├── piper
    |   └── (piper binaries)
    └── voices
        └── (voice files)
```

## Robot Arm

To be added

## Usage

In your virtual environment, run the `LlamaPi.py` script:
```
python LlamaPi.py
```

You'll see a window with big blue button and a text box showing the conversation.

The robot uses a "push-to-talk" mode for interaction:
Hold the button, talk, and release the button after you finish.
The robot will respond with text and voice.

The robot will also generate simple robot arm commands based on
the context of your conversation:
- If you say hello to the robot, it will generate a `$greet` command;
- If you sounds happy, it will generate a `$smile` command;
- If you sounds negative, it will generate a `$pat` command.

These simple commands will result in different gestures from the robot arm.

## Future Works

This is still WIP, lots of works needed...

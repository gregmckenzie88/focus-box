# Focus Box Prompt

This project generates an audio track designed to help keep you on task. It uses:

- **Binaural beats** at 40 Hz difference.
- **Voice prompts** for introducing tasks, minute-by-minute reminders, and upcoming tasks.
- **Break tone** at the end of each task.

## Problem Statement

While working on a computer, especially in a busy environment, it is very easy to become distracted or succumb to the impulse to multitask. This can get in the way of true productivity and can have a negative impact on the quality of your work.

By having the user declare a list of tasks they would like to focus on, set a time limit on it, provide the user with relaxing "brown noise" in the background, as well as a reminder every minute of what it is they should be focusing on, they can increase their productivity and work with an increased level of focus.

## Contents

1. [Requirements](#requirements)
2. [Setup and Installation](#setup-and-installation)
3. [Usage](#usage)
4. [Docker](#docker)

---

## Requirements

- Python 3.8 or above
- `ffmpeg` must be installed on your system (if you are not using Docker).
- The following Python dependencies:
  - `pydub==0.25.1`
  - `numpy==1.20.0`
  - `gTTS==2.2.3`
  - `pyspellchecker==0.7.2`
  - `pytz==2024.2`

## Setup and Installation

1. **Clone this repository** or download the files to your local machine:

   ```bash
   git clone https://github.com/gregmckenzie88/focus-box
   cd focus-box
   ```

2. **Install dependencies**:

   If you are running locally (not using Docker):

   ```bash
   pip install -r requirements.txt
   ```

   Ensure `ffmpeg` is installed on your system:

   - On macOS, use Homebrew: `brew install ffmpeg`
   - On Ubuntu: `sudo apt install ffmpeg`
   - On Windows, download and install it from [FFmpeg.org](https://ffmpeg.org/).

3. **Using Docker (if preferred)**:

   Ensure you have Docker Desktop installed on your system. If you do not, download it from [Docker Desktop](https://www.docker.com/products/docker-desktop/).

   Build the Docker image and run the container:

   ```bash
   docker build -t focus_box_image .
   docker run -v $(pwd):/app focus_box_image
   cp /Users/gregmckenzie/Desktop/repos/focus_box/focus_box_dist/*.mp3 /Users/gregmckenzie/Dropbox/__focus-vibe/
   ```

## Usage

After completing the installation, you can use the scripts included in this repository to generate audio tracks. See the scripts for specific usage instructions.

## Docker

If you prefer to run this project in a containerized environment, Docker is fully supported. Ensure Docker Desktop is installed on your machine ([download here](https://www.docker.com/products/docker-desktop)).

Run the following commands to set up and execute the Docker container:

```bash
docker build -t focus_box_image .
docker run -v $(pwd):/app focus_box_image
```

This setup ensures a consistent environment for running the project without the need to install Python dependencies or `ffmpeg` locally.

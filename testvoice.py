import subprocess

text = "Let's solve this equation step by step."

subprocess.run(
    ["piper", "--model", "en_US-lessac-medium.onnx", "--output_file", "voice.wav"],
    input=text.encode(),
    check=True,
)
print("Voice created: voice.wav")

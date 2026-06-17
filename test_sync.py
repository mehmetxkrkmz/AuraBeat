import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from src.core.downloader import Downloader

def callback(data):
    print("Progress:", data)

d = Downloader("./test_usb", progress_callback=callback)

url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
print("First download:")
res1 = d.download(url, fmt="audio", quality="128")
print("Result 1:", res1)

d2 = Downloader("./test_usb", progress_callback=callback)
print("Second download (should be skipped):")
res2 = d2.download(url, fmt="audio", quality="128")
print("Result 2:", res2)

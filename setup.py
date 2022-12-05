from setuptools import setup, find_packages


setup(
    name="video_sender",
    version="1.0",
    packages=['video_sender', 'video_sender.pyspin_camera', 'video_sender.uvc_camera'],
    scripts=['scripts/video-sender']
)

ffmpeg -f concat -safe 0 -i input.txt -c copy input_video.mp4

#ffmpeg -stream_loop -1 -i input_audio.mp3 -i input_video.mp4 -filter_complex "[0:a]volume=0.1[a];[1:a][a]amix=inputs=2:duration=first:dropout_transition=2[aout]" -map 1:v -map "[aout]" -c:v copy -c:a aac output.mp4

# Get the duration of the video in seconds
duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input_video.mp4)

# Calculate the start time of the fade effect
fade_start=$(bc <<< "$duration-2")

ffmpeg -stream_loop -1 -i input_audio.mp3 -i input_video.mp4 -filter_complex "[0:a]volume=0.2[a];[a]afade=t=out:st=$fade_start:d=2[a1];[1:a][a1]amix=inputs=2:duration=first:dropout_transition=2[aout]" -map 1:v -map "[aout]" -c:v copy -c:a aac output.mp4


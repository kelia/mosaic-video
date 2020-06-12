# mosaic-video

<p align="center">
  <img src="./mosaic-video.gif" alt="mosaic-video">
</p>


1. Create a bunch of videos you want to mosaic.
2. Save frames of video to folder
```
 ffmpeg -i PATH_TO_YOUR_VIDEO/video.mp4 -r 30/1 PATH_TO_YOUR_INPUT_DATA/input_videos/VIDEO_IDX/frame_%05d.png
```

3. Create cool visualization
```
python create_mosaic_video.py --n_stack=5 --num_frames=100 --wait_n_frames=10 --root_dir=example_input_data --output_width=1200 --output_height=720
```

4. Generate video from saved frames
```
ffmpeg -r 30/1 -i PATH_TO_THE_OUTPUT_DATA/out_frame_%05d.png  -vcodec mpeg4 -b:v 80000k PATH_TO_YOUR_FINAL_VIDEO/final_video.avi
```
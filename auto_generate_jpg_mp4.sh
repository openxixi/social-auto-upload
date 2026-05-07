#!/bin/bash

python add_date_to_image.py "./videos_pre/tmp.jpg" -o "./videos/tmp.jpg"
python ./auto_add_tail_to_videos.py ./videos_pre/tmp.mp4 -c ./videos/tmp.jpg -o ./videos/tmp.mp4
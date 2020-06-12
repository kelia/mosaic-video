import argparse
import os
import random
import time

import cv2
import numpy as np

from arrange_spiral import *

########################################################
# Define data root directory, find subdirectories
########################################################
parser = argparse.ArgumentParser(description='Create Multivideo')

parser.add_argument('--root_dir',
                    help='Path to data', required=True)
parser.add_argument('--num_frames',
                    help='Generate output sequence of N frames', required=True)
parser.add_argument('--wait_n_frames',
                    help='Wait N frames until zoom-out effect starts', required=True)
parser.add_argument('--n_stack',
                    help='How many frames to stack (will be applied for both axes)', required=True)
parser.add_argument('--output_width',
                    help='Width of output frames', required=True)
parser.add_argument('--output_height',
                    help='Height of output frames', required=True)

args = parser.parse_args()
root_dir = args.root_dir
des_num_frames = int(args.num_frames)
wait_for_n_frames = int(args.wait_n_frames)
n_stack = int(args.n_stack)

# input img dimensions
img_width = int(args.output_width)
img_height = int(args.output_height)

if n_stack % 2 == 0:
    n_stack += 1
    print("n_stack needs to be odd! Setting n_stack to %d" % (n_stack))

########################################################
# Define data root directory, find subdirectories
########################################################
output_dir = os.path.join(root_dir, "../output_video")
print("Creating multivideo in directory [%s]." % output_dir)
try:
    # Create target Directory
    os.mkdir(output_dir)
    print("Directory ", output_dir, " Created ")
except FileExistsError:
    print("Directory ", output_dir, " already exists")

list_subfolders_with_paths = [f.path for f in os.scandir(root_dir) if f.is_dir()]
print(list_subfolders_with_paths)
num_folders = len(list_subfolders_with_paths)
print("Directory contains %d folders to concatenate." % num_folders)

use_bold_trajectories = False

# randomize the ordering of the videos
number_list = list(range(0, n_stack ** 2))
random.shuffle(number_list)
number_list[0] = 0

# random offset for each video
random_offsets = np.random.randint(500, size=(n_stack ** 2))
random_offsets[0] = 0

for frame_idx in range(1, des_num_frames):
    start_main = time.time()
    print(frame_idx)
    # first version: linear scaling
    multiplicator = 0.0
    if frame_idx > wait_for_n_frames:
        # scale frame idx to [0, 1)
        frame_idx_scaled = (frame_idx - 1 - wait_for_n_frames) / (des_num_frames - 1 - wait_for_n_frames)
        # configure zoom-out effect --> choose 1 for linear zoom-out
        exponent = 3
        multiplicator = (n_stack - 1) / n_stack * frame_idx_scaled ** exponent
    multiplicator += 1.0 / n_stack
    # sanity check
    multiplicator = min(multiplicator, 1.0)
    print("multiplicator: %.6f" % multiplicator)

    # load corresponding frame from each folder
    frames = []
    out_dim = None

    scaling = int(n_stack * multiplicator)
    out_dim = (img_width, img_height)
    tile_size = (img_width // scaling, img_height // scaling)
    n_tiles_in_row = min(int(n_stack * multiplicator) + 2, n_stack)
    n_tiles_in_col = min(int(n_stack * multiplicator) + 2, n_stack)

    n_tiles_in_row = n_tiles_in_row + 1 if n_tiles_in_row % 2 == 0 else n_tiles_in_row
    n_tiles_in_col = n_tiles_in_col + 1 if n_tiles_in_col % 2 == 0 else n_tiles_in_col

    frame_concat = np.zeros((n_tiles_in_row * tile_size[1],
                             n_tiles_in_col * tile_size[0],
                             3))

    spiral_matrix_temp = spiral(n_tiles_in_row, n_tiles_in_col)
    spiral_matrix_temp = np.array(spiral_matrix_temp)

    # based on the multiplicator, we can compute how many frames we need to load
    # frames are loaded in row-major format, and placed afterwards
    for tile_idx in range(n_tiles_in_row * n_tiles_in_col):
        # lazy loading, load images only here
        # based on random rollout selection and random offset, load frame
        idx_subfolder = number_list[tile_idx] % len(list_subfolders_with_paths)
        chosen_folder = list_subfolders_with_paths[idx_subfolder]
        # get index of first frame
        file_list = sorted([name for name in os.listdir(chosen_folder) if
                            os.path.isfile(
                                os.path.join(chosen_folder, name)) and "frame" in name])
        index_first_frame = int(file_list[0][6:-4])
        # assemble filename
        num_images = len(file_list)
        num_images -= 2  # don't count the video file in the same folder
        adapted_frame_idx = (frame_idx + random_offsets[tile_idx]) % num_images + index_first_frame
        img_name = "frame_{:05d}.png".format(adapted_frame_idx)

        img_filename = os.path.join(chosen_folder, img_name)
        img = cv2.imread(img_filename)
        img = cv2.resize(img, tile_size, interpolation=cv2.INTER_AREA)

        index_tile = np.argwhere(spiral_matrix_temp == (tile_idx + 1))
        frame_concat[
        index_tile[0, 0] * tile_size[1]:(index_tile[0, 0] + 1) * tile_size[1],
        index_tile[0, 1] * tile_size[0]:(index_tile[0, 1] + 1) * tile_size[0], :] = img

    subset_row_start = int(frame_concat.shape[0] / 2 - multiplicator * n_stack * img.shape[0] / 2)
    subset_row_end = int(frame_concat.shape[0] / 2 + multiplicator * n_stack * img.shape[0] / 2)
    subset_col_start = int(frame_concat.shape[1] / 2 - multiplicator * n_stack * img.shape[1] / 2)
    subset_col_end = int(frame_concat.shape[1] / 2 + multiplicator * n_stack * img.shape[1] / 2)

    frame_subset = frame_concat[subset_row_start:subset_row_end,
                   subset_col_start:subset_col_end, :]

    # final resizing
    frame_out = cv2.resize(frame_subset, out_dim, interpolation=cv2.INTER_AREA)
    out_filename = os.path.join(root_dir, "../output_video/out_frame_{:05d}.png".format(frame_idx))
    print("Saving final frame to [%s]." % out_filename)
    cv2.imwrite(out_filename, frame_out)

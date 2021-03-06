import os
import sys
from time import sleep

import cv2
import numpy as np
import pandas as pd

column_headings = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

frame_trackbar = "frame"
speed_trackbar = "fps"

state_play = "play"
state_pause = "pause"
state_skip_fwd = "skip_fwd"
state_skip_fwd_big = "state_skip_fwd_big"
state_skip_back = "skip_back"
state_skip_back_big = "state_skip_back_big"
state_speed_increase = "speed_increase"
state_speed_decrease = "speed_decrease"
state_snapshot = "snapshot"
state_save_csv = "save_csv"
state_play_toggle = "play_toggle"
state_rotation_none = "state_rotation_none"
state_rotation_90 = "state_rotation_90"
state_rotation_180 = "state_rotation_180"
state_rotation_270 = "state_rotation_270"
state_exit = "exit"

windows_controls = "controls"


def main():
	if len(sys.argv) > 1:
		video = sys.argv[1]
		valid_file = is_valid_video(video)
	else:
		print("No video path argument provided")
		valid_file = False

	while not valid_file:
		video = input("video path: ")
		valid_file = is_valid_video(video)
		if not valid_file:
			print("Sorry that wasn't valid")

	print(split_path(video)[2])

	window_video = video

	fps_increment = 5
	big_skip = 5

	cv2.namedWindow(window_video, cv2.WINDOW_NORMAL)
	cv2.moveWindow(window_video, 500, 100)

	cv2.namedWindow(windows_controls)
	cv2.moveWindow(windows_controls, 100, 100)
	print("\nControls:", "\n")
	command_text_array = [
		"Space      Play/Pause",
		"Left/Right  Jump 1 frame",
		"Up/Down   Jump 5 frames",
		"+/-       Change FPS",
		"c           Capture frame",
		"s           Save csv of labels",
		"0-9        Toggle label 0-9",
		"a,s,d,f      0-270 degree rotation",
		"esc/q      Quit", ]
	help_text = "\n".join(command_text_array)
	print(help_text, "\n")

	font_size = 0.75
	height_factor = 40
	line_height = int(font_size * height_factor)
	width_factor = 20
	char_width = int(font_size * width_factor)

	controls_height = int(line_height * (len(command_text_array) + 0.5))
	controls_width = int(char_width * max([len(x) for x in command_text_array]))

	controls = np.zeros((controls_height, controls_width), np.uint8)

	y0, dy = line_height, line_height
	for frame_index_current, line in enumerate(help_text.split('\n')):
		y = y0 + frame_index_current * dy
		cv2.putText(controls, line, (int(line_height / 2), y), cv2.FONT_HERSHEY_SIMPLEX, font_size, 255)

	cap = cv2.VideoCapture(video)
	frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
	print("frame_count", frame_count)
	temp_im = cap.read()[1]
	cv2.resizeWindow(window_video, temp_im.shape[1] * 2, temp_im.shape[0] * 2)

	df = get_dataframe(video)

	print(df)

	frame_index_current = 0
	frame_index_previous = 0
	frame_rate = 30
	bFirstInitUi = False

	current_state = state_skip_fwd
	create_track_bar(window_video, frame_count, frame_rate)

	manual_rotation = "none"

	while True:
		cv2.imshow(windows_controls, controls)
		try:
			if current_state != state_pause or frame_index_previous != frame_index_current:
				while True:
					if frame_index_current >= frame_count:
						frame_index_current = 0
					elif frame_index_current < 0:
						frame_index_current = int(frame_count - 1)

					cv2.setTrackbarPos(frame_trackbar, window_video, frame_index_current)

					if frame_index_previous != frame_index_current - 1:
						cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index_current)
						print("seek to", frame_index_current)

					print('index', frame_index_current)
					ret, im = cap.read()
					if ret:
						break
					else:
						print("bad frame at", frame_index_current)
						if current_state == state_skip_back or current_state == state_skip_back_big:
							frame_index_current -= 1
						else:
							frame_index_current += 1

				original_image = im
				if manual_rotation != "none":
					im = cv2.rotate(im, manual_rotation)

				# cv2.putText(im, str(frame_index_current), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1)
				df_current_row = df.iloc[frame_index_current, :]
				df_string = ' '.join(str(int(d)) for d in df_current_row)
				print("df at", frame_index_current, "\n" + df_string)
				cv2.putText(im, ' '.join(str(int(d)) for d in column_headings), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
							0.75,
							(0, 255, 0),
							1)
				cv2.putText(im, df_string, (10, 60), cv2.FONT_HERSHEY_SIMPLEX,
							0.75,
							(0, 255, 0),
							1)

				cv2.imshow(window_video, im)
				if current_state != state_play:
					current_state = state_pause
				frame_index_previous = frame_index_current
				if not bFirstInitUi:
					bFirstInitUi = True

			state_previous = current_state
			current_state = {
				ord(' '): state_play_toggle,
				2555904: state_skip_fwd,
				2424832: state_skip_back,
				2490368: state_skip_fwd_big,
				2621440: state_skip_back_big,
				ord('+'): state_speed_increase, ord('='): state_speed_increase,
				ord('-'): state_speed_decrease, ord('_'): state_speed_decrease,
				ord('c'): state_snapshot, ord('C'): state_snapshot,
				ord('s'): state_save_csv, ord('s'): state_save_csv,
				ord('0'): "0", ord('1'): "1", ord('2'): "2", ord('3'): "3", ord('4'): "4", ord('5'): "5", ord('6'): "6",
				ord('7'): "7",
				ord('8'): "8", ord('9'): "9",
				ord('a'): state_rotation_none,
				ord('s'): state_rotation_90,
				ord('d'): state_rotation_180,
				ord('f'): state_rotation_270,
				-1: current_state,
				ord('q'): state_exit, ord('Q'): state_exit,
				27: state_exit
			}[cv2.waitKeyEx(10)]

			if current_state == state_play:
				frame_rate = cv2.getTrackbarPos(speed_trackbar, window_video)
				if frame_rate > 0:
					sleep(1.0 / frame_rate)
					frame_index_current += 1
				else:
					current_state = state_pause
				continue
			elif current_state == state_pause:
				frame_index_current = cv2.getTrackbarPos(frame_trackbar, window_video)
			elif current_state == state_exit:
				break
			elif current_state == state_skip_back:
				frame_index_current -= 1
			elif current_state == state_skip_fwd:
				frame_index_current += 1
			elif current_state == state_speed_decrease:
				frame_rate = max(frame_rate - fps_increment, 0)
				cv2.setTrackbarPos(speed_trackbar, window_video, frame_rate)
				current_state = state_play if (state_previous == state_play) else state_pause
			elif current_state == state_speed_increase:
				frame_rate = min(100, frame_rate + fps_increment)
				cv2.setTrackbarPos(speed_trackbar, window_video, frame_rate)
				current_state = state_play if (state_previous == state_play) else state_pause
			elif current_state == state_snapshot:
				cv2.putText(im, str(frame_index_current), (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1)
				snapshot_filename = strip_extension(video) + "_snapshot_" + str(
					frame_index_current).rjust(5, '0') + ".jpg"
				cv2.imwrite(snapshot_filename, im)
				print("frame", frame_index_current, "snapshot saved to", snapshot_filename)
			elif current_state == state_save_csv:
				save_csv(video, df)
			elif current_state == state_skip_fwd_big:
				frame_index_current += big_skip
			elif current_state == state_skip_back_big:
				frame_index_current -= big_skip
			elif current_state == state_play_toggle:
				current_state = state_pause if (state_previous == state_play) else state_play
			elif current_state in column_headings:
				df.iat[frame_index_current, int(current_state)] = not df.iloc[frame_index_current, int(current_state)]
				print("df at", frame_index_current, "update to",
					  "\n" + ' '.join(str(int(d)) for d in df.iloc[frame_index_current, :]))
				save_csv(video, df)
			elif current_state in {state_rotation_none, state_rotation_90, state_rotation_180, state_rotation_270}:
				if current_state == state_rotation_none:
					manual_rotation = "none"
				elif current_state == state_rotation_90:
					manual_rotation = cv2.ROTATE_90_CLOCKWISE
				elif current_state == state_rotation_180:
					manual_rotation = cv2.ROTATE_180
				elif current_state == state_rotation_270:
					manual_rotation = cv2.ROTATE_90_COUNTERCLOCKWISE

				rotate_window(window_video, original_image, manual_rotation)
				current_state = state_play if (state_previous == state_play) else state_pause

		except KeyError:
			print("Invalid Key was pressed")
	cv2.destroyAllWindows()


def create_track_bar(window_video="Video Player", frame_count=0, frame_rate=30):
	cv2.createTrackbar(frame_trackbar, window_video, 0, int(frame_count) - 1, on_change_do_nothing)
	cv2.setTrackbarPos(frame_trackbar, window_video, 0)

	cv2.createTrackbar(speed_trackbar, window_video, 1, 100, on_change_do_nothing)
	cv2.setTrackbarPos(speed_trackbar, window_video, frame_rate)


def process(im):
	return cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)


def save_csv(video, df):
	filename_csv = strip_extension(video) + ".csv"
	np.savetxt(filename_csv, df, delimiter=',')
	print("csv saved to", filename_csv)


def get_dataframe(video_file):
	filename_csv = video_file.split(".")[0] + ".csv"
	if os.path.exists(filename_csv):
		return pd.read_csv(filename_csv, header=None, index_col=None)
	else:
		return pd.DataFrame(
			False,
			index=range(
				0,
				int(
					cv2.VideoCapture(video_file)
						.get(cv2.CAP_PROP_FRAME_COUNT)
				)
			),
			columns=column_headings
		)


def strip_extension(file):
	temp_file = file.replace("\\", "/")
	path = file[:temp_file.rfind(".")]
	return path


def split_path(file):
	temp_file = file.replace("\\", "/")
	path = file[:temp_file.rfind("/")]
	filename = file[temp_file.rfind("/") + 1:temp_file.rfind(".")]
	extension = file[temp_file.rfind(".") + 1:]
	print(extension)
	return path, filename, extension


def is_valid_video(file):
	if os.path.exists(file) and split_path(file)[2] in {"mp4", "avi", "3gp"}:
		return True
	else:
		print("Please enter an absolute or relative video path")
		print("(mp4, avi or 3gp)")
		return False


def on_change_do_nothing(x):
	pass


def rotate_window(window_name, frame, rotation):
	if not rotation == "none":
		frame = cv2.rotate(frame, rotation)

	cv2.resizeWindow(window_name, frame.shape[1] * 2, frame.shape[0] * 2)

	cv2.imshow(window_name, frame)


main()

import json
import sys
import string
import os
import argparse
import vlc
from functools import partial
import time
import random

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QKeySequence, QPainter, QFont, QColor, QPen
from PyQt5.QtWidgets import QToolBar, QAction, QStatusBar, QShortcut, QFileDialog

import glob

# windows
# os.add_dll_directory(r'your_vlc_path') 

# ubuntu/mac
# os.environ['LD_LIBRARY_PATH'] = 'your_vlc_path'  



class Player(QtWidgets.QMainWindow):

    def __init__(self, muted=False, save_frames=False, master=None):
        QtWidgets.QMainWindow.__init__(self, master)
        # self.setWindowIcon(QIcon("icons/app.svg"))
        self.setWindowIcon(QIcon(self.resource_path("icons/piaspace-crop.jpg")))
        self.title = "PIASPACE Video Annotation Tool"

        self.muted = muted
        self.save_frames = save_frames

        self.setWindowTitle(self.title)
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        options |= QFileDialog.Directory

        # options |= QFileDialog.DontUseNativeDialog

        supported_formats = [".mp3", ".mp4", ".avi", ".wmv", ".mp4", ".mov", ".ogg", ".wav", ".ogm"]

        self.video_paths = []
        while len(self.video_paths) == 0:
            videos_dir = str(QFileDialog.getExistingDirectory(self, "Select Videos Directory", options=options))
            self.video_paths = []
            for fmt in supported_formats:
                self.video_paths += [f for f in glob.glob(videos_dir + "**/*"+fmt, recursive=False)]
            self.video_paths = sorted(set(self.video_paths))
            print(self.video_paths)

            if len(self.video_paths) == 0 or len(videos_dir) == 0:
                QtWidgets.QMessageBox.question(self, 'No videos exist', "Please select a directory containing videos.",
                                                             QtWidgets.QMessageBox.Ok)

        self.annotations_dir = ""
        while len(self.annotations_dir) == 0:
            self.annotations_dir = str(QFileDialog.getExistingDirectory(self, "Select Annotations Directory", options=options))
            print(self.annotations_dir)
            self.annotation_paths = [f for f in glob.glob(self.annotations_dir + "**/*.json", recursive=False)]
            if len(self.annotations_dir) == 0:
                QtWidgets.QMessageBox.question(self, 'No directory selected.', "Please select a directory for annotations",
                                                             QtWidgets.QMessageBox.Ok)


        self.num_videos = len(self.video_paths)
        self.current_video = 0

        self.annotations = {}

        for annotation_path in self.annotation_paths:
            j = json.load(open(annotation_path, "r"))
            self.annotations[j["name"]] = j

        print(self.annotation_paths)

        self.createVideoPlayer()

        self.createUI()

        self.createToolbar()

        self.statusbar = QStatusBar(self)

        self.setStatusBar(self.statusbar)

        self.current_event = "S"
        self.current_ann_idx = 1
        self.current_annotation = self.current_event + str(self.current_ann_idx)

        self.statusbar.showMessage("Current Annotation: " + self.current_annotation)

        self.createShortcuts()


        is_video_set = False
        for i, video_path in enumerate(self.video_paths):

            if "\\" in video_path:
                video_name = video_path.split("\\")[-1]
            else:
                video_name = video_path.split("/")[-1]

            if video_name not in self.annotations:
                self.file = self.OpenFile(video_path)

                self.current_video_attrs = self.annotations.get(video_name, {
                    "name": video_name,
                    "path": video_path,
                    "annotations": {},
                    "annotations_frame": {}
                })
                self.annotations[self.current_video_attrs["name"]] = self.current_video_attrs
                self.current_video = i

                # is_video_set = True # Disable this feature for opening the video based on current annotation

                break

        if not is_video_set:
            video_path = self.video_paths[0]
            if "\\" in video_path:
                video_name = video_path.split("\\")[-1]
            else:
                video_name = video_path.split("/")[-1]
            self.file = self.OpenFile(video_path)
            self.current_video_attrs = self.annotations.get(video_name, {
                "name": video_name,
                "path": video_path,
                "annotations": {}
            })

            self.annotations[self.current_video_attrs["name"]] = self.current_video_attrs

        self.play()

        self.next_visible = True
        self.prev_visible = True
        self.setVisibilities()

    def resource_path(self, relative_path):
        """ Get the absolute path to a resource, works for dev and PyInstaller """
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def setPrevNextVisibility(self):
        self.prev_visible = self.current_video != 0
        self.next_visible = self.current_video != self.num_videos - 1
        self.remove_visible = self.current_video_attrs["name"] in self.annotations and len(self.annotations[self.current_video_attrs["name"]]["annotations"]) > 0
        
        self.current_annotation = self.current_event + str(self.current_ann_idx)

        self.action_previous.setVisible(self.prev_visible)
        self.action_next.setVisible(self.next_visible)
        self.action_remove_annotations.setVisible(self.remove_visible)
        self.statusbar.clearMessage()
        self.statusbar.showMessage("Current Annotation: " + self.current_annotation)

    def createShortcuts(self):
        self.shortcut_playpause = QShortcut(QKeySequence(QtCore.Qt.Key_Space), self)
        self.shortcut_playpause.activated.connect(self.playPauseShortcut)

        self.shortcut_previous = QShortcut(QKeySequence(QtCore.Qt.Key_Left), self)
        self.shortcut_previous.activated.connect(self.previousShortcut)

        self.shortcut_next = QShortcut(QKeySequence(QtCore.Qt.Key_Right), self)
        self.shortcut_next.activated.connect(self.nextShortcut)

        self.shortcut_annotate = QShortcut(QKeySequence(QtCore.Qt.Key_Return), self)
        self.shortcut_annotate.activated.connect(self.annotate)

        self.shortcut_remove_annotation = QShortcut(QKeySequence(QtCore.Qt.Key_Backspace), self)
        self.shortcut_remove_annotation.activated.connect(self.removeAnnotations)

        # New
        self.shortcut_increase_annotation = QShortcut(QKeySequence(QtCore.Qt.Key_Up), self)
        self.shortcut_increase_annotation.activated.connect(self.update_current_annotation)

        self.shortcut_decrease_annotation = QShortcut(QKeySequence(QtCore.Qt.Key_Down), self)
        self.shortcut_decrease_annotation.activated.connect(self.decrease_current_annotation)


        # New shortcuts for moving frame
        self.shortcut_frame_forward = QShortcut(QKeySequence(QtCore.Qt.Key_E), self)
        self.shortcut_frame_forward.activated.connect(partial(self.moveFrameForward, unit=1))
        

        self.shortcut_frame_backward = QShortcut(QKeySequence(QtCore.Qt.Key_W), self)
        self.shortcut_frame_backward.activated.connect(partial(self.moveFrameBackward, unit=1))


        self.shortcut_frame_forward = QShortcut(QKeySequence(QtCore.Qt.Key_R), self)
        self.shortcut_frame_forward.activated.connect(partial(self.moveFrameForward, unit=10))

        self.shortcut_frame_backward = QShortcut(QKeySequence(QtCore.Qt.Key_Q), self)
        self.shortcut_frame_backward.activated.connect(partial(self.moveFrameBackward, unit=10))

        # for s in string.ascii_uppercase:
        #     key = getattr(QtCore.Qt, "Key_" + s)
        #     shortcut = QShortcut(QKeySequence(key), self)
        #     shortcut.activated.connect(self.changeAnnotationShortcut(s))

    def changeAnnotationShortcut(self, s):

        def annotationShortcut():
            self.current_annotation = s
            self.statusbar.clearMessage()
            self.statusbar.showMessage("Current Annotation: " + self.current_annotation)

        return annotationShortcut
    

    def removeAnnotations(self):
        annotation_keys = None
        # Remove the latest annotation
        if self.current_video_attrs["annotations"]:
            # Get the keys and sort them to find the last added annotation
            annotation_keys = list(self.current_video_attrs["annotations"].keys())
            if annotation_keys:
                last_annotation_key = annotation_keys[-1]  # Get the last key
                del self.current_video_attrs["annotations"][last_annotation_key]  # Remove the last annotation

        if self.current_video_attrs["annotations_frame"]:
            # Get the keys and sort them to find the last added annotation
            annotation_keys = list(self.current_video_attrs["annotations_frame"].keys())
            if annotation_keys:
                last_annotation_key = annotation_keys[-1]  # Get the last key
                del self.current_video_attrs["annotations_frame"][last_annotation_key]  # Remove the last annotation
                
        self.annotations[self.current_video_attrs["name"]] = self.current_video_attrs

        if self.current_video_attrs["annotations_frame"]:
            self.current_annotation = last_annotation_key

        self.setVisibilities()
        if annotation_keys is not None:
            event, idx = last_annotation_key[0], int(last_annotation_key[1:])
            self.current_event = event
            self.current_ann_idx = idx
            self.current_annotation = self.current_event + str(self.current_ann_idx)
            self.statusbar.showMessage("Deleted Annotation: " + last_annotation_key + " / Current Annotation: " + self.current_annotation)

    def get_last_saved_event_key(self, annotations_frame_dict):
        if annotations_frame_dict:
            keys = list(annotations_frame_dict.keys())
            last_key = keys[-1]
            return last_key[0]

        else:
            return None
    
    def check_paired_ts_key(self, annotations_frame_dict):
        if annotations_frame_dict:
            keys = list(annotations_frame_dict.keys())
            
            # Extract all indices that appear in the keys
            indices = sorted(set(int(key[1:]) for key in keys if key[1:].isdigit()))
            
            # Initialize lists to hold paired and unpaired keys
            paired = []
            unpaired = []

            # Loop to find paired and unpaired keys
            for i in indices:
                s_key = f"S{i}"
                e_key = f"E{i}"
                if s_key in keys and e_key in keys:
                    paired.append((s_key, e_key))
                else:
                    if s_key in keys:
                        unpaired.append(s_key)
                    if e_key in keys:
                        unpaired.append(e_key)

            # Check if there are any unpaired keys
            if not unpaired:
                return None
            else:
                return unpaired
        else:
            return None


    def trigger_paired_warning(self, text = ""):
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setText(f"Time stamp should be paired, {text}")
        msg_box.setWindowTitle("Warning")
        msg_box.exec_()  # This will display the message box
            

    
    def previousShortcut(self):
        if self.prev_visible:
            unpaired = self.check_paired_ts_key(self.current_video_attrs["annotations_frame"])
            if unpaired:
                self.trigger_paired_warning(text=unpaired)
            else:
                time.sleep(0.3)
                self.previous()

    def nextShortcut(self):
        if self.next_visible:
            unpaired = self.check_paired_ts_key(self.current_video_attrs["annotations_frame"])
            if unpaired:
                self.trigger_paired_warning(text=unpaired)
            else:
                time.sleep(0.3)
                self.next()
            
    def moveFrameForward(self, unit):
        # Move the slider 1 unit forward
        current_position = self.positionslider.value()
        new_position = min(current_position + unit, 1000)
        self.positionslider.setValue(new_position)
        self.setPosition(new_position)

    def moveFrameBackward(self, unit):
        # Move the slider 1 unit backward
        current_position = self.positionslider.value()
        new_position = max(current_position - unit, 0)
        self.positionslider.setValue(new_position)
        self.setPosition(new_position)

    def setVisibilities(self):
        self.setPrevNextVisibility()

        self.markwidget.setAnnotations(self.annotations[self.current_video_attrs["name"]]["annotations"])

    def update_loaded_event_idx(self, event, idx):
        if event == "S":
            event = "E"
        elif event == "E":
            event = "S"
            idx += 1
        else:
            raise ValueError("Invalid event state")
        
        self.current_event = event
        self.current_ann_idx = idx

    def decrease_loaded_event_idx(self, event, idx):
        if event == "S":
            event = "E"
            idx = max(1, idx-1)
        elif event == "E":
            event = "S"
        else:
            raise ValueError("Invalid event state")
        
        self.current_event = event
        self.current_ann_idx = idx


    def annotate(self):

        if self.current_annotation in self.current_video_attrs["annotations"].keys():
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            msg_box.setText("Duplicated annotation")
            msg_box.setWindowTitle("Warning")
            msg_box.exec()  # This will display the message box

        else:
            self.current_video_attrs["annotations"][self.current_annotation] = [self.mediaplayer.get_position()] + self.current_video_attrs["annotations"].get(self.current_annotation, [])
            
            ## New
            # Get current time position in milliseconds
            current_time = self.mediaplayer.get_time()

            # Get FPS (Frames Per Second)
            fps = self.mediaplayer.get_fps()

            # Calculate current frame number
            current_frame = int((current_time / 1000) * fps)

            self.current_video_attrs["annotations_frame"][self.current_annotation] = [current_frame]


            self.annotations[self.current_video_attrs["name"]] = self.current_video_attrs
            
            self.update_loaded_event_idx(self.current_event, self.current_ann_idx)
            self.current_annotation = self.current_event + str(self.current_ann_idx)

            self.setVisibilities()

            if self.save_frames:
                self.writeFrameToFile()

    def writeFrameToFile(self):
        path_to_save = os.path.join(self.annotations_dir, self.current_annotation)
        if not os.path.exists(path_to_save):
            os.mkdir(path_to_save)

        frame_file_name = os.path.join(path_to_save, 
                                       f'{self.current_video_attrs["name"]}_{str(self.mediaplayer.get_position())}'.replace(".", "_") + '.png')

        self.mediaplayer.video_take_snapshot(0, frame_file_name, 0 , 0)

    def saveAnnotation(self, annotation):
        with open(os.path.join(self.annotations_dir, annotation["name"] + ".json"), "w+") as f:
            json.dump(annotation, f)

    def playPauseShortcut(self):
        if self.isPaused:
            self.play()
        else:
            self.pause()

    def createVideoPlayer(self):

        self.instance = vlc.Instance()

        self.mediaplayer = self.instance.media_player_new()

        if self.muted:
            self.mediaplayer.audio_set_volume(0)

        self.isPaused = False


    def createToolbar(self):
        toolbar = QToolBar("Manage Video")
        toolbar.setIconSize(QSize(32, 32))

        self.addToolBar(toolbar)

        # self.action_play = QAction(QIcon("icons/play-button.png"), "Play", self)
        self.action_play = QAction(QIcon(self.resource_path("icons/play-button.png")), "Play", self)
        self.action_play.triggered.connect(self.play)
        self.action_play.setStatusTip("Play Video [Space Key]")
        toolbar.addAction(self.action_play)


        # self.action_pause = QAction(QIcon("icons/pause.png"), "Pause", self)
        self.action_pause = QAction(QIcon(self.resource_path("icons/pause.png")), "Pause", self)
        self.action_pause.triggered.connect(self.pause)
        self.action_pause.setVisible(False)
        self.action_pause.setStatusTip("Pause Video [Space Key]")
        toolbar.addAction(self.action_pause)

        # self.action_previous = QAction(QIcon("icons/previous.png"), "Previous Video", self)
        self.action_previous = QAction(QIcon(self.resource_path("icons/previous.png")), "Previous Video", self)
        self.action_previous.setStatusTip("Previous Video [Left]")
        self.action_previous.triggered.connect(self.previous)
        toolbar.addAction(self.action_previous)

        # self.action_next = QAction(QIcon("icons/next.png"), "Next Video", self)
        self.action_next = QAction(QIcon(self.resource_path("icons/next.png")), "Next Video", self)
        self.action_next.triggered.connect(self.next)
        self.action_next.setStatusTip("Next Video [Right]")
        toolbar.addAction(self.action_next)

        # self.action_annotate = QAction(QIcon("icons/plus.png"), "Annotate to current frame of the video", self)
        self.action_annotate = QAction(QIcon(self.resource_path("icons/plus.png")), "Annotate to current frame of the video", self)
        self.action_annotate.triggered.connect(self.annotate)
        self.action_annotate.setStatusTip("Annotate to current frame of the video [Enter Key]")
        toolbar.addAction(self.action_annotate)

        # self.action_remove_annotations = QAction(QIcon("icons/cancel.png"), "Remove current video's annotations", self)
        self.action_remove_annotations = QAction(QIcon(self.resource_path("icons/cancel.png")), "Remove current video's annotations", self)
        self.action_remove_annotations.triggered.connect(self.removeAnnotations)
        self.action_remove_annotations.setStatusTip("Remove current video's annotations [Backspace Key]")
        toolbar.addAction(self.action_remove_annotations)


    def play(self):
        print("Play clicked")
        self.PlayPause()

    def pause(self):
        print("Pause clicked")
        self.PlayPause()


    def reset_annotation(self):
        self.current_event = "S"
        self.current_ann_idx = 1
        self.current_annotation = self.current_event + str(self.current_ann_idx)
        self.statusbar.showMessage("Current Annotation: " + self.current_annotation)
        
    
    def update_current_annotation(self):
        self.update_loaded_event_idx(self.current_event, self.current_ann_idx)
        self.current_annotation = self.current_event + str(self.current_ann_idx)
        self.statusbar.showMessage("Current Annotation: " + self.current_annotation)
    
    def decrease_current_annotation(self):
        self.decrease_loaded_event_idx(self.current_event, self.current_ann_idx)
        self.current_annotation = self.current_event + str(self.current_ann_idx)
        self.statusbar.showMessage("Current Annotation: " + self.current_annotation)


    def previous(self):

        print("Previous clicked")

        self.reset_annotation()

        if self.current_video - 1 < 0:
            return

        self.saveAnnotation(self.current_video_attrs)

        if not self.isPaused:
            self.Stop()

        self.current_video -= 1
        video_path = self.video_paths[self.current_video]
        if "\\" in video_path:
            video_name = video_path.split("\\")[-1]
        else:
            video_name = video_path.split("/")[-1]


        self.file = self.OpenFile(video_path)

        if video_name in self.annotations:
            self.current_video_attrs = self.annotations[video_name]
            if self.current_video_attrs["annotations_frame"]:
                keys = list(self.current_video_attrs["annotations_frame"].keys())
                idx_keys = sorted([int(key[1:]) for key in keys])
                self.current_event = "S"
                self.current_ann_idx = max(idx_keys) + 1
        else:
            self.current_video_attrs = {
                "name": video_name,
                "path": video_path,
                "annotations": {},
                "annotations_frame": {}
            }

            self.annotations[video_name] = self.current_video_attrs

        self.progress.setValue(self.current_video)

        self.setVisibilities()
        self.play()

    def next(self):
        print("Next clicked")
        
        self.reset_annotation()

        self.saveAnnotation(self.current_video_attrs)

        if not self.isPaused:
            self.Stop()

        self.current_video += 1

        if self.current_video == self.num_videos:
            QtWidgets.QMessageBox.question(self, "No more videos left.", "All videos are annotated. Now, opening the first video...",
            QtWidgets.QMessageBox.Ok)
            self.current_video = 0

        video_path = self.video_paths[self.current_video]

        if "\\" in video_path:
            video_name = video_path.split("\\")[-1]
        else:
            video_name = video_path.split("/")[-1]

        self.file = self.OpenFile(video_path)

        if video_name in self.annotations:
            self.current_video_attrs = self.annotations[video_name]
            if self.current_video_attrs["annotations_frame"]:
                keys = list(self.current_video_attrs["annotations_frame"].keys())
                idx_keys = sorted([int(key[1:]) for key in keys])
                self.current_event = "S"
                self.current_ann_idx = max(idx_keys) + 1
        else:
            self.current_video_attrs = {
                "name": video_name,
                "path": video_path,
                "annotations": {},
                "annotations_frame": {}
            }

            self.annotations[video_name] = self.current_video_attrs

        self.current_annotation = self.current_event + str(self.current_ann_idx)

        self.progress.setValue(self.current_video)

        self.setVisibilities()
        self.play()

    def createUI(self):
        """Set up the user interface, signals & slots
        """
        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)

        # In this widget, the video will be drawn
        # if sys.platform == "darwin": # for MacOS
        #     self.videoframe = QtWidgets.QMacCocoaViewContainer(0)
        # else:
        #     self.videoframe = QtWidgets.QFrame()
        self.videoframe = QtWidgets.QFrame()
        self.palette = self.videoframe.palette()
        self.palette.setColor (QtGui.QPalette.Window,
                               QtGui.QColor(0,0,0))
        self.videoframe.setPalette(self.palette)
        self.videoframe.setAutoFillBackground(True)

        self.positionslider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.positionslider.setToolTip("Position")
        self.positionslider.setMaximum(1000)
        self.positionslider.sliderMoved.connect(self.setPosition)

        self.vboxlayout = QtWidgets.QVBoxLayout()
        self.vboxlayout.addWidget(self.videoframe)
        self.vboxlayout.addWidget(self.positionslider)

        self.markwidget = MarkWidget()

        self.vboxlayout.addWidget(self.markwidget)


        self.widget.setLayout(self.vboxlayout)

        self.progress = QtWidgets.QProgressBar(self)
        self.progress.setMaximum(self.num_videos)
        self.vboxlayout.addWidget(self.progress)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.updateUI)


    def PlayPause(self):
        """Toggle play/pause status
        """
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.action_play.setVisible(True)
            self.action_pause.setVisible(False)
            self.isPaused = True
        else:
            self.mediaplayer.play()
            self.action_play.setVisible(False)
            self.action_pause.setVisible(True)
            self.timer.start()
            self.isPaused = False

    def Stop(self):
        """Stop player
        """
        self.mediaplayer.stop()


    def OpenFile(self, filename=None):
        """Open a media file in a MediaPlayer
        """
        if filename is None or filename is False:
            print("Attempt to openup OpenFile")
            filenameraw = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", os.path.expanduser('~'))
            filename = filenameraw[0]

        if not filename:
            return

        # create the media
        if sys.version < '3':
            filename = unicode(filename)
        self.media = self.instance.media_new(filename)
        # put the media in the media player
        self.mediaplayer.set_media(self.media)

        # parse the metadata of the file
        self.media.parse()
        # set the title of the track as window title
        self.setWindowTitle(self.title + " | " + self.media.get_meta(0))

        # the media player has to be 'connected' to the QFrame
        # (otherwise a video would be displayed in it's own window)
        # this is platform specific!
        # you have to give the id of the QFrame (or similar object) to
        # vlc, different platforms have different functions for this
        if sys.platform.startswith('linux'): # for Linux using the X Server
            self.mediaplayer.set_xwindow(self.videoframe.winId())
        elif sys.platform == "win32": # for Windows
            self.mediaplayer.set_hwnd(self.videoframe.winId())
        elif sys.platform == "darwin": # for MacOS
            self.mediaplayer.set_nsobject(int(self.videoframe.winId()))


    def setPosition(self, position):
        """Set the position
        """
        # setting the position to where the slider was dragged
        self.mediaplayer.set_position(position / 1000.0)
        # the vlc MediaPlayer needs a float value between 0 and 1, Qt
        # uses integer variables, so you need a factor; the higher the
        # factor, the more precise are the results
        # (1000 should be enough)

    def updateUI(self):
        """updates the user interface"""
        # setting the slider to the desired position
        self.positionslider.setValue(self.mediaplayer.get_position() * 1000)

        if not self.mediaplayer.is_playing():
            # no need to call this function if nothing is played
            self.timer.stop()

            if not self.isPaused:
                self.Stop()
                unpaired = self.check_paired_ts_key(self.current_video_attrs["annotations_frame"])
                if unpaired:
                    self.trigger_paired_warning(text=unpaired)
                    self.positionslider.setValue(0 * 1000)
                    self.play()
                else:
                    self.next()
                    print("Next based on Update UI")

class MarkWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.annotations = {}
        self.setMaximumSize(5000, 30)
        random.seed(102)

        self.index_color_map = {
            "1": [104, 67, 31],
            "2": [112, 254, 249],
            "3": [35, 16, 234],
            "4": [255, 218, 30],
            "5": [1, 235, 94],
            "6": [251, 78, 251],
            "7": [137, 136, 164],
            "8": [230, 3, 110],
            "9": [112, 246, 18],
            "10": [252, 246, 253],
            "11": [26, 149, 229],
            "12": [3, 107, 104],
            "13": [221, 99, 6],
            "14": [250, 119, 131],
            "15": [88, 14, 130],
            "16": [175, 15, 213],
            "17": [158, 224, 141],
            "18": [5, 247, 203],
            "19": [40, 164, 10],
            "20": [156, 107, 251],
            "21": [1, 2, 10],
            "22": [170, 129, 72],
            "23": [198, 13, 9],
            "24": [242, 163, 227],
            "25": [80, 213, 90],
            "26": [153, 179, 0],
            "27": [246, 242, 136],
            "28": [232, 205, 54],
            "29": [48, 0, 118],
            "30": [145, 141, 159],
            "31": [209, 123, 57],
            "32": [54, 238, 181],
            "33": [234, 129, 225],
            "34": [68, 18, 185],
            "35": [217, 190, 167],
            "36": [46, 109, 136],
            "37": [39, 36, 205],
            "38": [97, 184, 251],
            "39": [223, 58, 100],
            "40": [2, 77, 235],
            "41": [176, 84, 182],
            "42": [186, 197, 194],
            "43": [243, 216, 112],
            "44": [222, 184, 177],
            "45": [84, 47, 72],
            "46": [88, 194, 209],
            "47": [52, 87, 214],
            "48": [115, 250, 36],
            "49": [229, 59, 230],
            "50": [244, 144, 16],
            "51": [189, 54, 232],
            "52": [7, 32, 192],
            "53": [212, 224, 223],
            "54": [130, 97, 27],
            "55": [170, 218, 211],
            "56": [43, 206, 103],
            "57": [120, 135, 216],
            "58": [200, 36, 50],
            "59": [112, 133, 45],
            "60": [62, 79, 130],
            "61": [68, 33, 4],
            "62": [59, 247, 47],
            "63": [112, 191, 51],
            "64": [195, 149, 250],
            "65": [204, 209, 119],
            "66": [117, 250, 86],
            "67": [198, 190, 30],
            "68": [174, 134, 5],
            "69": [17, 104, 54],
            "70": [201, 41, 252],
            "71": [118, 108, 86],
            "72": [202, 3, 59],
            "73": [31, 115, 187],
            "74": [249, 162, 174],
            "75": [76, 201, 1],
            "76": [219, 11, 176],
            "77": [38, 196, 198],
            "78": [112, 205, 249],
            "79": [198, 93, 59],
            "80": [157, 228, 193],
            "81": [5, 249, 253],
            "82": [133, 1, 52],
            "83": [255, 207, 192],
            "84": [55, 196, 143],
            "85": [84, 35, 250],
            "86": [42, 201, 45]
        }


    def get_color_for_index(self, index):
        if str(index) not in self.index_color_map:
            # Generate a random color and store it in the map as a list
            self.index_color_map[str(index)] = [
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            ]
        # Convert the list to a QColor object before returning
        color_values = self.index_color_map[str(index)]
        return QColor(color_values[0], color_values[1], color_values[2])



    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()

    def setAnnotations(self, annotations):
        self.annotations = annotations
        self.repaint()


    def drawWidget(self, qp):
        MAX_CAPACITY  = 1000
        font = QFont('Serif', 10, QFont.Light)
        qp.setFont(font)
        size = self.size()
        w    = size.width()
        h    = size.height()
        step = int(round(w / 1000))
        full = int(((w / MAX_CAPACITY) * MAX_CAPACITY))

        qp.setPen(QColor(255, 255, 255))
        qp.setBrush(QColor(255, 255, 184))
        qp.drawRect(0, 0, full, h)

        pen = QPen(QColor(20, 20, 20), 1, Qt.SolidLine)
        qp.setPen(pen)
        qp.setBrush(Qt.NoBrush)
        qp.drawRect(0, 0, w-1, h-1)
        j = 0
        
        for key, poslist in self.annotations.items():
            current_idx = int(key[1:])
            qp.setPen(QPen(self.get_color_for_index(current_idx), 1.5, Qt.SolidLine))

            for pos in poslist:
                x = int(w*pos)
                metrics = qp.fontMetrics()
                qp.drawLine(x, 0, x, h)
                fw = metrics.width(key)
                qp.drawText(x+fw/2, h/2, key)




if __name__ == "__main__":
    # os.environ["VLC_PLUGIN_PATH"] = "/usr/lib64/vlc/plugins"
    parser = argparse.ArgumentParser(
        description='PIASPACE video annotation.')
    parser.add_argument('--muted', action='store_true',
                        help=('Run muted.'))
    parser.add_argument('--save_frames', action='store_true',
                        help=('Save video frames as png files during annotation.'))

    args = parser.parse_args()
    
    app = QtWidgets.QApplication(sys.argv)
    player = Player(args.muted, args.save_frames)
    player.show()
    player.resize(640, 480)
    sys.exit(app.exec_())

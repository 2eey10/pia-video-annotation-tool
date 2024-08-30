#  PIA Video Annotation Tool
Video Annotation Tool helps to annotate positions in videos possibly for events later to be processed.


### Requirements
* [Anaconda3](https://www.anaconda.com/distribution/#download-section)


### Installation

To install the necessary environment, run the following command:

```bash
conda env create -f env.yml
```

### Running Instructions
1. Execute `conda activate video-activation-tool` in shell.
2. Execute `python main.py` in shell.
3. Select directory containing videos to be annotated at first file dialog.
4. Select directory to put annotations (should contain current annotations if there is) at second file dialog.
5. Use shortcuts or the icons in menu to proceed.

### Annotation Format
```
{
   "name":"video_file_name.avi",
   "path":"/Volumes/NAME/video_file_path.avi",
   "annotations":{
      "F":[
         0.051943399012088776
      ],
      "S":[
         0.14098712801933289
      ],
      "A":[
         0.28347572684288025,
         0.2289014607667923,
         0.194297194480896,
         ... other annoation positions within [0, 1] annotated with A
      ],
   "annotations_frames":{
      "S": ...
   }
}
```
- The `"annotations"` positions correspond to the position in the video, normalized to a range of `[0, 1]`.
- The `"annotations_frames"` correspond to the current frame number.

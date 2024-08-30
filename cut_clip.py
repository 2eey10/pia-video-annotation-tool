import os
import json
import cv2

# Define the path to the JSON files
JSON_PATH = "C:\\Users\\rahad\\Downloads\\Abuse-20240829T064653Z-001\\Abuse"

# Find all .json files in the directory
json_files = [f for f in os.listdir(JSON_PATH) if f.endswith('.json')]

export_path = "./"
for json_file in json_files:
    # Construct full path to the JSON file
    json_file_path = os.path.join(JSON_PATH, json_file)
    
    # Load the JSON data
    with open(json_file_path, 'r') as f:
        json_data = json.load(f)
    
    # Extract the video path
    video_path = json_data["path"]
    video_name = os.path.basename(video_path)
    
    # Read the video using OpenCV
    video = cv2.VideoCapture(video_path)
    
    # Check if the video was successfully opened
    if not video.isOpened():
        raise ValueError(f"Error opening video file: {video_path}")
    
    # Find the total number of frames
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Extract annotation pairs from the JSON data
    annotations = json_data.get("annotations_frame", {})
    
    # Ensure the annotation pairs exist
    if not annotations:
        print(f"No annotation pairs found in {video_name}")
        continue
    
    # Make annotation pairs list
    pairs_list = []
    for key in annotations:
        if key.startswith("S"):
            index = key[1:]  # Extract the index number
            E_key = f"E{index}"
            S_value = annotations[key][0]
            E_value = annotations.get(E_key, [None])[0]
            
            if E_value is not None:
                pairs_list.append((int(S_value), int(E_value)))
            else:
                raise ValueError(f"Missing corresponding 'E' value for 'S{index}' in annotations.")
    
    # Print the pairs list
    print(f"Video: {video_name}")
    print("Annotation Pairs List:")
    print(pairs_list)
    
    # Loop through each pair and create video clips
    for pair in pairs_list:
        start_frame = pair[0]
        end_frame = pair[1]
        
        # Set the video to the start frame
        video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Initialize video writer
        clip_name = f"{video_name}_{start_frame}_{end_frame}.mp4"
        output_path = os.path.join(export_path, clip_name)
        fps = video.get(cv2.CAP_PROP_FPS)
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Write frames from start_frame to end_frame
        for frame_num in range(start_frame, end_frame + 1):
            ret, frame = video.read()
            if not ret:
                print(f"Error reading frame {frame_num} from {video_name}")
                break
            out.write(frame)
        
        # Release the video writer
        out.release()
        print(f"Exported clip: {output_path}")

    # Release the video file
    video.release()

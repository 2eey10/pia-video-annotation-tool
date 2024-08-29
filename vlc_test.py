import vlc

# Initialize VLC instance
vlc_instance = vlc.Instance()
media_player = vlc_instance.media_player_new()
print("works")
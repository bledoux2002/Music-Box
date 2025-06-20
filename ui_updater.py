import os
from tracks import Track
from yt_dlp.postprocessor import PostProcessor

class UIUpdatePostProcessor(PostProcessor):
    def __init__(self, musicbox_instance):
        '''
        Custom post-processor to update UI as files are downloaded
        '''
        super().__init__(None)
        self.musicbox = musicbox_instance

    def run(self, info):
        # This runs after the file is fully processed (e.g., mp3 is ready)
        filename = info['filepath']
        basename = os.path.basename(filename)
        # Add to playlist and tracks
        self.musicbox.playlist_all.add_track(self.musicbox.clean_filename(basename), basename)
        self.musicbox.tracks[basename] = Track()
        # Update the UI (must use .after to run in main thread)
        self.musicbox.root.after(0, lambda: self.musicbox.change_playlist(None))
        self.musicbox.cur_download += 1
        return [], info
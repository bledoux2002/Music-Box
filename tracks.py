import random

class Playlist:
    def __init__(self, name):
        self.name = name
        self.tracks = {}
        self.new_queue()

    def set_name(self, name):
        self.name = name

    def add_track(self, name, file):
        self.tracks[name] = file
        self.queue.append(name)

    def remove_track(self, name):
        del self.tracks[name]
        self.queue.remove(name)

    def get_track_names(self):
        names = []
        for name, _ in self.tracks.items():
            names.append(name)
        return names

    def get_tracks(self):
        tracks = []
        for _, track in self.tracks.items():
            tracks.append(track)
        return tracks

    def get_track(self, name):
        return self.tracks[name]
    
    def get_queue(self):
        return self.queue
    
    def shuffle_queue(self):
        random.shuffle(self.queue)
        
    def queue_pop(self, shuffle):
        track = self.queue[0]
        self.queue = self.queue[1:]
        if self.queue_empty():
            self.new_queue()
            if shuffle:
                self.shuffle_queue()
        return self.tracks[track]
    
    def new_queue(self):
        self.queue = []
        for track, _ in self.tracks.items():
            self.queue.append(track)
            
    def queue_empty(self):
        if len(self.queue) == 0:
            return True
        else:
            return False
    
    def get_length(self):
        return len(self.tracks)

class Track:
    def __init__(self):
        self.playlists = set()
        
    def add_to_playlist(self, playlist):
        self.playlists.add(playlist)
    
    def remove_from_playlist(self, playlist):
        if playlist in self.playlists:
            self.playlists.remove(playlist)
    
    def get_playlists(self):
        return self.playlists
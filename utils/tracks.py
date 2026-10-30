import random

class Playlist:
    def __init__(self, name):
        '''
        Playlist class to hold a list of tracks and their filenames, controlling ordering of playback
        '''
        self.name = name
        self.queue = []
        self.queue_pos = 0
        self.tracks = {}
        self.was_shuffled = False

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def add_track(self, name, file):
        self.tracks[name] = file
        self.queue.append(name)

    def remove_track(self, name):
        del self.tracks[name]
        self.queue.remove(name)

    def get_track(self, name):
        return self.tracks[name]

    def get_tracks(self):
        tracks = []
        for _, track in self.tracks.items():
            tracks.append(track)
        return tracks

    def get_track_names(self):
        names = []
        for name, _ in self.tracks.items():
            names.append(name)
        return names

    def get_queue(self):
        return self.queue
    
    def get_queue_pos(self):
        return self.queue_pos
    
    def set_queue_pos(self, num):
        self.queue_pos = num
        
    def increment_queue(self, num):
        # Next song played in queue (or previous if given -1). Will loop the playlist, preserving order even if shuffled
        self.queue_pos += num
        if self.queue_pos >= len(self.queue):
            self.queue_pos = 0
        elif self.queue_pos < 0:
            self.queue_pos = len(self.queue) - 1
        track = self.queue[self.queue_pos]
        return track

    def shuffle_queue(self):
        # Shuffle queue while ensuring current track is at start
        print('Before shuffle: ' + str(self.queue_pos))
        cur_track = self.queue[self.queue_pos]
        random.shuffle(self.queue)
        index = self.queue.index(cur_track)
        self.queue.pop(index)
        self.queue.insert(0, cur_track)
        self.queue_pos = 0
        print('After shuffle: ' + str(self.queue_pos))

    def unshuffle_queue(self):
        # Unshuffle queue, relocating position of current track
        print('Before unshuffle: ' + str(self.queue_pos))
        cur_track = self.queue[self.queue_pos]
        self.queue = self.get_track_names()
        self.queue_pos = self.queue.index(cur_track)
        print('After unshuffle: ' + str(self.queue_pos))

    def get_length(self):
        return len(self.tracks)

    def get_queue_position(self):
        return self.queue_pos

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
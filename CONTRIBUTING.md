# Contributing to Adaptive Music Box

## How to Contribute

- Fork the repository
- Create a new branch for your feature or bugfix
- Make your changes
- Submit a pull request

## Ways to Contribute

- **Coding Style**: Codebase is currently very messy. But it works. So whatever. Compartmentalizing code, even just reogranizing existing functions into more descriptive sections would be helpful.
- **Efficiency**: A lot of redundant code. Same as **Coding Style**. Particularly downloading a playlist of videos with `yt_dlp` will first download the following once for every file to get the information, then again when actually downloading them. This was the only way to add the tracks as they were downloaded, but time-wise it hardly helps since these are downloaded 2n times for n videos.
```
[youtube] id: Downloading webpage 
[youtube] id: Downloading tv client config 
[youtube] id: Downloading tv player API JSON 
[youtube] id: Downloading ios player API JSON 
[youtube] id: Downloading m3u8 information
```
- **Tests**: Currently there are no unit tests to ensure functionality. They would make development and testing much easier.
"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

from mabench.environments.base import Env
from mabench.environments.retail.data import load_data
from typing import Dict, List, Optional, Union, Any, Callable
from mabench.environments.user import UserStrategy


def search_tracks(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for tracks on Spotify by name, artist, or album.

    Args:
        query: Search query string
        limit: Maximum number of results to return (default: 10)

    Returns:
        List of track objects with id, name, artist, album, and popularity
    """
    pass


def get_track_details(track_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific track.

    Args:
        track_id: Spotify track ID

    Returns:
        Track details including audio features (tempo, key, danceability, etc.)
    """
    pass


def create_playlist(
    user_id: str, name: str, description: str, public: bool = False
) -> Dict[str, Any]:
    """Create a new playlist for a user.

    Args:
        user_id: User's Spotify ID
        name: Name of the playlist
        description: Description of the playlist
        public: Whether the playlist should be public (default: False)

    Returns:
        Details of the created playlist including ID
    """
    pass


def add_tracks_to_playlist(playlist_id: str, track_ids: List[str]) -> Dict[str, Any]:
    """Add tracks to an existing playlist.

    Args:
        playlist_id: Spotify playlist ID
        track_ids: List of track IDs to add

    Returns:
        Status of the operation
    """
    pass


def get_user_playlists(user_id: str) -> List[Dict[str, Any]]:
    """Get a list of the user's playlists.

    Args:
        user_id: User's Spotify ID

    Returns:
        List of playlist objects with id, name, and track count
    """
    pass


def get_playlist_tracks(playlist_id: str) -> List[Dict[str, Any]]:
    """Get the tracks in a playlist.

    Args:
        playlist_id: Spotify playlist ID

    Returns:
        List of track objects in the playlist
    """
    pass


def get_recommendations(
    seed_tracks: List[str], limit: int = 20
) -> List[Dict[str, Any]]:
    """Get track recommendations based on seed tracks.

    Args:
        seed_tracks: List of track IDs to use as seeds (max 5)
        limit: Maximum number of recommendations to return (default: 20)

    Returns:
        List of recommended track objects
    """
    pass


def create_radio(track_id: str, duration_minutes: int = 60) -> Dict[str, Any]:
    """Create a radio station based on a track.

    Args:
        track_id: Seed track ID
        duration_minutes: Duration of the radio in minutes (default: 60)

    Returns:
        Radio session details including tracks
    """
    pass


def get_user_profile(user_id: str) -> Dict[str, Any]:
    """Get a user's Spotify profile information.

    Args:
        user_id: User's Spotify ID

    Returns:
        User profile details including subscription level and preferences
    """
    pass


def get_user_top_tracks(
    user_id: str, time_range: str = "medium_term"
) -> List[Dict[str, Any]]:
    """Get a user's top tracks.

    Args:
        user_id: User's Spotify ID
        time_range: Time range to consider (short_term, medium_term, long_term)

    Returns:
        List of the user's most played tracks
    """
    pass


def start_playback(
    device_id: str,
    context_uri: Optional[str] = None,
    track_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Start or resume playback on a device.

    Args:
        device_id: ID of the device to play on
        context_uri: URI of album, artist, or playlist to play
        track_ids: List of track IDs to play (used if context_uri is None)

    Returns:
        Status of the playback operation
    """
    pass


def pause_playback(device_id: str) -> Dict[str, Any]:
    """Pause playback on a device.

    Args:
        device_id: ID of the device

    Returns:
        Status of the pause operation
    """
    pass


def skip_to_next(device_id: str) -> Dict[str, Any]:
    """Skip to the next track in the queue.

    Args:
        device_id: ID of the device

    Returns:
        Status of the skip operation
    """
    pass


def skip_to_previous(device_id: str) -> Dict[str, Any]:
    """Skip to the previous track in the queue.

    Args:
        device_id: ID of the device

    Returns:
        Status of the skip operation
    """
    pass


def get_available_devices(user_id: str) -> List[Dict[str, Any]]:
    """Get a list of the user's available devices.

    Args:
        user_id: User's Spotify ID

    Returns:
        List of available devices with their IDs and types
    """
    pass


def create_mood_based_playlist(
    user_id: str, mood: str, name: str = None
) -> Dict[str, Any]:
    """Create a playlist based on a specified mood.

    Args:
        user_id: User's Spotify ID
        mood: Desired mood (e.g., 'happy', 'relaxed', 'energetic')
        name: Custom name for the playlist (default: None, will use mood name)

    Returns:
        Created playlist details
    """
    pass


def get_artist_top_tracks(artist_id: str) -> List[Dict[str, Any]]:
    """Get an artist's top tracks.

    Args:
        artist_id: Spotify artist ID

    Returns:
        List of the artist's top tracks
    """
    pass


def queue_track(track_id: str, device_id: str) -> Dict[str, Any]:
    """Add a track to the playback queue.

    Args:
        track_id: Spotify track ID
        device_id: ID of the device

    Returns:
        Status of the queue operation
    """
    pass


def search_by_genre(genre: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Search for tracks by genre.

    Args:
        genre: Genre to search for
        limit: Maximum number of results to return (default: 20)

    Returns:
        List of tracks matching the genre
    """
    pass


def transfer_to_human_dj() -> Dict[str, str]:
    """Transfer the conversation to a human DJ specialist.

    Returns:
        Status message of the transfer
    """
    pass


ALL_TOOLS = [
    search_tracks,
    get_track_details,
    create_playlist,
    add_tracks_to_playlist,
    get_user_playlists,
    get_playlist_tracks,
    get_recommendations,
    create_radio,
    get_user_profile,
    get_user_top_tracks,
    start_playback,
    pause_playback,
    skip_to_next,
    skip_to_previous,
    get_available_devices,
    create_mood_based_playlist,
    get_artist_top_tracks,
    queue_track,
    search_by_genre,
    transfer_to_human_dj,
]

WIKI = """
# Spotify DJ AI Policy

The current time is 2025-03-24 22:55:00 PST.

As a Spotify DJ AI, you can help users discover music, create and manage playlists, and control playback on their devices.

- Before taking any actions that modify a user's library (creating playlists, adding tracks, deleting playlists), you must list the action details and obtain explicit user confirmation (yes) to proceed.

- You should not provide any information, knowledge, or procedures not provided by the user or available tools, or give subjective recommendations or comments about artists' personal lives or controversies.

- You should only make one tool call at a time, and if you make a tool call, you should not respond to the user simultaneously. If you respond to the user, you should not make a tool call at the same time.

- You should deny user requests that are against this policy.

- You should transfer the user to a human DJ specialist if and only if the request cannot be handled within the scope of your actions.

## Domain Basic

- Each user has a profile containing user ID, display name, email, subscription type (Free, Premium, or Family), connected devices, and saved playlists.

- Each track has a track ID, name, artist(s), album, duration, and audio features (tempo, key, danceability, energy, valence, etc.).

- Each playlist has a playlist ID, name, description, owner, privacy setting (public or private), and a list of tracks.

- Device playback status includes the active device, currently playing track, playback state (playing, paused), volume, and queue.

## Music Discovery

- The DJ must first confirm the user's ID before proceeding with personalized recommendations.

- Recommendations can be generated based on seed tracks, artists, genres, or the user's listening history. The DJ can use get_recommendations to generate suggestions.

- Radio stations can be created based on tracks, artists, or moods using the create_radio function.

- Mood-based playlists can be created using create_mood_based_playlist, which analyzes audio features to match tracks with specific moods.

## Playlist Management

- Creating playlists: The DJ can create new playlists with a name and description. A playlist can be public or private (default is private).

- Adding tracks: Tracks can be added to playlists using add_tracks_to_playlist. Before adding tracks, the DJ should confirm the action with the user.

- Viewing playlists: The DJ can retrieve a user's playlists and display their contents.

- Premium users can create unlimited playlists, while Free users are limited to 10,000 tracks across all playlists.

## Playback Control

- The DJ can control playback on the user's available devices, including starting/resuming playback, pausing, and skipping tracks.

- Before starting playback, the DJ must confirm the device to play on by retrieving available devices using get_available_devices.

- Premium users have unlimited skips and can play any specific track on demand. Free users have limited skips per hour and can only play in shuffle mode for playlists and albums.

- The queue_track function allows adding tracks to the playback queue. Premium users can queue any track, while Free users can only queue tracks from their own playlists.

## Feature Limitations

- Premium features: On-demand track playback, unlimited skips, no advertisements, higher audio quality, and offline listening.

- Free user limitations: Shuffle-only mode for playlists and albums, limited skips, advertisements between songs, and standard audio quality.

- Some features might not be available in all regions or on all devices. The DJ should inform users when a requested feature is not available for their subscription type or region.

## Privacy and Consent

- The DJ must respect users' privacy preferences and obtain consent before creating public playlists or accessing personal listening history.

- The DJ should not share a user's playlists or listening history with other users without explicit permission.

- For any personalized recommendation that requires accessing the user's listening history, the DJ should explain what data will be used and get user consent.
"""

RULES = [
    "You are a Spotify DJ AI assistant. You are chatting with a user, and you can call tools or respond to the user.",
    "The DJ should always first confirm the user ID before proceeding with any personalized task.",
    "The DJ should not proceed with any task if the user ID is not found.",
    "For any changes to the user's library, e.g., playlist creation, adding tracks, or modifying playback, the DJ must confirm the details with the user and ask for permission, and get explicit authorization (yes) to proceed.",
    "The DJ should solve the user task given the tools, without transferring to a human DJ specialist unless absolutely necessary.",
    "The DJ should not make up any information or knowledge about music, artists, or features not provided from the user or the tools.",
    "The DJ should at most make one tool call at a time, and if the DJ makes a tool call, it does not respond to the user at the same time.",
    "The DJ should respect subscription limitations and inform Free users when a Premium feature is requested.",
    "The DJ should not provide any subjective opinions on artists' personal lives or controversies.",
    "The DJ should prioritize user privacy and only access listening history with consent.",
]


class MockSpotifyDomainEnv(Env):
    name: str = "spotify"

    def __init__(
        self,
        user_strategy: Union[str, UserStrategy] = UserStrategy.LLM,
        user_model: str = "gpt-4o",
        user_provider: Optional[str] = None,
        task_split: str = "test",
        task_index: Optional[int] = None,
        **kwargs: Any,
    ):
        super().__init__(
            data_load_func=load_data,
            tools=ALL_TOOLS,
            tasks=[],
            wiki=WIKI,
            rules=RULES,
            user_strategy=user_strategy,
            user_model=user_model,
            user_provider=user_provider,
            task_index=task_index,
            **kwargs,
        )
        self.terminate_tools = ["transfer_to_human_dj"]

    @property
    def tools_info(self) -> Dict[str, Dict[str, Callable]]:
        return {self.name: self.tools_map}

from json import tool
import os
import json
from typing import Optional
from agents.context_agents import ContextAgent
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import anthropic
from langchain.tools import tool

from langchain.agents import create_agent



# Wrapper for Spotify API Interactions
class SpotifyClient():
    def __init__(self):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
                client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
                redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback"),
                scope="user-top-read user-read-recently-played"
            )
        )

    
    def get_top_tracks(self, time_range: str = "medium_term", limit: int = 5) -> list:
        try:
            results = self.sp.current_user_top_tracks(time_range=time_range, limit=limit)
            return [
                {
                    "name": track["name"],
                    "artist": ", ".join([artist["name"] for artist in track["artists"]]),
                    "popularity": track["popularity"]
                }
                for track in results["items"]
            ]
        except Exception as e:
            return [{"error": f"Failed to fetch top tracks: {str(e)}"}]

    
    def get_recent_tracks(self, limit: int = 5) -> list:

        try:
            results = self.sp.current_user_recently_played(limit=limit)
            return [
                {
                    "name": track["track"]["name"],
                    "artist": ", ".join([artist["name"] for artist in track["track"]["artists"]]),
                    "played_at": track["played_at"]
                }
                for track in results["items"]
            ]
        except Exception as e:
            return [{"error": f"Failed to fetch recent tracks: {str(e)}"}]

    
    def get_favorite_genres(self, limit: int = 5) -> list:

        try:
            results = self.sp.current_user_top_artists(limit=50, time_range="medium_term")
            genre_counts = {}

            for artist in results["items"]:
                for genre in artist.get("genres", []):
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1

            sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
            return [{"genre": genre, "count": count} for genre, count in sorted_genres[:limit]]
        except Exception as e:
            return [{"error": f"Failed to fetch favorite genres: {str(e)}"}]

    
    def get_top_artists(self, time_range: str = "medium_term", limit: int = 5) -> list:

        try:
            results = self.sp.current_user_top_artists(time_range=time_range, limit=limit)
            return [
                {
                    "name": artist["name"],
                    "genres": artist.get("genres", []),
                    "popularity": artist["popularity"]
                }
                for artist in results["items"]
            ]
        except Exception as e:
            return [{"error": f"Failed to fetch top artists: {str(e)}"}]

    
    def get_current_user_profile(self) -> dict:

        try:
            user = self.sp.current_user()
            return {
                "display_name": user.get("display_name"),
                "followers": user.get("followers", {}).get("total", 0),
                "external_urls": user.get("external_urls", {}).get("spotify"),
                "country": user.get("country")
            }
        except Exception as e:
            return {"error": f"Failed to fetch user profile: {str(e)}"}


class SpotifyAgent(ContextAgent):
    # Tools are wrappers over the SpotifyCLient functions that interact with the Spotify API.
    @tool
    def get_top_tracks(self, time_range, limit) -> list:
        """Get user's top tracks.
        Args:
            time_range: 'long_term' (several years), 'medium_term' (6 months), 'short_term' (4 weeks)
            limit: Number of tracks to return (1-50)
        Returns:
            List of track information
        """
        return self.spotify_client.get_top_tracks(time_range=time_range, limit=limit)
    
    @tool
    def get_recent_tracks(self, limit) -> list:
        """Get user's recently played tracks.
        Args:
            limit: Number of recent tracks to return (1-50)

        Returns:
            List of recently played track information
        """
        return self.spotify_client.get_recent_tracks(limit=limit)
    
    @tool
    def get_favorite_genres(self, limit) -> list:
        """Get user's favorite genres based on top artists.
        Args:
            limit: Number of genres to return

        Returns:
            List of favorite genres with counts
        """
        return self.spotify_client.get_favorite_genres(limit=limit)
    
    @tool
    def get_top_artists(self, time_range, limit) -> list:
        """Get user's top artists.
        Args:
            time_range: 'long_term', 'medium_term', or 'short_term'
            limit: Number of artists to return (1-50)

        Returns:
            List of top artist information
        """
        return self.spotify_client.get_top_artists(time_range=time_range, limit=limit)
    
    @tool
    def get_current_user_profile(self) -> dict:
        """Get current user's profile information.
        Returns:
            User profile data
        """
        return self.spotify_client.get_current_user_profile()

    def __init__(self):
        self.agent = create_agent(
            model="claude-opus-4-6",
            tools=[self.get_top_tracks, self.get_recent_tracks, self.get_favorite_genres, self.get_top_artists, self.get_current_user_profile],
            system_prompt=self.system_prompt
        )

        self.spotify_client = SpotifyClient()

    




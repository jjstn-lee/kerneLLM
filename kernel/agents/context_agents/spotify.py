import os
import json
from typing import Optional
from agents.context_agents import ContextAgent
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import anthropic

class SpotifyClient():
    def __init__(self):
        # Initialize Spotify client with OAuth
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
                client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
                redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback"),
                scope="user-top-read user-read-recently-played"
            )
        )
        
    def get_top_tracks(self, time_range: str = "medium_term", limit: int = 5) -> list:
        """Get user's top tracks.

        Args:
            time_range: 'long_term' (several years), 'medium_term' (6 months), 'short_term' (4 weeks)
            limit: Number of tracks to return (1-50)

        Returns:
            List of track information
        """
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
        """Get user's recently played tracks.

        Args:
            limit: Number of recent tracks to return (1-50)

        Returns:
            List of recently played track information
        """
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
        """Get user's favorite genres based on top artists.

        Args:
            limit: Number of genres to return

        Returns:
            List of favorite genres with counts
        """
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
        """Get user's top artists.

        Args:
            time_range: 'long_term', 'medium_term', or 'short_term'
            limit: Number of artists to return (1-50)

        Returns:
            List of top artist information
        """
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
        """Get current user's profile information.

        Returns:
            User profile data
        """
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

    def run(self, prompt: str = "") -> str:
        """Execute the agent with optional user prompt.

        Args:
            prompt: User's request for Spotify data

        Returns:
            Formatted string with requested Spotify information
        """
        prompt_lower = prompt.lower()
        result = {}

        # Default: return overview of user's Spotify data
        if not prompt or "overview" in prompt_lower:
            result["profile"] = self.get_current_user_profile()
            result["top_tracks"] = self.get_top_tracks()
            result["top_artists"] = self.get_top_artists()
            result["favorite_genres"] = self.get_favorite_genres()

        # Handle specific requests
        if "recent" in prompt_lower or "recently" in prompt_lower:
            result["recent_tracks"] = self.get_recent_tracks()

        if "top track" in prompt_lower:
            result["top_tracks"] = self.get_top_tracks()

        if "top artist" in prompt_lower:
            result["top_artists"] = self.get_top_artists()

        if "genre" in prompt_lower:
            result["favorite_genres"] = self.get_favorite_genres()

        return self._format_output(result)

    def _format_output(self, data: dict) -> str:
        """Format the output data into a readable string."""
        output = []

        if "profile" in data and data["profile"]:
            profile = data["profile"]
            if "error" not in profile:
                output.append(f"👤 User: {profile.get('display_name', 'Unknown')}")
                output.append(f"   Followers: {profile.get('followers', 0)}")
                if profile.get("country"):
                    output.append(f"   Country: {profile['country']}")

        if "top_tracks" in data and data["top_tracks"]:
            output.append("\n🎵 Top Tracks:")
            for i, track in enumerate(data["top_tracks"][:5], 1):
                if "error" not in track:
                    output.append(f"   {i}. {track['name']} - {track['artist']} ({track['popularity']}% popularity)")

        if "top_artists" in data and data["top_artists"]:
            output.append("\n🎤 Top Artists:")
            for i, artist in enumerate(data["top_artists"][:5], 1):
                if "error" not in artist:
                    output.append(f"   {i}. {artist['name']} ({artist['popularity']}% popularity)")

        if "favorite_genres" in data and data["favorite_genres"]:
            output.append("\n🎸 Favorite Genres:")
            for i, genre_info in enumerate(data["favorite_genres"][:5], 1):
                if "error" not in genre_info:
                    output.append(f"   {i}. {genre_info['genre']} (appears in {genre_info['count']} artist(s))")

        if "recent_tracks" in data and data["recent_tracks"]:
            output.append("\n⏰ Recently Played:")
            for i, track in enumerate(data["recent_tracks"][:5], 1):
                if "error" not in track:
                    output.append(f"   {i}. {track['name']} - {track['artist']}")

        return "\n".join(output) if output else "No Spotify data available."

class SpotifyAgent(ContextAgent):
    def __init__(self, id: str, system_prompt: str = "", kb: Optional[dict] = None):
        super().__init__(id, system_prompt, kb)
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.spotify_client = SpotifyClient()
        self.model = "claude-opus-4-6"

    def _create_tools(self):
        """Create tool definitions from SpotifyClient methods."""
        return [
            {
                "name": "get_current_user_profile",
                "description": "Get current user's Spotify profile information including display name, followers, and country.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_top_tracks",
                "description": "Get user's top Spotify tracks for a given time range.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "time_range": {
                            "type": "string",
                            "enum": ["long_term", "medium_term", "short_term"],
                            "description": "Time range: 'long_term' (several years), 'medium_term' (6 months), 'short_term' (4 weeks)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of tracks to return (1-50)",
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_recent_tracks",
                "description": "Get user's recently played Spotify tracks.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of recent tracks to return (1-50)",
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_top_artists",
                "description": "Get user's top Spotify artists for a given time range.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "time_range": {
                            "type": "string",
                            "enum": ["long_term", "medium_term", "short_term"],
                            "description": "Time range: 'long_term' (several years), 'medium_term' (6 months), 'short_term' (4 weeks)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of artists to return (1-50)",
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_favorite_genres",
                "description": "Get user's favorite music genres based on their top artists.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of genres to return",
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": []
                }
            }
        ]

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a SpotifyClient tool and return the result as JSON."""
        try:
            if tool_name == "get_current_user_profile":
                result = self.spotify_client.get_current_user_profile()
            elif tool_name == "get_top_tracks":
                result = self.spotify_client.get_top_tracks(
                    time_range=tool_input.get("time_range", "medium_term"),
                    limit=tool_input.get("limit", 5)
                )
            elif tool_name == "get_recent_tracks":
                result = self.spotify_client.get_recent_tracks(
                    limit=tool_input.get("limit", 5)
                )
            elif tool_name == "get_top_artists":
                result = self.spotify_client.get_top_artists(
                    time_range=tool_input.get("time_range", "medium_term"),
                    limit=tool_input.get("limit", 5)
                )
            elif tool_name == "get_favorite_genres":
                result = self.spotify_client.get_favorite_genres(
                    limit=tool_input.get("limit", 5)
                )
            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})

            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def run(self, prompt: str) -> str:
        """Execute the agent with a user prompt using Claude API with tool use."""
        messages = [
            {"role": "user", "content": prompt}
        ]

        system_prompt = self.system_prompt or (
            "You are a helpful Spotify assistant. Use the available tools to help users "
            "explore their Spotify listening habits, top tracks, artists, and genres. "
            "Provide insightful analysis and recommendations based on the data."
        )

        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                tools=self._create_tools(),
                messages=messages
            )

            # Check if Claude is done (no more tool calls)
            if response.stop_reason == "end_turn":
                # Extract final text response
                for block in response.content:
                    if block.type == "text":
                        return block.text
                return "No response generated."

            # If Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Add assistant's response to messages
                messages.append({"role": "assistant", "content": response.content})

                # Execute tools and collect results
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_result = self._execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": tool_result
                        })

                # Add tool results as user message
                messages.append({"role": "user", "content": tool_results})
            else:
                # Unexpected stop reason, return what we have
                for block in response.content:
                    if block.type == "text":
                        return block.text
                return "Unexpected response from model."

    
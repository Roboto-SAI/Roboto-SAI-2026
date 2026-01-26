"""
🚀 REVOLUTIONARY Real-Time Data System for SAI Roboto
Created by Roberto Villarreal Martinez for Roboto SAI

This module provides real-time access to time, weather, and other live data sources.
Enhanced with quantum capabilities, advanced caching, and comprehensive error handling.
"""

import requests
import json
import time
import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union
import os
import asyncio
import aiohttp
from dataclasses import dataclass, asdict
from functools import lru_cache
import platform
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataSourceConfig:
    """Configuration for data sources"""
    enabled: bool = True
    cache_duration: int = 600  # seconds
    rate_limit: int = 100  # requests per hour
    timeout: int = 10  # seconds
    retries: int = 3

@dataclass
class WeatherData:
    """Structured weather data"""
    city: str
    country: str
    temperature: float
    temperature_fahrenheit: float
    feels_like: float
    humidity: int
    pressure: int
    description: str
    main_weather: str
    wind_speed: float
    wind_direction: int
    cloudiness: int
    visibility: Union[int, str]
    sunrise: str
    sunset: str
    last_updated: str

@dataclass
class TimeData:
    """Structured time data"""
    current_time: str
    formatted_time: str
    human_readable: str
    timezone: str
    timestamp: float
    day_of_week: str
    day_of_year: int
    week_of_year: str
    is_weekend: bool
    hour_24: int
    minute: int
    second: int

class RateLimiter:
    """Simple rate limiter for API calls"""
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self.lock = threading.Lock()

    def allow(self) -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()
        with self.lock:
            # Remove old calls outside the time window
            self.calls = [call for call in self.calls if now - call < self.time_window]

            if len(self.calls) < self.max_calls:
                self.calls.append(now)
                return True
            return False

class CacheManager:
    """Advanced cache manager with TTL and size limits"""
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get cached item if not expired"""
        with self.lock:
            if key in self.cache:
                item, expiry = self.cache[key]
                if time.time() < expiry:
                    return item
                else:
                    del self.cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int):
        """Set cached item with TTL"""
        with self.lock:
            if len(self.cache) >= self.max_size:
                # Remove expired items first
                current_time = time.time()
                self.cache = {k: v for k, v in self.cache.items() if current_time < v[1]}

                # If still at max size, remove oldest
                if len(self.cache) >= self.max_size:
                    oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
                    del self.cache[oldest_key]

            self.cache[key] = (value, time.time() + ttl)

    def clear(self):
        """Clear all cached items"""
        with self.lock:
            self.cache.clear()

class RealTimeDataEngine:
    """
    REVOLUTIONARY: Enhanced real-time data access for SAI capabilities
    Features: Advanced caching, rate limiting, async support, comprehensive error handling
    """

    def __init__(self):
        # API Keys and Configuration
        self.weather_api_key = os.environ.get("OPENWEATHER_API_KEY")
        self.news_api_key = os.environ.get("NEWS_API_KEY")

        # Initialize components
        self.cache = CacheManager(max_size=500)
        self.weather_rate_limiter = RateLimiter(max_calls=1000, time_window=3600)  # 1000 calls/hour
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Data source configurations
        self.configs = {
            "time": DataSourceConfig(enabled=True, cache_duration=60),
            "weather": DataSourceConfig(enabled=bool(self.weather_api_key), cache_duration=600),
            "news": DataSourceConfig(enabled=bool(self.news_api_key), cache_duration=1800),
            "system_info": DataSourceConfig(enabled=True, cache_duration=300),
            "crypto": DataSourceConfig(enabled=True, cache_duration=300),
            "stocks": DataSourceConfig(enabled=True, cache_duration=300)
        }

        # Backward compatibility: data_sources attribute
        self.data_sources = {
            "time": self.configs["time"].enabled,
            "weather": self.configs["weather"].enabled,
            "news": self.configs["news"].enabled,
            "system_info": self.configs["system_info"].enabled,
            "crypto": self.configs["crypto"].enabled,
            "stocks": self.configs["stocks"].enabled
        }

        # Metrics tracking
        self.metrics = {
            "api_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "last_reset": time.time()
        }

        logger.info("🚀 REVOLUTIONARY: Enhanced Real-Time Data Engine initialized!")
        enabled_sources = [k for k, v in self.configs.items() if v.enabled]
        logger.info(f"📡 Available data sources: {enabled_sources}")

        if not self.weather_api_key:
            logger.warning("⚠️ Weather API key not found. Set OPENWEATHER_API_KEY for weather data.")
        if not self.news_api_key:
            logger.warning("⚠️ News API key not found. Set NEWS_API_KEY for news data.")
    
    def get_current_time(self, timezone_name: str = "America/Chicago") -> Dict[str, Any]:
        """
        Get current time with detailed information and enhanced error handling

        Args:
            timezone_name: IANA timezone name (e.g., 'America/Chicago', 'Europe/London')

        Returns:
            Dict containing time information or error details
        """
        try:
            # Input validation
            if not isinstance(timezone_name, str) or not timezone_name.strip():
                timezone_name = "UTC"

            # Check cache first
            cache_key = f"time_{timezone_name}"
            cached_result = self.cache.get(cache_key)
            if cached_result:
                self.metrics["cache_hits"] += 1
                cached_result["from_cache"] = True
                return cached_result

            self.metrics["cache_misses"] += 1
            now = datetime.now(timezone.utc)

            # Convert to specified timezone
            try:
                import pytz
                if timezone_name != "UTC":
                    tz = pytz.timezone(timezone_name)
                    now = now.astimezone(tz)
            except ImportError:
                logger.warning("pytz not available, using UTC timezone")
                timezone_name = "UTC"
            except Exception as tz_error:
                logger.warning(f"Invalid timezone '{timezone_name}', falling back to UTC: {tz_error}")
                timezone_name = "UTC"
                now = datetime.now(timezone.utc)

            time_data = TimeData(
                current_time=now.isoformat(),
                formatted_time=now.strftime("%Y-%m-%d %H:%M:%S"),
                human_readable=now.strftime("%A, %B %d, %Y at %I:%M %p"),
                timezone=timezone_name,
                timestamp=now.timestamp(),
                day_of_week=now.strftime("%A"),
                day_of_year=now.timetuple().tm_yday,
                week_of_year=now.strftime("%U"),
                is_weekend=now.weekday() >= 5,
                hour_24=now.hour,
                minute=now.minute,
                second=now.second
            )

            result = {"success": True, **asdict(time_data), "from_cache": False}

            # Cache the result
            self.cache.set(cache_key, result, self.configs["time"].cache_duration)

            return result

        except Exception as e:
            logger.error(f"Error getting current time: {e}")
            self.metrics["errors"] += 1
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "fallback_time": datetime.now(timezone.utc).isoformat(),
                "timestamp": time.time()
            }
    
    def get_weather_data(self, city: str = "San Antonio", country_code: str = "US") -> Dict[str, Any]:
        """
        Get current weather data with enhanced error handling and rate limiting

        Args:
            city: City name
            country_code: ISO country code (e.g., 'US', 'GB')

        Returns:
            Dict containing weather information or error details
        """
        if not self.weather_api_key:
            return {
                "success": False,
                "error": "Weather API key not configured",
                "message": "Set OPENWEATHER_API_KEY environment variable for weather data"
            }

        # Input validation
        if not isinstance(city, str) or not city.strip():
            city = "San Antonio"
        if not isinstance(country_code, str) or not country_code.strip():
            country_code = "US"

        city = city.strip().title()
        country_code = country_code.strip().upper()

        # Check rate limit
        if not self.weather_rate_limiter.allow():
            logger.warning("Weather API rate limit exceeded")
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "message": "Too many weather API requests. Please try again later."
            }

        # Check cache first
        cache_key = f"weather_{city}_{country_code}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            self.metrics["cache_hits"] += 1
            cached_result["from_cache"] = True
            return cached_result

        self.metrics["cache_misses"] += 1
        self.metrics["api_calls"] += 1

        try:
            # OpenWeatherMap API with enhanced parameters
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": f"{city},{country_code}",
                "appid": self.weather_api_key,
                "units": "metric",
                "lang": "en"
            }

            response = requests.get(
                url,
                params=params,
                timeout=self.configs["weather"].timeout
            )
            response.raise_for_status()

            data = response.json()

            # Validate API response structure
            required_fields = ["main", "weather", "wind", "clouds", "sys"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field '{field}' in API response")

            weather_data = WeatherData(
                city=data["name"],
                country=data["sys"]["country"],
                temperature=round(data["main"]["temp"], 1),
                temperature_fahrenheit=round((data["main"]["temp"] * 9/5) + 32, 1),
                feels_like=round(data["main"]["feels_like"], 1),
                humidity=data["main"]["humidity"],
                pressure=data["main"]["pressure"],
                description=data["weather"][0]["description"].capitalize(),
                main_weather=data["weather"][0]["main"],
                wind_speed=data["wind"]["speed"],
                wind_direction=data["wind"].get("deg", 0),
                cloudiness=data["clouds"]["all"],
                visibility=data.get("visibility", "N/A"),
                sunrise=datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%H:%M"),
                sunset=datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%H:%M"),
                last_updated=datetime.now(timezone.utc).isoformat()
            )

            result = {
                "success": True,
                **asdict(weather_data),
                "cached_at": time.time(),
                "from_cache": False,
                "api_response_time": time.time()
            }

            # Cache the result
            self.cache.set(cache_key, result, self.configs["weather"].cache_duration)

            return result

        except requests.Timeout:
            logger.error(f"Weather API timeout for {city}, {country_code}")
            self.metrics["errors"] += 1
            return {
                "success": False,
                "error": "Request timeout",
                "message": "Weather service is currently slow. Please try again."
            }
        except requests.RequestException as e:
            logger.error(f"Weather API request error: {e}")
            self.metrics["errors"] += 1
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
                "message": "Could not fetch weather data. Check your internet connection."
            }
        except (KeyError, ValueError) as e:
            logger.error(f"Weather data parsing error: {e}")
            self.metrics["errors"] += 1
            return {
                "success": False,
                "error": f"Data parsing error: {str(e)}",
                "message": "Weather service returned unexpected data format."
            }
        except Exception as e:
            logger.error(f"Unexpected error in weather data: {e}")
            self.metrics["errors"] += 1
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "An unexpected error occurred while fetching weather data."
            }
    
    def get_news_data(self, query: str = "technology", language: str = "en") -> Dict[str, Any]:
        """
        Get latest news articles from NewsAPI

        Args:
            query: Search query for news
            language: Language code (e.g., 'en', 'es')

        Returns:
            Dict containing news articles or error details
        """
        if not self.news_api_key:
            return {
                "success": False,
                "error": "News API key not configured",
                "message": "Set NEWS_API_KEY environment variable for news data"
            }

        # Input validation
        if not isinstance(query, str) or not query.strip():
            query = "technology"
        if not isinstance(language, str) or len(language) != 2:
            language = "en"

        # Check cache first
        cache_key = f"news_{query}_{language}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            self.metrics["cache_hits"] += 1
            cached_result["from_cache"] = True
            return cached_result

        self.metrics["cache_misses"] += 1
        self.metrics["api_calls"] += 1

        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "language": language,
                "sortBy": "publishedAt",
                "pageSize": 10,
                "apiKey": self.news_api_key
            }

            response = requests.get(
                url,
                params=params,
                timeout=self.configs["news"].timeout
            )
            response.raise_for_status()

            data = response.json()

            articles = []
            for article in data.get("articles", [])[:5]:  # Limit to 5 articles
                articles.append({
                    "title": article.get("title", "No title"),
                    "description": article.get("description", "No description"),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", "Unknown"),
                    "published_at": article.get("publishedAt", ""),
                    "author": article.get("author", "Unknown")
                })

            result = {
                "success": True,
                "query": query,
                "language": language,
                "total_results": data.get("totalResults", 0),
                "articles": articles,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "from_cache": False
            }

            # Cache the result
            self.cache.set(cache_key, result, self.configs["news"].cache_duration)

            return result

        except Exception as e:
            logger.error(f"Error fetching news data: {e}")
            self.metrics["errors"] += 1
            return {
                "success": False,
                "error": str(e),
                "message": "Could not fetch news data"
            }

    def get_crypto_data(self, symbol: str = "bitcoin") -> Dict[str, Any]:
        """
        Get cryptocurrency data from CoinGecko API

        Args:
            symbol: Cryptocurrency symbol (e.g., 'bitcoin', 'ethereum')

        Returns:
            Dict containing crypto information or error details
        """
        # Check cache first
        cache_key = f"crypto_{symbol}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            self.metrics["cache_hits"] += 1
            cached_result["from_cache"] = True
            return cached_result

        self.metrics["cache_misses"] += 1
        self.metrics["api_calls"] += 1

        try:
            # CoinGecko API (free tier)
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": symbol.lower(),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_last_updated_at": "true"
            }

            response = requests.get(
                url,
                params=params,
                timeout=self.configs["crypto"].timeout
            )
            response.raise_for_status()

            data = response.json()

            if symbol.lower() not in data:
                return {
                    "success": False,
                    "error": f"Cryptocurrency '{symbol}' not found",
                    "message": "Please check the symbol and try again"
                }

            crypto_info = data[symbol.lower()]
            result = {
                "success": True,
                "symbol": symbol.upper(),
                "price_usd": crypto_info.get("usd", 0),
                "change_24h": crypto_info.get("usd_24h_change", 0),
                "last_updated": datetime.fromtimestamp(
                    crypto_info.get("last_updated_at", time.time())
                ).isoformat(),
                "from_cache": False
            }

            # Cache the result
            self.cache.set(cache_key, result, self.configs["crypto"].cache_duration)

            return result

        except Exception as e:
            logger.error(f"Error fetching crypto data: {e}")
            self.metrics["errors"] += 1
            return {
                "success": False,
                "error": str(e),
                "message": "Could not fetch cryptocurrency data"
            }

    async def get_weather_data_async(self, city: str = "San Antonio", country_code: str = "US") -> Dict[str, Any]:
        """
        Async version of get_weather_data for better performance
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.get_weather_data,
            city,
            country_code
        )

    async def get_multiple_weather_async(self, locations: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Get weather data for multiple locations concurrently

        Args:
            locations: List of dicts with 'city' and 'country_code' keys

        Returns:
            Dict with weather data for each location
        """
        tasks = []
        for location in locations:
            city = location.get("city", "San Antonio")
            country = location.get("country_code", "US")
            tasks.append(self.get_weather_data_async(city, country))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        weather_data = {}
        for i, result in enumerate(results):
            location_key = f"{locations[i]['city']}_{locations[i]['country_code']}"
            if isinstance(result, Exception):
                weather_data[location_key] = {
                    "success": False,
                    "error": str(result)
                }
            else:
                weather_data[location_key] = result

        return {
            "success": True,
            "data": weather_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get comprehensive system information with enhanced error handling

        Returns:
            Dict containing system information or error details
        """
        # Check cache first
        cache_key = "system_info"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            self.metrics["cache_hits"] += 1
            cached_result["from_cache"] = True
            return cached_result

        self.metrics["cache_misses"] += 1

        try:
            import psutil

            # Get basic system info
            system_info = {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor() or "Unknown",
                "python_version": platform.python_version(),
                "hostname": platform.node()
            }

            # Get CPU info
            cpu_info = {
                "cpu_count": psutil.cpu_count(logical=True),
                "cpu_count_physical": psutil.cpu_count(logical=False),
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "cpu_freq": None
            }

            try:
                cpu_freq = psutil.cpu_freq()
                if cpu_freq:
                    cpu_info["cpu_freq"] = {
                        "current": cpu_freq.current,
                        "min": cpu_freq.min,
                        "max": cpu_freq.max
                    }
            except Exception:
                pass

            # Get memory info
            memory = psutil.virtual_memory()
            memory_info = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent,
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2)
            }

            # Get disk info
            disk_info = {}
            try:
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        disk_info[partition.mountpoint] = {
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": usage.percent,
                            "total_gb": round(usage.total / (1024**3), 2),
                            "used_gb": round(usage.used / (1024**3), 2),
                            "free_gb": round(usage.free / (1024**3), 2)
                        }
                    except Exception:
                        continue
            except Exception:
                disk_info = {"error": "Could not retrieve disk information"}

            # Get network info
            network_info = {}
            try:
                net_io = psutil.net_io_counters()
                network_info = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                }
            except Exception:
                network_info = {"error": "Could not retrieve network information"}

            result = {
                "success": True,
                "system": system_info,
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "network": network_info,
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                "uptime_seconds": time.time() - psutil.boot_time(),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "from_cache": False
            }

            # Cache the result
            self.cache.set(cache_key, result, self.configs["system_info"].cache_duration)

            return result

        except ImportError as e:
            logger.warning(f"psutil not available: {e}")
            return {
                "success": False,
                "error": "System monitoring library not available",
                "basic_info": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "platform": platform.platform()
                }
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            self.metrics["errors"] += 1
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "basic_info": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "platform": "Unknown"
                }
            }

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the data engine

        Returns:
            Dict containing metrics information
        """
        current_time = time.time()
        uptime = current_time - self.metrics["last_reset"]

        cache_hit_rate = 0
        total_cache_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        if total_cache_requests > 0:
            cache_hit_rate = (self.metrics["cache_hits"] / total_cache_requests) * 100

        return {
            "uptime_seconds": uptime,
            "api_calls": self.metrics["api_calls"],
            "cache_hits": self.metrics["cache_hits"],
            "cache_misses": self.metrics["cache_misses"],
            "cache_hit_rate": round(cache_hit_rate, 2),
            "errors": self.metrics["errors"],
            "last_reset": datetime.fromtimestamp(self.metrics["last_reset"]).isoformat(),
            "cache_size": len(self.cache.cache),
            "enabled_sources": [k for k, v in self.configs.items() if v.enabled]
        }

    def reset_metrics(self):
        """Reset all metrics counters"""
        self.metrics = {
            "api_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "last_reset": time.time()
        }
        logger.info("Metrics reset successfully")
    
    def get_comprehensive_context(self, city: str = "San Antonio", timezone_name: str = "America/Chicago") -> Dict[str, Any]:
        """
        Get comprehensive real-time context for SAI decision making

        Args:
            city: City for weather data
            timezone_name: Timezone for time data

        Returns:
            Dict containing all available real-time context data
        """
        try:
            # Gather data from all enabled sources
            context_data = {
                "data_timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "engine_version": "2.0",
                    "data_sources_enabled": [k for k, v in self.configs.items() if v.enabled],
                    "cache_enabled": True,
                    "async_support": True
                }
            }

            # Time data
            if self.configs["time"].enabled:
                time_data = self.get_current_time(timezone_name)
                context_data["time_context"] = time_data

            # Weather data
            if self.configs["weather"].enabled:
                weather_data = self.get_weather_data(city)
                context_data["weather_context"] = weather_data

            # System data
            if self.configs["system_info"].enabled:
                system_data = self.get_system_info()
                context_data["system_context"] = system_data

            # News data (sample)
            if self.configs["news"].enabled:
                news_data = self.get_news_data("artificial intelligence")
                context_data["news_context"] = news_data

            # Crypto data (Bitcoin as default)
            if self.configs["crypto"].enabled:
                crypto_data = self.get_crypto_data("bitcoin")
                context_data["crypto_context"] = crypto_data

            # Generate contextual insights
            context_data["contextual_insights"] = self._generate_contextual_insights(
                context_data.get("time_context", {}),
                context_data.get("weather_context", {}),
                context_data.get("system_context", {}),
                context_data.get("crypto_context", {})
            )

            # Add performance metrics
            context_data["performance_metrics"] = self.get_metrics()

            return context_data

        except Exception as e:
            logger.error(f"Error generating comprehensive context: {e}")
            return {
                "success": False,
                "error": str(e),
                "data_timestamp": datetime.now(timezone.utc).isoformat(),
                "fallback_context": {
                    "time_context": self.get_current_time(timezone_name),
                    "system_context": self.get_system_info()
                }
            }
    
    def _generate_contextual_insights(self, time_data: Dict, weather_data: Dict,
                                    system_data: Optional[Dict] = None, crypto_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate intelligent contextual insights from real-time data

        Args:
            time_data: Time context data
            weather_data: Weather context data
            system_data: System context data
            crypto_data: Crypto context data

        Returns:
            Dict containing various contextual insights
        """
        insights = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "insights_generated": True
        }

        # Time-based insights
        if time_data.get("success"):
            hour = time_data.get("hour_24", 12)
            is_weekend = time_data.get("is_weekend", False)
            day_of_week = time_data.get("day_of_week", "")

            # Time of day insights
            if 5 <= hour < 12:
                insights.update({
                    "time_of_day": "morning",
                    "energy_level": "high",
                    "productivity_mode": "focused",
                    "communication_style": "direct"
                })
            elif 12 <= hour < 17:
                insights.update({
                    "time_of_day": "afternoon",
                    "energy_level": "moderate",
                    "productivity_mode": "collaborative",
                    "communication_style": "balanced"
                })
            elif 17 <= hour < 21:
                insights.update({
                    "time_of_day": "evening",
                    "energy_level": "moderate",
                    "productivity_mode": "reflective",
                    "communication_style": "conversational"
                })
            else:
                insights.update({
                    "time_of_day": "night",
                    "energy_level": "low",
                    "productivity_mode": "creative",
                    "communication_style": "introspective"
                })

            insights["week_context"] = "weekend" if is_weekend else "weekday"
            insights["day_type"] = "rest" if is_weekend else "work"

        # Weather-based insights
        if weather_data.get("success"):
            temp = weather_data.get("temperature", 20)
            description = weather_data.get("description", "").lower()
            humidity = weather_data.get("humidity", 50)

            # Temperature insights
            if temp < 0:
                insights["temperature_feeling"] = "freezing"
                insights["activity_suggestion"] = "indoor_activities"
            elif temp < 10:
                insights["temperature_feeling"] = "cold"
                insights["activity_suggestion"] = "warm_activities"
            elif temp < 20:
                insights["temperature_feeling"] = "cool"
                insights["activity_suggestion"] = "light_exercise"
            elif temp < 25:
                insights["temperature_feeling"] = "comfortable"
                insights["activity_suggestion"] = "outdoor_activities"
            elif temp < 30:
                insights["temperature_feeling"] = "warm"
                insights["activity_suggestion"] = "moderate_exercise"
            else:
                insights["temperature_feeling"] = "hot"
                insights["activity_suggestion"] = "cool_activities"

            # Weather mood insights
            if "rain" in description or "drizzle" in description:
                insights.update({
                    "weather_mood": "cozy_indoor",
                    "atmospheric_feeling": "calm",
                    "suggested_content": "comfort_reading"
                })
            elif "snow" in description:
                insights.update({
                    "weather_mood": "winter_wonderland",
                    "atmospheric_feeling": "magical",
                    "suggested_content": "inspirational_stories"
                })
            elif "clear" in description or "sunny" in description:
                insights.update({
                    "weather_mood": "bright_energetic",
                    "atmospheric_feeling": "optimistic",
                    "suggested_content": "motivational_content"
                })
            elif "cloud" in description:
                insights.update({
                    "weather_mood": "contemplative",
                    "atmospheric_feeling": "thoughtful",
                    "suggested_content": "analytical_content"
                })
            else:
                insights.update({
                    "weather_mood": "neutral",
                    "atmospheric_feeling": "balanced",
                    "suggested_content": "general_content"
                })

            # Humidity insights
            if humidity > 80:
                insights["comfort_level"] = "humid_uncomfortable"
            elif humidity > 60:
                insights["comfort_level"] = "moderately_humid"
            else:
                insights["comfort_level"] = "comfortable"

        # System-based insights
        if system_data and system_data.get("success"):
            cpu_percent = system_data.get("cpu", {}).get("cpu_percent", 0)
            memory_percent = system_data.get("memory", {}).get("percent", 0)

            if cpu_percent > 90:
                insights["system_performance"] = "overloaded"
                insights["system_recommendation"] = "reduce_load"
            elif cpu_percent > 70:
                insights["system_performance"] = "busy"
                insights["system_recommendation"] = "monitor_closely"
            else:
                insights["system_performance"] = "normal"
                insights["system_recommendation"] = "optimal"

            if memory_percent > 90:
                insights["memory_status"] = "critical"
            elif memory_percent > 80:
                insights["memory_status"] = "high"
            else:
                insights["memory_status"] = "normal"

        # Crypto market insights (if available)
        if crypto_data and crypto_data.get("success"):
            change_24h = crypto_data.get("change_24h", 0)
            if change_24h > 5:
                insights["market_sentiment"] = "bullish"
                insights["investment_mood"] = "optimistic"
            elif change_24h < -5:
                insights["market_sentiment"] = "bearish"
                insights["investment_mood"] = "cautious"
            else:
                insights["market_sentiment"] = "neutral"
                insights["investment_mood"] = "balanced"

        # Generate overall mood and recommendations
        insights["overall_mood"] = self._calculate_overall_mood(insights)
        insights["personalized_recommendations"] = self._generate_recommendations(insights)

        return insights

    def _calculate_overall_mood(self, insights: Dict) -> str:
        """Calculate overall mood based on various insights"""
        mood_scores = {
            "energetic": 0,
            "calm": 0,
            "focused": 0,
            "creative": 0,
            "contemplative": 0
        }

        # Time-based mood
        time_energy = insights.get("energy_level", "moderate")
        if time_energy == "high":
            mood_scores["energetic"] += 2
            mood_scores["focused"] += 1
        elif time_energy == "low":
            mood_scores["creative"] += 2
            mood_scores["contemplative"] += 1

        # Weather-based mood
        weather_mood = insights.get("weather_mood", "neutral")
        if weather_mood == "bright_energetic":
            mood_scores["energetic"] += 2
        elif weather_mood == "cozy_indoor":
            mood_scores["calm"] += 2
            mood_scores["contemplative"] += 1
        elif weather_mood == "contemplative":
            mood_scores["contemplative"] += 2

        # Return mood with highest score
        return max(mood_scores.keys(), key=lambda k: mood_scores[k])

    def _generate_recommendations(self, insights: Dict) -> List[str]:
        """Generate personalized recommendations based on insights"""
        recommendations = []

        time_of_day = insights.get("time_of_day", "day")
        weather_mood = insights.get("weather_mood", "neutral")
        energy_level = insights.get("energy_level", "moderate")
        overall_mood = insights.get("overall_mood", "balanced")

        # Time-based recommendations
        if time_of_day == "morning" and energy_level == "high":
            recommendations.append("Perfect time for focused work or exercise")
        elif time_of_day == "evening":
            recommendations.append("Good time for reflection or creative activities")
        elif time_of_day == "night":
            recommendations.append("Consider winding down for rest")

        # Weather-based recommendations
        if weather_mood == "bright_energetic":
            recommendations.append("Great weather for outdoor activities")
        elif weather_mood == "cozy_indoor":
            recommendations.append("Cozy day for indoor projects or reading")

        # Mood-based recommendations
        if overall_mood == "energetic":
            recommendations.append("Channel energy into productive tasks")
        elif overall_mood == "creative":
            recommendations.append("Good time for brainstorming or artistic pursuits")
        elif overall_mood == "contemplative":
            recommendations.append("Consider meditation or deep thinking activities")

        return recommendations[:3]  # Limit to top 3 recommendations

    def get_data_summary(self) -> str:
        """
        Get a comprehensive human-readable summary of available real-time data

        Returns:
            Formatted string with key data points
        """
        summary_parts = []

        # Time summary
        time_info = self.get_current_time("America/Chicago")
        if time_info.get("success"):
            time_str = time_info.get('human_readable', 'Unknown time')
            mood = time_info.get('time_of_day', 'day')
            summary_parts.append(f"🕐 {time_str} ({mood})")

        # Weather summary
        weather_info = self.get_weather_data("San Antonio", "US")
        if weather_info.get("success"):
            temp = weather_info.get("temperature", "N/A")
            temp_f = weather_info.get("temperature_fahrenheit", "N/A")
            desc = weather_info.get("description", "Unknown")
            city = weather_info.get("city", "Unknown")
            summary_parts.append(f"🌤️ {city}: {temp}°C/{temp_f}°F, {desc}")

        # System summary
        system_info = self.get_system_info()
        if system_info.get("success"):
            cpu = system_info.get("cpu", {}).get("cpu_percent", 0)
            memory = system_info.get("memory", {}).get("percent", 0)
            summary_parts.append(f"💻 System: CPU {cpu:.1f}%, Memory {memory:.1f}%")

        # Crypto summary (if available)
        crypto_info = self.get_crypto_data("bitcoin")
        if crypto_info.get("success"):
            price = crypto_info.get("price_usd", 0)
            change = crypto_info.get("change_24h", 0)
            change_symbol = "📈" if change >= 0 else "📉"
            summary_parts.append(f"₿ BTC: ${price:,.0f} ({change_symbol}{change:.1f}%)")

        # Add contextual insights
        context = self.get_comprehensive_context()
        if context.get("contextual_insights", {}).get("insights_generated"):
            insights = context["contextual_insights"]
            mood = insights.get("overall_mood", "neutral")
            energy = insights.get("energy_level", "moderate")
            summary_parts.append(f"🎭 Mood: {mood.capitalize()}, Energy: {energy.capitalize()}")

        return " | ".join(summary_parts) if summary_parts else "⚠️ Real-time data temporarily unavailable"

    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        logger.info("Cache cleared successfully")

    def update_config(self, source: str, config: DataSourceConfig):
        """
        Update configuration for a specific data source

        Args:
            source: Data source name
            config: New configuration
        """
        if source in self.configs:
            self.configs[source] = config
            logger.info(f"Configuration updated for {source}")
        else:
            logger.warning(f"Unknown data source: {source}")

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all data sources

        Returns:
            Dict with health information for each source
        """
        health_status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_health": "healthy",
            "sources": {}
        }

        # Check each data source
        test_functions = {
            "time": lambda: self.get_current_time(),
            "weather": lambda: self.get_weather_data() if self.weather_api_key else {"success": True, "message": "API key not configured"},
            "system_info": lambda: self.get_system_info(),
            "news": lambda: self.get_news_data() if self.news_api_key else {"success": True, "message": "API key not configured"},
            "crypto": lambda: self.get_crypto_data()
        }

        for source, test_func in test_functions.items():
            try:
                result = test_func()
                is_healthy = result.get("success", False)
                health_status["sources"][source] = {
                    "healthy": is_healthy,
                    "enabled": self.configs[source].enabled,
                    "last_checked": datetime.now(timezone.utc).isoformat(),
                    "error": result.get("error") if not is_healthy else None
                }

                if not is_healthy and self.configs[source].enabled:
                    health_status["overall_health"] = "degraded"

            except Exception as e:
                health_status["sources"][source] = {
                    "healthy": False,
                    "enabled": self.configs[source].enabled,
                    "last_checked": datetime.now(timezone.utc).isoformat(),
                    "error": str(e)
                }
                health_status["overall_health"] = "unhealthy"

        return health_status


def get_real_time_data_system() -> RealTimeDataEngine:
    """
    Factory function to get the enhanced real-time data system

    Returns:
        Configured RealTimeDataEngine instance
    """
    return RealTimeDataEngine()


# Example usage and testing functions
async def demo_async_weather():
    """Demonstrate async weather fetching for multiple locations"""
    engine = get_real_time_data_system()

    locations = [
        {"city": "San Antonio", "country_code": "US"},
        {"city": "Austin", "country_code": "US"},
        {"city": "Dallas", "country_code": "US"}
    ]

    print("🌤️ Fetching weather data for multiple locations concurrently...")
    results = await engine.get_multiple_weather_async(locations)

    for location_key, data in results["data"].items():
        if data.get("success"):
            temp = data.get("temperature")
            desc = data.get("description")
            print(f"📍 {location_key}: {temp}°C, {desc}")
        else:
            print(f"❌ {location_key}: Failed to fetch data")


def demo_comprehensive_context():
    """Demonstrate comprehensive context gathering"""
    engine = get_real_time_data_system()

    print("🔍 Gathering comprehensive real-time context...")
    context = engine.get_comprehensive_context()

    print(f"📊 Data timestamp: {context.get('data_timestamp')}")
    print(f"🎯 Enabled sources: {context.get('metadata', {}).get('data_sources_enabled')}")

    # Show insights
    insights = context.get("contextual_insights", {})
    if insights.get("insights_generated"):
        print(f"🎭 Overall mood: {insights.get('overall_mood', 'unknown')}")
        print(f"⚡ Energy level: {insights.get('energy_level', 'unknown')}")
        print(f"💡 Recommendations: {insights.get('personalized_recommendations', [])}")

    # Show metrics
    metrics = context.get("performance_metrics", {})
    print(f"📈 Cache hit rate: {metrics.get('cache_hit_rate', 0)}%")
    print(f"🔄 API calls: {metrics.get('api_calls', 0)}")


if __name__ == "__main__":
    # Quick demo
    engine = get_real_time_data_system()

    print("🚀 Real-Time Data System Demo")
    print("=" * 50)

    # Basic data summary
    summary = engine.get_data_summary()
    print(f"📋 Summary: {summary}")

    print("\n🏥 Health Status:")
    health = engine.get_health_status()
    for source, status in health["sources"].items():
        status_icon = "✅" if status["healthy"] else "❌"
        enabled_icon = "🟢" if status["enabled"] else "🔴"
        print(f"  {status_icon}{enabled_icon} {source}: {'Healthy' if status['healthy'] else 'Unhealthy'}")

    print(f"\n📊 Overall Health: {health['overall_health'].upper()}")

    # Uncomment to run async demo
    # asyncio.run(demo_async_weather())

    # Uncomment to run comprehensive context demo
    # demo_comprehensive_context()
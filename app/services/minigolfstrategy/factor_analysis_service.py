"""
Golf Course Factor Analysis Service
AI-powered analysis for optimal golf course timing decisions
"""
import asyncio
import httpx
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from app.core.config import settings

logger = logging.getLogger(__name__)

class WeatherService:
    """Weather data service for golf course analysis using OpenWeatherMap free APIs"""
    
    def __init__(self):
        self.openweather_api_key = settings.openweather_api_key
        self.current_weather_url = "https://api.openweathermap.org/data/2.5/weather"
        self.forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
        self.onecall_url = "https://api.openweathermap.org/data/3.0/onecall"
    
    async def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather conditions using Current Weather API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.current_weather_url,
                    params={
                        "lat": lat,
                        "lon": lon,
                        "appid": self.openweather_api_key,
                        "units": "imperial"
                    }
                )
                response.raise_for_status()
                weather_data = response.json()
                logger.debug(f"OpenWeatherMap Current Weather API Response: {json.dumps(weather_data, indent=2)}")
                return weather_data
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return {}
    
    async def get_forecast(self, lat: float, lon: float, days: int = 5) -> Dict[str, Any]:
        """Get weather forecast using 5-day forecast API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.forecast_url,
                    params={
                        "lat": lat,
                        "lon": lon,
                        "appid": self.openweather_api_key,
                        "units": "imperial",
                        "cnt": days * 8  # 8 forecasts per day (every 3 hours)
                    }
                )
                response.raise_for_status()
                forecast_data = response.json()
                logger.info(f"OpenWeatherMap Forecast API Response: {json.dumps(forecast_data, indent=2)}")
                return forecast_data
        except Exception as e:
            logger.error(f"Weather forecast error: {e}")
            return {}
    
    async def get_onecall_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get comprehensive weather data using One Call API 3.0"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.onecall_url,
                    params={
                        "lat": lat,
                        "lon": lon,
                        "appid": self.openweather_api_key,
                        "units": "imperial",
                        "exclude": "minutely"  # Exclude minutely data to save API calls
                    }
                )
                response.raise_for_status()
                onecall_data = response.json()
                logger.info(f"OpenWeatherMap One Call API Response: {json.dumps(onecall_data, indent=2)}")
                return onecall_data
        except Exception as e:
            logger.error(f"One Call Weather API error: {e}")
            # Fallback to basic weather API
            return await self.get_current_weather(lat, lon)

class GolfCourseFactorAnalyzer:
    """AI-powered factor analysis for golf course timing decisions"""
    
    def __init__(self):
        self.weather_service = WeatherService()
        self.openrouter_api_key = settings.openrouter_api_key
        self.openrouter_url = settings.openrouter_api_url
    
    def calculate_weather_score(self, weather_data: Dict[str, Any]) -> float:
        """Calculate comprehensive weather suitability score (0-100) using OpenWeatherMap data"""
        if not weather_data:
            return 50.0  # Neutral score if no weather data
        
        # Check if this is One Call API format or basic Current Weather API format
        if "current" in weather_data:
            # One Call API format
            current = weather_data.get("current", {})
            hourly = weather_data.get("hourly", [])
            daily = weather_data.get("daily", [])
            alerts = weather_data.get("alerts", [])
            
            # Current conditions
            temp = current.get("temp", 70)
            humidity = current.get("humidity", 50)
            wind_speed = current.get("wind_speed", 5)
            conditions = current.get("weather", [{}])[0].get("main", "Clear")
            uv_index = current.get("uvi", 0)
            visibility = current.get("visibility", 10000)
        else:
            # Basic Current Weather API format
            temp = weather_data.get("main", {}).get("temp", 70)
            humidity = weather_data.get("main", {}).get("humidity", 50)
            wind_speed = weather_data.get("wind", {}).get("speed", 5)
            conditions = weather_data.get("weather", [{}])[0].get("main", "Clear")
            uv_index = 0  # Not available in basic API
            visibility = weather_data.get("visibility", 10000)
            
            # Set empty arrays for One Call API specific data
            hourly = []
            daily = []
            alerts = []
        
        # Calculate current weather score
        current_score = self._calculate_current_weather_score(
            temp, humidity, wind_speed, conditions, uv_index, visibility
        )
        
        # Calculate timing-based score (next 6 hours)
        timing_score = self._calculate_timing_score(hourly)
        
        # Calculate precipitation risk
        precipitation_score = self._calculate_precipitation_score(hourly, daily)
        
        # Calculate multi-day outlook
        outlook_score = self._calculate_outlook_score(daily)
        
        # Check for weather alerts
        alert_penalty = self._calculate_alert_penalty(alerts)
        
        # Weighted average with timing and precipitation considerations
        weather_score = (
            current_score * 0.4 +
            timing_score * 0.25 +
            precipitation_score * 0.2 +
            outlook_score * 0.1 +
            alert_penalty * 0.05
        )
        
        return max(0, min(100, round(weather_score, 1)))
    
    def _calculate_current_weather_score(self, temp: float, humidity: int, wind_speed: float, 
                                       conditions: str, uv_index: float, visibility: int) -> float:
        """Calculate score for current weather conditions"""
        # Temperature score (optimal: 65-80°F)
        if 65 <= temp <= 80:
            temp_score = 100
        elif 55 <= temp < 65 or 80 < temp <= 90:
            temp_score = 80
        elif 45 <= temp < 55 or 90 < temp <= 100:
            temp_score = 60
        else:
            temp_score = 30
        
        # Humidity score (optimal: 40-60%)
        if 40 <= humidity <= 60:
            humidity_score = 100
        elif 30 <= humidity < 40 or 60 < humidity <= 70:
            humidity_score = 80
        else:
            humidity_score = 60
        
        # Wind score (optimal: 0-10 mph)
        if wind_speed <= 10:
            wind_score = 100
        elif wind_speed <= 15:
            wind_score = 80
        elif wind_speed <= 20:
            wind_score = 60
        else:
            wind_score = 30
        
        # Conditions score
        condition_scores = {
            "Clear": 100,
            "Clouds": 90,
            "Mist": 70,
            "Rain": 20,
            "Snow": 10,
            "Thunderstorm": 5
        }
        conditions_score = condition_scores.get(conditions, 50)
        
        # UV Index score (moderate UV is good for golf)
        if 3 <= uv_index <= 6:
            uv_score = 100
        elif 1 <= uv_index < 3 or 6 < uv_index <= 8:
            uv_score = 80
        else:
            uv_score = 60
        
        # Visibility score
        if visibility >= 10000:
            visibility_score = 100
        elif visibility >= 5000:
            visibility_score = 80
        else:
            visibility_score = 60
        
        return (
            temp_score * 0.25 +
            humidity_score * 0.15 +
            wind_score * 0.25 +
            conditions_score * 0.2 +
            uv_score * 0.1 +
            visibility_score * 0.05
        )
    
    def _calculate_timing_score(self, hourly: list) -> float:
        """Calculate score based on weather timing over next 6 hours"""
        if not hourly or len(hourly) < 6:
            return 50.0
        
        scores = []
        for hour_data in hourly[:6]:  # Next 6 hours
            temp = hour_data.get("temp", 70)
            conditions = hour_data.get("weather", [{}])[0].get("main", "Clear")
            wind_speed = hour_data.get("wind_speed", 5)
            pop = hour_data.get("pop", 0)  # Probability of precipitation
            
            # Calculate hourly score
            hour_score = 50  # Base score
            
            # Temperature adjustment
            if 65 <= temp <= 80:
                hour_score += 30
            elif 55 <= temp < 65 or 80 < temp <= 90:
                hour_score += 20
            elif 45 <= temp < 55 or 90 < temp <= 100:
                hour_score += 10
            
            # Wind adjustment
            if wind_speed <= 10:
                hour_score += 10
            elif wind_speed > 20:
                hour_score -= 20
            
            # Precipitation probability penalty
            hour_score -= (pop * 50)  # Reduce score based on rain probability
            
            # Condition adjustment
            if conditions == "Clear":
                hour_score += 10
            elif conditions in ["Rain", "Thunderstorm"]:
                hour_score -= 30
            
            scores.append(max(0, min(100, hour_score)))
        
        return sum(scores) / len(scores)
    
    def _calculate_precipitation_score(self, hourly: list, daily: list) -> float:
        """Calculate score based on precipitation risk"""
        if not hourly:
            return 50.0
        
        # Check next 6 hours for rain
        rain_hours = 0
        total_precipitation = 0
        
        for hour_data in hourly[:6]:
            pop = hour_data.get("pop", 0)
            if pop > 0.3:  # 30% chance or higher
                rain_hours += 1
            if "rain" in hour_data:
                total_precipitation += hour_data["rain"].get("1h", 0)
        
        # Calculate precipitation score
        if rain_hours == 0:
            precip_score = 100
        elif rain_hours <= 2:
            precip_score = 70
        elif rain_hours <= 4:
            precip_score = 40
        else:
            precip_score = 10
        
        # Adjust for precipitation amount
        if total_precipitation > 5:  # Heavy rain
            precip_score *= 0.5
        elif total_precipitation > 2:  # Moderate rain
            precip_score *= 0.7
        
        return precip_score
    
    def _calculate_outlook_score(self, daily: list) -> float:
        """Calculate score based on multi-day weather outlook"""
        if not daily or len(daily) < 3:
            return 50.0
        
        scores = []
        for day_data in daily[:3]:  # Next 3 days
            temp = day_data.get("temp", {})
            conditions = day_data.get("weather", [{}])[0].get("main", "Clear")
            pop = day_data.get("pop", 0)
            
            # Get average temperature
            avg_temp = (temp.get("min", 70) + temp.get("max", 70)) / 2
            
            day_score = 50
            
            # Temperature scoring
            if 65 <= avg_temp <= 80:
                day_score += 30
            elif 55 <= avg_temp < 65 or 80 < avg_temp <= 90:
                day_score += 20
            
            # Precipitation penalty
            day_score -= (pop * 40)
            
            # Condition adjustment
            if conditions == "Clear":
                day_score += 20
            elif conditions in ["Rain", "Thunderstorm"]:
                day_score -= 30
            
            scores.append(max(0, min(100, day_score)))
        
        return sum(scores) / len(scores)
    
    def _calculate_alert_penalty(self, alerts: list) -> float:
        """Calculate penalty for weather alerts"""
        if not alerts:
            return 0
        
        penalty = 0
        for alert in alerts:
            event = alert.get("event", "").lower()
            if "thunderstorm" in event or "tornado" in event:
                penalty += 50
            elif "rain" in event or "flood" in event:
                penalty += 30
            elif "wind" in event:
                penalty += 20
            else:
                penalty += 10
        
        return min(50, penalty)  # Cap penalty at 50 points
    
    def _extract_detailed_weather_insights(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed weather insights from OpenWeatherMap data"""
        if not weather_data:
            return {"error": "No weather data available"}
        
        # Check if this is One Call API format or basic Current Weather API format
        if "current" in weather_data:
            # One Call API format
            current = weather_data.get("current", {})
            hourly = weather_data.get("hourly", [])
            daily = weather_data.get("daily", [])
            alerts = weather_data.get("alerts", [])
            
            # Current conditions
            current_temp = current.get("temp", 0)
            current_humidity = current.get("humidity", 0)
            current_wind_speed = current.get("wind_speed", 0)
            current_conditions = current.get("weather", [{}])[0].get("description", "Unknown")
            uv_index = current.get("uvi", 0)
            visibility = current.get("visibility", 0)
        else:
            # Basic Current Weather API format
            current_temp = weather_data.get("main", {}).get("temp", 0)
            current_humidity = weather_data.get("main", {}).get("humidity", 0)
            current_wind_speed = weather_data.get("wind", {}).get("speed", 0)
            current_conditions = weather_data.get("weather", [{}])[0].get("description", "Unknown")
            uv_index = 0  # Not available in basic API
            visibility = weather_data.get("visibility", 0)
            
            # Set empty arrays for One Call API specific data
            hourly = []
            daily = []
            alerts = []
        
        # Extract timing insights
        timing_insights = self._get_timing_insights(hourly)
        
        # Extract precipitation insights
        precipitation_insights = self._get_precipitation_insights(hourly, daily)
        
        # Extract temperature trends
        temp_trends = self._get_temperature_trends(hourly, daily)
        
        # Extract wind analysis
        wind_analysis = self._get_wind_analysis(hourly)
        
        # Extract alerts summary
        alerts_summary = self._get_alerts_summary(alerts)
        
        return {
            "current": {
                "temperature": round(current_temp, 1),
                "humidity": current_humidity,
                "wind_speed": round(current_wind_speed * 2.237, 1),  # Convert m/s to mph
                "conditions": current_conditions,
                "uv_index": uv_index,
                "visibility": visibility / 1000 if visibility else 0  # Convert to km
            },
            "timing": timing_insights,
            "precipitation": precipitation_insights,
            "temperature_trends": temp_trends,
            "wind_analysis": wind_analysis,
            "alerts": alerts_summary,
            "best_times": self._find_best_playing_times(hourly),
            "weather_summary": self._generate_weather_summary(current, hourly, daily)
        }
    
    def _get_timing_insights(self, hourly: list) -> Dict[str, Any]:
        """Get insights about weather timing over next 6 hours"""
        if not hourly or len(hourly) < 6:
            return {"error": "Insufficient hourly data"}
        
        insights = {
            "next_6_hours": [],
            "best_hour": None,
            "worst_hour": None,
            "rain_risk": 0
        }
        
        best_score = 0
        worst_score = 100
        rain_hours = 0
        
        for i, hour_data in enumerate(hourly[:6]):
            temp = hour_data.get("temp", 70)
            conditions = hour_data.get("weather", [{}])[0].get("main", "Clear")
            wind_speed = hour_data.get("wind_speed", 5)
            pop = hour_data.get("pop", 0)
            
            # Calculate hour score
            hour_score = 50
            if 65 <= temp <= 80:
                hour_score += 30
            if wind_speed <= 10:
                hour_score += 10
            if conditions == "Clear":
                hour_score += 10
            hour_score -= (pop * 50)
            
            hour_info = {
                "hour": i + 1,
                "time": hour_data.get("dt", 0),
                "temperature": round(temp, 1),
                "conditions": conditions,
                "wind_speed": round(wind_speed * 2.237, 1),
                "rain_probability": round(pop * 100, 1),
                "score": max(0, min(100, hour_score))
            }
            
            insights["next_6_hours"].append(hour_info)
            
            if hour_score > best_score:
                best_score = hour_score
                insights["best_hour"] = hour_info
            
            if hour_score < worst_score:
                worst_score = hour_score
                insights["worst_hour"] = hour_info
            
            if pop > 0.3:
                rain_hours += 1
        
        insights["rain_risk"] = round((rain_hours / 6) * 100, 1)
        return insights
    
    def _get_precipitation_insights(self, hourly: list, daily: list) -> Dict[str, Any]:
        """Get detailed precipitation analysis"""
        if not hourly:
            return {"error": "No hourly data available"}
        
        # Next 6 hours analysis
        rain_hours = 0
        total_precip = 0
        max_precip_hour = 0
        
        for hour_data in hourly[:6]:
            pop = hour_data.get("pop", 0)
            if pop > 0.3:
                rain_hours += 1
            if "rain" in hour_data:
                precip = hour_data["rain"].get("1h", 0)
                total_precip += precip
                if precip > max_precip_hour:
                    max_precip_hour = precip
        
        # Daily analysis
        daily_rain_days = 0
        for day_data in daily[:3]:
            if day_data.get("pop", 0) > 0.3:
                daily_rain_days += 1
        
        return {
            "next_6_hours": {
                "rain_hours": rain_hours,
                "total_precipitation": round(total_precip, 2),
                "max_hourly_precipitation": round(max_precip_hour, 2),
                "rain_probability": round((rain_hours / 6) * 100, 1)
            },
            "next_3_days": {
                "rainy_days": daily_rain_days,
                "overall_rain_risk": round((daily_rain_days / 3) * 100, 1)
            },
            "recommendation": self._get_precipitation_recommendation(rain_hours, total_precip)
        }
    
    def _get_temperature_trends(self, hourly: list, daily: list) -> Dict[str, Any]:
        """Analyze temperature trends"""
        if not hourly or not daily:
            return {"error": "Insufficient data"}
        
        # Hourly temperature trend
        temps = [hour.get("temp", 70) for hour in hourly[:6]]
        temp_trend = "stable"
        if len(temps) >= 2:
            if temps[-1] > temps[0] + 2:
                temp_trend = "rising"
            elif temps[-1] < temps[0] - 2:
                temp_trend = "falling"
        
        # Daily temperature range
        today = daily[0] if daily else {}
        temp_range = today.get("temp", {})
        min_temp = temp_range.get("min", 70)
        max_temp = temp_range.get("max", 70)
        
        return {
            "current_trend": temp_trend,
            "hourly_temps": [round(t, 1) for t in temps],
            "today_range": {
                "min": round(min_temp, 1),
                "max": round(max_temp, 1),
                "range": round(max_temp - min_temp, 1)
            },
            "comfort_level": self._assess_temperature_comfort(temps[0] if temps else 70)
        }
    
    def _get_wind_analysis(self, hourly: list) -> Dict[str, Any]:
        """Analyze wind conditions"""
        if not hourly:
            return {"error": "No hourly data"}
        
        wind_speeds = [hour.get("wind_speed", 5) for hour in hourly[:6]]
        wind_directions = [hour.get("wind_deg", 0) for hour in hourly[:6]]
        
        avg_wind = sum(wind_speeds) / len(wind_speeds)
        max_wind = max(wind_speeds)
        
        # Wind direction consistency
        direction_changes = 0
        for i in range(1, len(wind_directions)):
            if abs(wind_directions[i] - wind_directions[i-1]) > 45:
                direction_changes += 1
        
        return {
            "average_speed": round(avg_wind * 2.237, 1),  # Convert to mph
            "max_speed": round(max_wind * 2.237, 1),
            "direction_changes": direction_changes,
            "consistency": "stable" if direction_changes <= 1 else "variable",
            "golf_impact": self._assess_wind_impact(avg_wind)
        }
    
    def _get_alerts_summary(self, alerts: list) -> Dict[str, Any]:
        """Summarize weather alerts"""
        if not alerts:
            return {"active": False, "count": 0}
        
        alert_types = []
        severity_levels = []
        
        for alert in alerts:
            event = alert.get("event", "")
            alert_types.append(event)
            
            # Determine severity
            if any(word in event.lower() for word in ["warning", "emergency", "tornado"]):
                severity_levels.append("high")
            elif any(word in event.lower() for word in ["advisory", "watch"]):
                severity_levels.append("medium")
            else:
                severity_levels.append("low")
        
        return {
            "active": True,
            "count": len(alerts),
            "types": alert_types,
            "highest_severity": max(severity_levels) if severity_levels else "low",
            "recommendation": "Avoid outdoor activities" if "high" in severity_levels else "Exercise caution"
        }
    
    def _find_best_playing_times(self, hourly: list) -> list:
        """Find the best times to play golf in the next 6 hours"""
        if not hourly or len(hourly) < 6:
            return []
        
        hour_scores = []
        for i, hour_data in enumerate(hourly[:6]):
            temp = hour_data.get("temp", 70)
            conditions = hour_data.get("weather", [{}])[0].get("main", "Clear")
            wind_speed = hour_data.get("wind_speed", 5)
            pop = hour_data.get("pop", 0)
            
            score = 50
            if 65 <= temp <= 80:
                score += 30
            if wind_speed <= 10:
                score += 10
            if conditions == "Clear":
                score += 10
            score -= (pop * 50)
            
            hour_scores.append({
                "hour": i + 1,
                "score": max(0, min(100, score)),
                "time": hour_data.get("dt", 0),
                "temperature": round(temp, 1),
                "conditions": conditions
            })
        
        # Sort by score and return top 3
        hour_scores.sort(key=lambda x: x["score"], reverse=True)
        return hour_scores[:3]
    
    def _generate_weather_summary(self, current: dict, hourly: list, daily: list) -> str:
        """Generate a human-readable weather summary"""
        if not current:
            return "Weather data unavailable"
        
        # Handle both One Call API and basic API formats
        if "temp" in current:
            # One Call API format
            temp = current.get("temp", 70)
            conditions = current.get("weather", [{}])[0].get("description", "unknown")
            wind_speed = current.get("wind_speed", 5)
        else:
            # Basic API format - current is actually the full weather_data
            temp = current.get("main", {}).get("temp", 70)
            conditions = current.get("weather", [{}])[0].get("description", "unknown")
            wind_speed = current.get("wind", {}).get("speed", 5)
        
        summary_parts = [
            f"Currently {round(temp, 1)}°F with {conditions}",
            f"Wind at {round(wind_speed * 2.237, 1)} mph"
        ]
        
        if hourly and len(hourly) >= 6:
            rain_hours = sum(1 for h in hourly[:6] if h.get("pop", 0) > 0.3)
            if rain_hours > 0:
                summary_parts.append(f"Rain expected in {rain_hours} of the next 6 hours")
            else:
                summary_parts.append("No significant rain expected")
        else:
            summary_parts.append("Forecast data not available")
        
        return ". ".join(summary_parts) + "."
    
    def _get_precipitation_recommendation(self, rain_hours: int, total_precip: float) -> str:
        """Get recommendation based on precipitation"""
        if rain_hours == 0:
            return "Perfect conditions - no rain expected"
        elif rain_hours <= 2 and total_precip < 2:
            return "Light rain possible - bring rain gear"
        elif rain_hours <= 4:
            return "Moderate rain risk - consider postponing"
        else:
            return "Heavy rain expected - not recommended for golf"
    
    def _assess_temperature_comfort(self, temp: float) -> str:
        """Assess temperature comfort level"""
        if 65 <= temp <= 80:
            return "Perfect"
        elif 55 <= temp < 65 or 80 < temp <= 90:
            return "Good"
        elif 45 <= temp < 55 or 90 < temp <= 100:
            return "Acceptable"
        else:
            return "Challenging"
    
    def _assess_wind_impact(self, wind_speed: float) -> str:
        """Assess wind impact on golf"""
        wind_mph = wind_speed * 2.237
        if wind_mph <= 10:
            return "Minimal impact"
        elif wind_mph <= 15:
            return "Slight impact on ball flight"
        elif wind_mph <= 20:
            return "Moderate impact - adjust shots"
        else:
            return "High impact - very challenging conditions"
    
    def calculate_seasonal_score(self, month: int, latitude: float) -> float:
        """Calculate seasonal suitability score based on location and month"""
        # Northern states (higher latitude) have more seasonal variation
        if latitude > 40:  # Northern states
            seasonal_scores = {
                1: 20, 2: 30, 3: 50, 4: 70, 5: 90, 6: 95,
                7: 100, 8: 95, 9: 90, 10: 70, 11: 40, 12: 25
            }
        elif latitude > 35:  # Mid-latitude states
            seasonal_scores = {
                1: 40, 2: 50, 3: 70, 4: 85, 5: 95, 6: 100,
                7: 95, 8: 90, 9: 85, 10: 75, 11: 60, 12: 45
            }
        else:  # Southern states
            seasonal_scores = {
                1: 60, 2: 70, 3: 80, 4: 90, 5: 95, 6: 100,
                7: 85, 8: 80, 9: 85, 10: 90, 11: 80, 12: 70
            }
        
        return seasonal_scores.get(month, 70)
    
    def calculate_crowd_score(self, day_of_week: int, month: int) -> float:
        """Calculate crowd level score (higher = less crowded)"""
        # Weekend penalty
        weekend_penalty = 20 if day_of_week in [5, 6] else 0
        
        # Peak season penalty (summer months)
        peak_season_penalty = 15 if month in [6, 7, 8] else 0
        
        # Holiday penalty (approximate)
        holiday_penalty = 25 if month in [12, 1] else 0
        
        base_score = 100
        crowd_score = base_score - weekend_penalty - peak_season_penalty - holiday_penalty
        
        return max(20, crowd_score)  # Minimum score of 20
    
    def calculate_course_condition_score(self, course_data: Dict[str, Any]) -> float:
        """Calculate course condition score based on course data"""
        if not course_data:
            return 70.0
        
        # Extract course metrics
        slope_rating = course_data.get("slope_rating", 113)
        course_rating = course_data.get("course_rating", 72)
        
        # Slope rating analysis (113 is average)
        if slope_rating <= 110:
            slope_score = 90  # Easy course
        elif slope_rating <= 120:
            slope_score = 80  # Moderate course
        elif slope_rating <= 130:
            slope_score = 70  # Challenging course
        else:
            slope_score = 60  # Very difficult course
        
        # Course rating analysis
        if course_rating <= 70:
            rating_score = 95  # Excellent course
        elif course_rating <= 75:
            rating_score = 85  # Very good course
        elif course_rating <= 80:
            rating_score = 75  # Good course
        else:
            rating_score = 65  # Average course
        
        return (slope_score + rating_score) / 2
    
    async def get_ai_recommendation(
        self, 
        course_name: str, 
        factors: Dict[str, Any]
    ) -> str:
        """Get AI-powered recommendation using OpenRouter"""
        try:
            prompt = f"""
            You are a friendly golf course advisor. Give a warm, conversational recommendation for {course_name} based on these conditions:
            
            Weather: {factors.get('weather_score', 'N/A')}/100
            Season: {factors.get('seasonal_score', 'N/A')}/100  
            Crowds: {factors.get('crowd_score', 'N/A')}/100
            Course Quality: {factors.get('course_condition_score', 'N/A')}/100
            Overall: {factors.get('overall_score', 'N/A')}/100
            
            Date: {factors.get('date', 'N/A')}
            Location: {factors.get('location', 'N/A')}
            
            Write a friendly, encouraging recommendation in 2-3 sentences. Use conversational language like "you'll love", "perfect timing", "great conditions". 
            Be positive and helpful. Don't use technical jargon or scores in the response - just give practical advice about whether to play today.
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.openrouter_url,
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "mistralai/mistral-7b-instruct:free",
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 200,
                        "temperature": 0.7
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
                
        except Exception as e:
            logger.error(f"AI recommendation error: {e}")
            return self._generate_fallback_recommendation(factors)
    
    def _generate_fallback_recommendation(self, factors: Dict[str, Any]) -> str:
        """Generate a human-friendly fallback recommendation when AI is unavailable"""
        overall_score = factors.get('overall_score', 0)
        weather_score = factors.get('weather_score', 0)
        seasonal_score = factors.get('seasonal_score', 0)
        crowd_score = factors.get('crowd_score', 0)
        course_condition = factors.get('course_condition_score', 0)
        
        # Create more personalized recommendations based on specific factors
        if overall_score >= 85:
            if weather_score >= 80 and seasonal_score >= 80:
                return "Absolutely perfect day for golf! You've hit the jackpot with ideal weather and peak season conditions. The course is in pristine shape - grab your clubs and head out for an amazing round!"
            else:
                return "Excellent timing! The course is in fantastic condition and you'll have a wonderful experience. Weather looks great and crowds are manageable - definitely worth playing today!"
        elif overall_score >= 70:
            if course_condition >= 80:
                return "Great day to play! The course is beautifully maintained and you'll enjoy excellent playing conditions. Weather is decent and crowds are reasonable - go ahead and book your tee time!"
            else:
                return "Good conditions for golf! You should have a pleasant round with decent weather and manageable crowds. The course is in solid shape - worth getting out there!"
        elif overall_score >= 55:
            if weather_score < 60:
                return "Decent day for golf, though you might want to keep an eye on the weather. The course is playable and crowds should be okay - just be prepared for some challenging conditions."
            else:
                return "Not bad timing for a round! Conditions are okay overall, though you might encounter some busy crowds or course maintenance. Still worth playing if you're flexible."
        else:
            if weather_score < 50:
                return "Today might be tough for golf with challenging weather conditions. The course could be wet or windy, and crowds might be heavy. Consider waiting for better weather or trying an indoor alternative."
            else:
                return "Today presents some challenges for golf. Weather conditions aren't ideal and crowds could be heavy. You might want to wait for better conditions or try a different day."
    
    async def analyze_course_timing(
        self, 
        course_data: Dict[str, Any],
        target_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Comprehensive timing analysis for a golf course"""
        if target_date is None:
            target_date = datetime.now()
        
        # Extract course information
        course_name = course_data.get("course_name", "Unknown Course")
        location = course_data.get("location", {})
        lat = location.get("latitude", 0)
        lon = location.get("longitude", 0)
        
        # Get weather data using One Call API for comprehensive data
        # Fallback to basic weather API if One Call fails
        weather_data = await self.weather_service.get_onecall_weather(lat, lon)
        if not weather_data or "error" in weather_data:
            logger.warning(f"One Call API failed, falling back to basic weather API for lat={lat}, lon={lon}")
        weather_data = await self.weather_service.get_current_weather(lat, lon)
        
        # Calculate factor scores
        weather_score = self.calculate_weather_score(weather_data)
        seasonal_score = self.calculate_seasonal_score(target_date.month, lat)
        crowd_score = self.calculate_crowd_score(target_date.weekday(), target_date.month)
        course_condition_score = self.calculate_course_condition_score(course_data)
        
        # Calculate overall score
        overall_score = (
            weather_score * 0.35 +
            seasonal_score * 0.25 +
            crowd_score * 0.25 +
            course_condition_score * 0.15
        )
        
        # Prepare factors for AI analysis
        factors = {
            "weather_score": weather_score,
            "seasonal_score": seasonal_score,
            "crowd_score": crowd_score,
            "course_condition_score": course_condition_score,
            "overall_score": round(overall_score, 1),
            "date": target_date.strftime("%Y-%m-%d"),
            "location": f"{location.get('city', 'Unknown')}, {location.get('state', 'Unknown')}"
        }
        
        # Get AI recommendation
        ai_recommendation = await self.get_ai_recommendation(course_name, factors)
        
        return {
            "course_name": course_name,
            "analysis_date": target_date.isoformat(),
            "location": location,
            "scores": {
                "weather": weather_score,
                "seasonal": seasonal_score,
                "crowd": crowd_score,
                "course_condition": course_condition_score,
                "overall": round(overall_score, 1)
            },
            "weather_data": self._extract_detailed_weather_insights(weather_data),
            "recommendation": ai_recommendation,
            "timing_grade": self._get_timing_grade(overall_score)
        }
    
    def _get_timing_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "A-"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "B-"
        elif score >= 60:
            return "C+"
        elif score >= 55:
            return "C"
        elif score >= 50:
            return "C-"
        else:
            return "D"

# Global analyzer instance
golf_factor_analyzer = GolfCourseFactorAnalyzer()

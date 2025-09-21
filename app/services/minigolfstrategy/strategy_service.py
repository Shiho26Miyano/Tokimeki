"""
Golf Strategy Calculation Service
AI-powered strategy recommendations using mathematical models
"""
import math
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Club:
    name: str
    carry_distance: float
    roll_distance: float
    accuracy_sigma: float
    loft_angle: float

@dataclass
class Hazard:
    start_distance: float
    end_distance: float
    penalty_strokes: float
    hazard_type: str

@dataclass
class Hole:
    par: int
    total_yardage: float
    fairway_width: float
    hazards: List[Hazard]
    green_size: float

@dataclass
class Conditions:
    wind_speed: float
    wind_direction: float
    temperature: float
    humidity: float
    course_firmness: float

class GolfStrategyCalculator:
    """Advanced golf strategy calculator using mathematical models"""
    
    def __init__(self):
        self.wind_adjustment_factor = 1.5
        self.temperature_adjustment_factor = 0.1
        self.humidity_adjustment_factor = 0.05
    
    def calculate_wind_adjusted_distance(
        self, 
        base_distance: float, 
        wind_speed: float, 
        wind_direction: float,
        shot_direction: float
    ) -> float:
        """Calculate wind-adjusted shot distance"""
        # Calculate wind component in shot direction
        wind_component = wind_speed * math.cos(math.radians(wind_direction - shot_direction))
        
        # Apply wind adjustment
        adjusted_distance = base_distance + (wind_component * self.wind_adjustment_factor)
        
        return max(0, adjusted_distance)
    
    def calculate_roll_distance(
        self, 
        base_roll: float, 
        course_firmness: float, 
        temperature: float,
        humidity: float
    ) -> float:
        """Calculate expected roll distance based on conditions"""
        # Temperature adjustment
        temp_factor = 1 + (temperature - 70) * self.temperature_adjustment_factor
        
        # Humidity adjustment
        humidity_factor = 1 + (humidity - 50) * self.humidity_adjustment_factor
        
        # Course firmness adjustment
        firmness_factor = 0.3 + 0.7 * course_firmness
        
        return base_roll * temp_factor * humidity_factor * firmness_factor
    
    def calculate_hazard_probability(
        self, 
        shot_distance: float, 
        shot_accuracy: float, 
        hazard: Hazard
    ) -> float:
        """Calculate probability of hitting a hazard"""
        if hazard.start_distance <= shot_distance <= hazard.end_distance:
            # Calculate probability based on normal distribution
            mean = shot_distance
            sigma = shot_accuracy
            
            # Probability of landing in hazard range
            prob_in_range = self._normal_cdf(hazard.end_distance, mean, sigma) - \
                          self._normal_cdf(hazard.start_distance, mean, sigma)
            
            return min(1.0, max(0.0, prob_in_range))
        
        return 0.0
    
    def _normal_cdf(self, x: float, mean: float, sigma: float) -> float:
        """Calculate cumulative distribution function for normal distribution"""
        if sigma <= 0:
            return 1.0 if x >= mean else 0.0
        
        z = (x - mean) / (sigma * math.sqrt(2))
        return 0.5 * (1 + math.erf(z))
    
    def calculate_expected_strokes(
        self, 
        hole: Hole, 
        club: Club, 
        conditions: Conditions
    ) -> float:
        """Calculate expected strokes for a given club and conditions"""
        # Calculate wind-adjusted carry distance
        wind_adjusted_carry = self.calculate_wind_adjusted_distance(
            club.carry_distance, 
            conditions.wind_speed, 
            conditions.wind_direction,
            0  # Assuming straight shot
        )
        
        # Calculate roll distance
        roll_distance = self.calculate_roll_distance(
            club.roll_distance,
            conditions.course_firmness,
            conditions.temperature,
            conditions.humidity
        )
        
        # Total expected distance
        total_distance = wind_adjusted_carry + roll_distance
        
        # Calculate remaining distance to hole
        remaining_distance = max(0, hole.total_yardage - total_distance)
        
        # Calculate hazard probability
        hazard_penalty = 0
        for hazard in hole.hazards:
            hazard_prob = self.calculate_hazard_probability(
                total_distance, 
                club.accuracy_sigma, 
                hazard
            )
            hazard_penalty += hazard_prob * hazard.penalty_strokes
        
        # Calculate approach shot difficulty
        approach_difficulty = self._calculate_approach_difficulty(remaining_distance, hole.par)
        
        # Calculate putting difficulty
        putting_difficulty = self._calculate_putting_difficulty(remaining_distance)
        
        # Total expected strokes
        expected_strokes = 1 + approach_difficulty + putting_difficulty + hazard_penalty
        
        return expected_strokes
    
    def _calculate_approach_difficulty(self, remaining_distance: float, par: int) -> float:
        """Calculate approach shot difficulty based on remaining distance"""
        if remaining_distance <= 10:
            return 0.0  # On the green
        elif remaining_distance <= 100:
            return 0.2  # Short approach
        elif remaining_distance <= 200:
            return 0.5  # Medium approach
        else:
            return 1.0  # Long approach
    
    def _calculate_putting_difficulty(self, remaining_distance: float) -> float:
        """Calculate putting difficulty based on remaining distance"""
        if remaining_distance <= 10:
            return 1.0  # Putting
        elif remaining_distance <= 100:
            return 1.2  # Chipping
        else:
            return 1.4  # Long approach
    
    def find_optimal_strategy(
        self, 
        hole: Hole, 
        available_clubs: List[Club], 
        conditions: Conditions
    ) -> Dict[str, Any]:
        """Find the optimal strategy for a hole"""
        best_strategy = None
        best_expected_strokes = float('inf')
        
        strategies = []
        
        for club in available_clubs:
            expected_strokes = self.calculate_expected_strokes(hole, club, conditions)
            
            # Calculate hazard probability
            total_hazard_prob = 0
            for hazard in hole.hazards:
                hazard_prob = self.calculate_hazard_probability(
                    club.carry_distance + club.roll_distance,
                    club.accuracy_sigma,
                    hazard
                )
                total_hazard_prob += hazard_prob
            
            strategy = {
                "club": club.name,
                "expected_strokes": round(expected_strokes, 2),
                "hazard_probability": round(total_hazard_prob, 3),
                "remaining_distance": max(0, hole.total_yardage - (club.carry_distance + club.roll_distance)),
                "confidence_score": self._calculate_confidence_score(expected_strokes, total_hazard_prob),
                "risk_level": self._assess_risk_level(total_hazard_prob, expected_strokes)
            }
            
            strategies.append(strategy)
            
            if expected_strokes < best_expected_strokes:
                best_expected_strokes = expected_strokes
                best_strategy = strategy
        
        return {
            "recommended_strategy": best_strategy,
            "all_strategies": strategies,
            "hole_analysis": {
                "par": hole.par,
                "total_yardage": hole.total_yardage,
                "difficulty_rating": self._calculate_hole_difficulty(hole),
                "hazard_count": len(hole.hazards)
            }
        }
    
    def _calculate_confidence_score(self, expected_strokes: float, hazard_prob: float) -> float:
        """Calculate confidence score for a strategy"""
        # Lower expected strokes and hazard probability = higher confidence
        stroke_score = max(0, 1 - (expected_strokes - 1) / 3)  # Normalize to 0-1
        hazard_score = max(0, 1 - hazard_prob)
        
        return round((stroke_score + hazard_score) / 2, 3)
    
    def _assess_risk_level(self, hazard_prob: float, expected_strokes: float) -> str:
        """Assess risk level of a strategy"""
        if hazard_prob > 0.3 or expected_strokes > 2.5:
            return "high"
        elif hazard_prob > 0.1 or expected_strokes > 2.0:
            return "medium"
        else:
            return "low"
    
    def _calculate_hole_difficulty(self, hole: Hole) -> float:
        """Calculate overall hole difficulty rating"""
        base_difficulty = hole.par * 0.5  # Base difficulty by par
        yardage_factor = hole.total_yardage / 400  # Normalize by typical par-4 length
        hazard_factor = len(hole.hazards) * 0.2  # Add difficulty for hazards
        
        return round(base_difficulty + yardage_factor + hazard_factor, 2)

class ExecutiveCaddieCalculator:
    """CaddieAlpha™ Risk-Reward Analyzer for executive golf strategy"""
    
    def __init__(self):
        self.risk_tolerance_factors = {
            "aggressive": 1.5,
            "balanced": 1.0,
            "conservative": 0.7
        }
    
    def calculate_volatility(self, slope_rating: float, handicap: int) -> float:
        """Calculate volatility based on slope rating and hole handicap"""
        # Higher slope = more volatile course
        # Lower handicap = more volatile hole (harder)
        slope_factor = slope_rating / 113.0  # Normalize slope rating
        handicap_factor = (18 - handicap + 1) / 18.0  # Invert handicap (1=hardest, 18=easiest)
        
        volatility = slope_factor * handicap_factor
        return round(volatility, 3)
    
    def calculate_expected_strokes(self, par: int, strategy: str, volatility: float) -> float:
        """Calculate expected strokes for different strategies"""
        base_ev = par
        
        # Strategy adjustments - make aggressive strategy more likely to beat par
        if strategy == "aggressive":
            ev_adjustment = -0.5 + (volatility * 0.1)  # Risk for reward, more aggressive
        elif strategy == "balanced":
            ev_adjustment = -0.1 + (volatility * 0.05)   # Slight advantage
        else:  # conservative
            ev_adjustment = 0.1 + (volatility * 0.02)  # Play it safe
        
        expected_strokes = base_ev + ev_adjustment
        return round(expected_strokes, 2)
    
    def calculate_blow_up_probability(self, volatility: float, strategy: str) -> float:
        """Calculate probability of blow-up (double bogey or worse)"""
        base_prob = volatility * 0.3  # Base probability from volatility
        
        # Strategy adjustments
        if strategy == "aggressive":
            prob_multiplier = 1.8
        elif strategy == "balanced":
            prob_multiplier = 1.0
        else:  # conservative
            prob_multiplier = 0.6
        
        blow_up_prob = min(0.95, base_prob * prob_multiplier)
        return round(blow_up_prob, 3)
    
    def calculate_caddie_score(self, expected_strokes: float, volatility: float, par: int) -> float:
        """Calculate CaddieScore (Sharpe-like: reward ÷ risk)"""
        if volatility == 0:
            return 0.0
        
        # Reward: how much better than par
        reward = max(0, par - expected_strokes)
        
        # Risk: volatility
        risk = volatility
        
        # CaddieScore = reward / risk (higher is better)
        caddie_score = reward / risk if risk > 0 else 0
        return round(caddie_score, 2)
    
    def analyze_hole_strategy(
        self, 
        hole_data: Dict[str, Any], 
        risk_budget: float,
        strategy: str = "balanced"
    ) -> Dict[str, Any]:
        """Analyze strategy for a single hole"""
        par = hole_data.get("par", 4)
        yardage = hole_data.get("yardage", 400)
        handicap = hole_data.get("handicap", 9)
        slope_rating = hole_data.get("slope_rating", 113)
        
        # Calculate metrics
        volatility = self.calculate_volatility(slope_rating, handicap)
        expected_strokes = self.calculate_expected_strokes(par, strategy, volatility)
        blow_up_prob = self.calculate_blow_up_probability(volatility, strategy)
        caddie_score = self.calculate_caddie_score(expected_strokes, volatility, par)
        
        # Determine recommendation
        risk_cost = volatility * self.risk_tolerance_factors[strategy]
        
        if risk_cost <= risk_budget and caddie_score > 1.0:
            recommendation = "press"
            explanation = f"High CaddieScore ({caddie_score}) + low risk cost ({risk_cost:.2f}) → press for birdie opportunity"
        else:
            recommendation = "protect"
            if risk_cost > risk_budget:
                explanation = f"Risk cost ({risk_cost:.2f}) exceeds budget ({risk_budget}) → protect par"
            else:
                explanation = f"Low CaddieScore ({caddie_score}) → protect par, press elsewhere"
        
        return {
            "hole": hole_data.get("hole_number", 1),
            "par": par,
            "yardage": yardage,
            "handicap": handicap,
            "volatility": volatility,
            "expected_strokes": expected_strokes,
            "blow_up_probability": blow_up_prob,
            "caddie_score": caddie_score,
            "risk_cost": round(risk_cost, 2),
            "recommended": recommendation,
            "explanation": explanation
        }
    
    def calculate_caddie_alpha_strategy(
        self, 
        course_data: Dict[str, Any], 
        tee_name: str, 
        gender: str,
        risk_budget: float = 2.5
    ) -> Dict[str, Any]:
        """Calculate complete CaddieAlpha strategy for a course"""
        # Handle nested course data structure
        if "course" in course_data:
            course_data = course_data["course"]
        
        # Extract tee data
        tee_data = None
        if gender.upper() == "M":
            tee_data = next((tee for tee in course_data.get("tees", {}).get("male", []) 
                           if tee.get("tee_name") == tee_name), None)
        else:
            tee_data = next((tee for tee in course_data.get("tees", {}).get("female", []) 
                           if tee.get("tee_name") == tee_name), None)
        
        if not tee_data:
            raise ValueError(f"Tee '{tee_name}' not found for gender '{gender}'")
        
        slope_rating = tee_data.get("slope_rating", 113)
        holes = tee_data.get("holes", [])
        
        # Analyze each hole
        hole_analyses = []
        press_holes = []
        protect_holes = []
        total_risk_used = 0.0
        total_caddie_score = 0.0
        
        for i, hole in enumerate(holes, 1):
            hole_data = {
                "hole_number": i,
                "par": hole.get("par", 4),
                "yardage": hole.get("yardage", 400),
                "handicap": hole.get("handicap", 9),
                "slope_rating": slope_rating
            }
            
            analysis = self.analyze_hole_strategy(hole_data, risk_budget)
            hole_analyses.append(analysis)
            
            if analysis["recommended"] == "press":
                press_holes.append(i)
            else:
                protect_holes.append(i)
            
            total_risk_used += analysis["risk_cost"]
            total_caddie_score += analysis["caddie_score"]
        
        return {
            "summary": {
                "caddie_score_total": round(total_caddie_score, 1),
                "risk_budget_used": round(total_risk_used, 1),
                "risk_budget_remaining": round(risk_budget - total_risk_used, 1),
                "press_holes": press_holes,
                "protect_holes": protect_holes,
                "total_holes": len(holes),
                "course_name": course_data.get("course_name", "Unknown Course"),
                "tee_name": tee_name,
                "gender": gender
            },
            "holes": hole_analyses
        }

# Global calculator instances
golf_strategy_calculator = GolfStrategyCalculator()
executive_caddie_calculator = ExecutiveCaddieCalculator()
